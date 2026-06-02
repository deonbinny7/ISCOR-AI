import os
from fpdf import FPDF
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1] / "knowledge_base"

MOCK_DOCS = {
    "WHO": {
        "stress.pdf": [
            "Stress Management Guide",
            "Stress is a natural human response that prompts us to address challenges and threats in our lives.",
            "Everyone experiences stress to some degree.",
            "However, when stress becomes chronic, it can have serious impacts on physical and mental health.",
            "To manage stress, consider the following techniques: regular physical activity, adequate sleep, and mindfulness practices.",
            "Deep breathing exercises can help lower your heart rate and promote relaxation.",
            "Social support from friends and family is also a critical buffer against stress.",
            "Limiting caffeine and alcohol intake can prevent exacerbation of stress symptoms.",
            "If stress becomes overwhelming, seeking professional help from a therapist or counsellor is recommended."
        ],
        "sleep.pdf": [
            "Sleep Hygiene Guidelines",
            "Sleep is essential for cognitive function, emotional well-being, and physical health.",
            "Adults should aim for 7 to 9 hours of quality sleep per night.",
            "Establish a consistent sleep schedule by going to bed and waking up at the same time every day.",
            "Create a restful environment: keep your bedroom dark, quiet, and cool.",
            "Limit exposure to screens (phones, tablets, computers) for at least an hour before bedtime, as blue light can suppress melatonin production.",
            "Avoid heavy meals, caffeine, and alcohol close to bedtime.",
            "Engage in relaxing activities before bed, such as reading or taking a warm bath.",
            "Regular physical activity during the day can promote better sleep at night."
        ]
    },
    "NHS": {
        "wellbeing.pdf": [
            "Five Steps to Mental Wellbeing",
            "1. Connect with other people. Good relationships are important for your mental wellbeing.",
            "2. Be physically active. Being active is not only great for your physical health and fitness, but it can also improve your mental wellbeing.",
            "3. Learn new skills. Research shows that learning new skills can also improve your mental wellbeing by boosting self-confidence.",
            "4. Give to others. Even the smallest act can count, whether it's a smile, a thank you or a kind word.",
            "5. Pay attention to the present moment (mindfulness). Paying more attention to the present moment can improve your mental wellbeing."
        ],
        "exercise.pdf": [
            "Exercise and Mental Health",
            "Regular exercise can have a profoundly positive impact on depression, anxiety, and ADHD.",
            "It also relieves stress, improves memory, helps you sleep better, and boosts your overall mood.",
            "You don't have to be a fitness fanatic to reap the benefits. Modest amounts of exercise can make a real difference.",
            "Aim for at least 30 minutes of moderate exercise five times a week.",
            "Activities like brisk walking, cycling, or swimming are excellent choices.",
            "Even a short 15-minute walk can help clear your mind and improve your mood."
        ]
    },
    "Universities": {
        "student_stress.pdf": [
            "Managing Academic Pressure",
            "University life can be highly demanding, leading to academic stress.",
            "It's important to develop effective time management skills to handle coursework and exams.",
            "Break large tasks into smaller, manageable chunks.",
            "Create a realistic study schedule and stick to it, but allow for flexibility.",
            "Take regular breaks during study sessions to maintain focus and prevent burnout.",
            "Don't hesitate to reach out to professors or teaching assistants if you're struggling with course material.",
            "Utilize campus resources such as the writing center, tutoring services, and academic advising.",
            "Remember that your grades do not define your worth."
        ]
    }
}

def create_mock_pdfs():
    for category, docs in MOCK_DOCS.items():
        cat_dir = BASE_DIR / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        
        for filename, lines in docs.items():
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("helvetica", size=12)
            
            for line in lines:
                pdf.multi_cell(w=190, h=10, text=line)
            
            output_path = cat_dir / filename
            pdf.output(str(output_path))
            print(f"Created: {output_path}")

if __name__ == "__main__":
    create_mock_pdfs()
    print("Mock PDFs generated successfully.")
