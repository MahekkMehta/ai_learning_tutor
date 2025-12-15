AI Learning Tutor – Pro

A multimodal, adaptive AI learning assistant built using Streamlit and Google Gemini API.
This application helps users learn from PDFs, images, ask questions via an AI tutor, take assessments, track progress, and export learning reports.

🚀 Features

📘 Document Learning – Upload PDFs and receive structured summaries

🖼 Image Learning – Upload images and get educational explanations

💬 AI Tutor – Ask questions in free mode or document-based mode

📝 Assessment System – Auto-generated questions with AI evaluation

📊 Dashboard – Tracks scores, attempts, and learning progress

📄 PDF Report Export – Download a learning performance report

🗂 Persistent History – Chat and image analysis stored locally (SQLite)

🛠 Tech Stack

Python

Streamlit

Google Gemini API

SQLite

pdfplumber

Pillow

ReportLab

📦 Installation & Setup
1️⃣ Clone the Repository
git clone https://github.com/MahekkMehta/ai_learning_tutor.git
cd ai-learning-tutor

2️⃣ Install Dependencies
pip install -r requirements.txt

3️⃣ Add Google Gemini API Key (MANDATORY)

Create the following file:

.streamlit/secrets.toml


Add your API key:

GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"

▶️ Run the Application
streamlit run app.py


The app will open in your browser at:

http://localhost:8501

🔐 IMPORTANT: API KEY USAGE DISCLAIMER (MANDATORY)

⚠️ This project requires a valid Google Gemini API key to function.

The API key is NOT included in this repository

Each user must generate their own API key

The API key must be stored locally in .streamlit/secrets.toml

DO NOT commit or share your API key publicly

The repository owner is NOT responsible for any API usage, quota exhaustion, or billing issues

👉 If the API key is missing, the application will NOT work.

📁 Project Structure
ai-learning-tutor/
│
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── .streamlit/
    └── secrets.toml   # (ignored by git)

🧪 Notes

SQLite database (ai_tutor.db) is created automatically at runtime

Audio and PDF exports are generated locally and ignored by Git

Internet connection is required for AI responses

📜 License

This project is provided for educational and academic use only.

👤 Author

Developed by Pratik Desai and Mahek Mehta