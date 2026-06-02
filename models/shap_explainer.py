import pandas as pd
import numpy as np
import pickle
import shap
import json

class SHAPExplainer:
    def __init__(self, model_path='models/final_model.pkl', data_path='datasets/primary_dataset_clean.csv'):
        # Load the model
        with open(model_path, 'rb') as f:
            self.model = pickle.load(f)
            
        # Load a sample of the data to initialize TreeExplainer and get feature names
        from modeling_pipeline import engineer_features
        from sklearn.model_selection import train_test_split
        
        df = pd.read_csv(data_path)
        df = engineer_features(df)
        
        label_map = {'Low': 0, 'Moderate': 1, 'High': 2}
        df['Target'] = df['Risk_Category'].map(label_map)
        
        # Use strictly the primary training set (80% split with random_state=42)
        X_all = df.drop(columns=['Risk_Category', 'Target'])
        y_all = df['Target']
        
        X_train, _, _, _ = train_test_split(X_all, y_all, test_size=0.2, stratify=y_all, random_state=42)
        
        self.X = X_train
        self.feature_names = self.X.columns.tolist()
        
        # Initialize the explainer
        # TreeExplainer is fast for Random Forests
        self.explainer = shap.TreeExplainer(self.model)

    def explain(self, input_row_dict):
        """
        Takes a single row as a dictionary.
        Returns the structured JSON contract required by the LLM layer.
        """
        # Convert to DataFrame
        row_df = pd.DataFrame([input_row_dict])[self.feature_names]
        
        # Align dtypes to prevent SHAP/model crashes (e.g. XGBoost strictness on float vs int)
        for col in self.feature_names:
            expected_dtype = self.X[col].dtype
            if row_df[col].dtype != expected_dtype:
                row_df[col] = row_df[col].astype(expected_dtype)
        
        # Get Predictions
        # Random Forest returns probabilities directly
        probas = self.model.predict_proba(row_df)[0]
        risk_class_idx = np.argmax(probas)
        
        class_names = ['Low', 'Moderate', 'High']
        risk_label = class_names[risk_class_idx]
        
        risk_probabilities = {
            "Low": round(probas[0], 4),
            "Moderate": round(probas[1], 4),
            "High": round(probas[2], 4)
        }
        
        # Compute SHAP values
        shap_values = self.explainer.shap_values(row_df)
        
        # In multi-class classification, shap_values is a list of arrays (one for each class).
        # We care about explaining why it chose its PREDICTED class (or specifically why it's High risk).
        # Let's explain the predicted class's probability.
        # Note: Depending on the SHAP version, shap_values might be an array of shape (n_samples, n_features, n_classes)
        # Let's handle both structures.
        if isinstance(shap_values, list):
            class_shap_values = shap_values[risk_class_idx][0]
        else:
            # SHAP 0.45+ often returns shape (n_samples, n_features, n_classes)
            class_shap_values = shap_values[0, :, risk_class_idx]
            
        # Create a list of feature contributions
        factors = []
        for i, feature_name in enumerate(self.feature_names):
            val = class_shap_values[i]
            direction = "increases_risk" if val > 0 else "decreases_risk"
            # For Low Risk, a positive SHAP value increases the probability of LOW risk, 
            # which might be confusing. So we should standardise:
            # A factor "increases_risk" if it pushes towards High Risk.
            # So let's always look at the SHAP values for the "High" class (index 2) to determine direction.
            pass
            
        # Re-computing strictly against the "High" class (index 2) to ensure 'increases_risk' means what the LLM thinks it means
        if isinstance(shap_values, list):
            high_class_shap = shap_values[2][0]
        else:
            high_class_shap = shap_values[0, :, 2]
            
        factors = []
        for i, feature_name in enumerate(self.feature_names):
            val = high_class_shap[i]
            direction = "increases_risk" if val > 0 else "decreases_risk"
            factors.append({
                "feature": feature_name,
                "shap_value": round(float(abs(val)), 4),
                "direction": direction,
                "raw_value": val
            })
            
        # Sort by absolute magnitude of SHAP value
        factors = sorted(factors, key=lambda x: x['shap_value'], reverse=True)
        
        # Extract top 4 factors
        top_factors = []
        for f in factors[:4]:
            feat = f['feature']
            user_val = row_df[feat].iloc[0]
            
            # 1. Cohort Percentile
            feature_vals = self.X[feat]
            percentile = int((feature_vals < user_val).mean() * 100)
            
            # 2. Counterfactual String
            display_name = feat.replace('_', ' ')
            if f['direction'] == "increases_risk":
                counterfactual = f"Decreasing your {display_name} is associated with a lower predicted risk."
            else:
                counterfactual = f"Maintaining or increasing your {display_name} helps protect against higher risk."
                
            top_factors.append({
                "feature": feat,
                "shap_value": f['shap_value'],
                "direction": f['direction'],
                "cohort_percentile": percentile,
                "counterfactual": counterfactual
            })
            
        output = {
            "risk_label": risk_label,
            "risk_probabilities": risk_probabilities,
            "top_factors": top_factors
        }
        
        return json.dumps(output, indent=2)

if __name__ == '__main__':
    explainer = SHAPExplainer()
    
    # Test with a dummy row (from the primary dataset means)
    dummy_row = explainer.X.mean().to_dict()
    
    print("Testing SHAP Explainer JSON output:\\n")
    print(explainer.explain(dummy_row))
