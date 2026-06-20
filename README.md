# Automated Academic Timetabling System 🎓🗓️

An advanced, full-stack web application designed to solve the highly complex Constraint Satisfaction Problem (CSP) of university scheduling. Built with **Django** and powered by the **Google OR-Tools (CP-SAT)** mathematical optimization engine, this system automatically generates 100% mathematically feasible, collision-free academic timetables in seconds.

**Developer:** Muhammad  
**Version:** 1.0.0  

---

## 🚀 Key Features

* **Algorithmic Constraint Engine:** Replaces manual scheduling by mapping real-world department rules (rooms, courses, teacher availability) into complex mathematical equations to eliminate double-booking and schedule conflicts.
* **Role-Based Access Control (RBAC):** * **Coordinator Portal:** Manage domain entities, tweak constraints, and initialize the scheduling engine.
  * **Faculty Dashboard:** Personalized views for teachers to see exactly when and where they are teaching.
  * **Student Dashboard:** Dedicated cohort views showing section-specific class times and locations.
* **Dynamic Timetable UI:** Highly readable, responsive grid layouts built with Tailwind CSS, featuring dynamically calculated lecture duration slots.
* **Platform Independent:** Designed to run seamlessly on both Linux and Windows environments.

## 🛠️ Tech Stack

* **Backend:** Python 3.12, Django 6.x
* **Optimization Engine:** Google OR-Tools (Constraint Programming - SAT Solver)
* **Frontend:** HTML5, CSS3, Tailwind CSS, Django Templates
* **Database:** SQLite (Relational structure resolving Many-to-Many entity constraints)

---

## ⚙️ Installation & Setup

This project is designed to be easily deployable on any local machine. Follow these steps to get the environment running:

### 1. Clone the Repository
```bash
git clone [https://github.com/YOUR_USERNAME/university-scheduler.git](https://github.com/YOUR_USERNAME/university-scheduler.git)
cd university-scheduler
```

### 2. Create and Activate a Virtual Environment
**For Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```
**For Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
# Note: If requirements.txt is missing, run: pip install django google-ortools
```

### 4. Setup the Database
Apply the initial migrations to construct the SQLite database schema:
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Seed the Database (Important!)
Before running the engine, populate the database with baseline university data (Rooms, Courses, Sections, Teachers):
```bash
python manage.py seed_university
```

### 6. Create a Superuser (Coordinator Access)
```bash
python manage.py createsuperuser
```

### 7. Run the Application
```bash
python manage.py runserver
```
Navigate to `http://127.0.0.1:8000/` in your browser.

---

## 📖 Usage Guide

1. **Initialize the Schedule:** Log in as the Coordinator (Superuser), navigate to the Coordinator Dashboard, and click **"Initialize Schedule Matrix"**. The backend Python algorithm will evaluate all constraints and write the successful timetable to the database.
2. **View as Student:** Create a new student account from the signup page, select a section, and view the personalized cohort schedule.
3. **View as Faculty:** Create a faculty account, select your teacher profile, and view your specific teaching itinerary.

---

## 📝 License
This project is for educational and portfolio purposes.