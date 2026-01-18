# 📘 StudyStack  
### Smart Study Planner & Learning Platform

StudyStack is a smart, student-focused web platform designed to help learners **plan, organize, and improve their studies intelligently**. It started as a smart study planner and is evolving into a full learning ecosystem inspired by platforms like GeeksforGeeks and modern e-learning systems.

---

## 🚀 Vision

StudyStack aims to become a unified platform where students can:

- Plan their studies effectively  
- Track tasks and progress  
- Upload and manage study materials  
- Get smart assistance (difficulty estimation, planning help, insights)  
- Share useful notes and resources with others  

The long-term goal is to build a system that not only manages tasks, but **actively supports learning.**

---

## ✨ Current Features

- 🔐 User authentication (Signup / Login / Logout)  
- 📚 Subject management  
- ✅ Task creation with deadlines, difficulty & estimated hours  
- 📊 Personal dashboard (total, pending, completed tasks)  
- 📁 Study material upload (PDF, TXT, DOCX)  
- 🤖 Smart task flow (foundation for auto difficulty estimation)  
- 🎨 Modern, clean UI design  

---

## 🧠 Smart Features (In Progress)

- Automatic difficulty estimation from uploaded documents  
- Smart confirmation system for task difficulty  
- Intelligent study suggestions  
- File-based task generation  
- Learning analytics (streaks, consistency, weak areas)  

---

## 🌱 Planned Features

Inspired by e-learning platforms:

- 📂 Public notes & resource sharing  
- 🔍 Discover section (subjects, notes, tasks, guides)  
- 🏆 Study streaks & achievement system  
- 📈 Productivity & learning insights  
- 👥 Community contributions  
- 🤝 Collaborative learning tools  
- 🧪 AI-assisted planning & summarization  

---

## 🛠 Tech Stack

**Backend**
- Python  
- Django  
- SQLite (development)

**Frontend**
- HTML  
- CSS  
- JavaScript  

**Libraries**
- PyPDF2  
- python-docx  

---

## 📁 Project Structure

studystack/
│
├── core/            # Main app (models, views, forms)
├── templates/       # HTML templates
├── static/          # CSS, JS, assets
├── db.sqlite3
├── manage.py
└── README.md

---
## ⚙️ Setup Instructions

```bash
git clone "https://github.com/varun05126/StudyStack"
cd StudyStack
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 manage.py migrate
python3 manage.py runserver

Open: http://127.0.0.1:8000

---
## 👨‍💻 Author

StudyStack is designed and developed by:

**Varun M**  
B.Tech CSE (Artificial Intelligence & Machine Learning)  
Vardhaman College of Engineering, Telangana, India  

Passionate about building practical, student-centric learning platforms.


## 📌 Status

StudyStack is under active development.
Features are being added step-by-step with a focus on building a real-world usable learning platform.
