# DASS-21 Cutoff Methodology

## Derivation of Target Labels
To establish a psychometrically valid target label for the ISCOR AI screening tool, we derived our baseline risk logic from the established **Depression, Anxiety and Stress Scale - 21 Items (DASS-21)**. 

The DASS-21 provides quantitative measures across three subscales. Since it is a short-form version of the DASS-42, the standard clinical practice is to sum the scores for each 7-item subscale and multiply by 2 to use the official DASS-42 severity cutoffs.

### Step 1: Subscale Scoring
The 21 items are scored on a 0-3 Likert scale and grouped as follows:
- **Depression**: Items 3, 5, 10, 13, 16, 17, 21
- **Anxiety**: Items 2, 4, 7, 9, 15, 19, 20
- **Stress**: Items 1, 6, 8, 11, 12, 14, 18

### Step 2: Standard Severity Cutoffs
Using the official DASS cutoffs, the multiplied scores are mapped to severity bands:
- **Depression**: Normal (0-9), Mild (10-13), Moderate (14-20), Severe (21-27), Extremely Severe (28+)
- **Anxiety**: Normal (0-7), Mild (8-9), Moderate (10-14), Severe (15-19), Extremely Severe (20+)
- **Stress**: Normal (0-14), Mild (15-18), Moderate (19-25), Severe (26-33), Extremely Severe (34+)

### Step 3: Mapping to ISCOR AI Risk Tiers
To fulfill the project scope of providing a simplified *screening signal* rather than a diagnostic output, we collapsed the 5-tier clinical severity bands into a **3-tier Risk Category (Low, Moderate, High)**:
- **Low Risk**: Covers 'Normal' and 'Mild' scores. These represent baseline to slightly elevated symptoms that are common and do not typically require intervention beyond general wellness practices.
- **Moderate Risk**: Maps directly to 'Moderate' scores. Indicates a noticeable elevation in symptoms where structured lifestyle modifications or non-urgent counseling could be beneficial.
- **High Risk**: Covers 'Severe' and 'Extremely Severe' scores. This triggers the **Risk Gate / Safety Router** in our architecture, suppressing the LLM and routing the user to professional crisis resources.

An individual's **Overall Risk** is determined by taking the maximum risk category across their three subscales. For example, if a student has Low Depression, Low Stress, but High Anxiety, their overall screening signal is High Risk.

### Step 4: Application to Primary Training Dataset
Since our primary training dataset (`students_mental_health_survey.csv`) contains self-reported 0-5 proxy scores rather than raw DASS-21 item responses, we use the DASS-21 reference dataset to derive the relative proportions for each risk band on the Depression, Anxiety, and Stress subscales. We then map the primary dataset scores to the same Low/Moderate/High proportions via percentile-aligned cutoffs, preserving the original ordinal scale while ensuring the target labels are aligned with a validated psychometric reference.
