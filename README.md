# 🏥 AI Medical Appointment & Disease Prediction System

A full-stack web application built with **Flask**, **scikit-learn**, **MySQL**, and **Bootstrap 5**.  
Patients can check possible diseases from symptoms using a trained Random Forest model, and book appointments with specialists.

---

## 📁 Project Structure

```
medical_ai_system/
├── backend/
│   ├── app.py              # Main Flask application
│   ├── train_model.py      # ML model training script
│   ├── config.py           # Database & app configuration
│   ├── disease_model.pkl   # Saved model (generated after training)
│   └── model_meta.json     # Symptom list & metadata (generated)
├── dataset/
│   └── disease_dataset.csv # Symptom-disease training data
├── templates/
│   ├── partials/
│   │   └── navbar.html
│   ├── index.html
│   ├── register.html
│   ├── login.html
│   ├── dashboard.html
│   ├── predict.html
│   ├── appointment.html
│   ├── history.html
│   ├── doctor_dashboard.html
│   └── admin_dashboard.html
├── static/
│   ├── css/style.css
│   └── js/ images/
├── schema.sql              # MySQL schema + seed data
├── requirements.txt
└── README.md
```

---

## ⚙️ Prerequisites

| Tool | Version |
|------|---------|
| Python | 3.9 + |
| MySQL  | 8.0 +  |
| pip    | latest |

---

## 🚀 Setup Instructions

### 1. Clone / unzip the project

```bash
cd medical_ai_system
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL

Open **`backend/config.py`** and set your credentials:

```python
MYSQL_USER     = "root"
MYSQL_PASSWORD = "your_mysql_password"
MYSQL_DB       = "medical_ai_db"
```

### 5. Create the database and tables

```bash
mysql -u root -p < schema.sql
```

This creates the `medical_ai_db` database, all tables, and seeds demo accounts.

### 6. Train the machine-learning model

```bash
cd backend
python train_model.py
```

This generates:
- `backend/disease_model.pkl` — the trained Random Forest model
- `backend/model_meta.json`   — symptom list and metadata used by the app

### 7. Run the Flask application

```bash
# Still inside backend/
python app.py
```

Visit **http://localhost:5000** in your browser.

---

## 🔐 Demo Credentials

| Role   | Email                        | Password   |
|--------|------------------------------|------------|
| Admin  | admin@medipredict.ai         | admin123   |
| Doctor | doctor@medipredict.ai        | doctor123  |

Register a new account for a patient role.

---

## 🧠 Machine Learning Details

- **Algorithm:** Random Forest Classifier (200 estimators)
- **Dataset:** 41 diseases × 132 symptom features
- **Encoding:** `LabelEncoder` for disease labels
- **Output:** Predicted disease + confidence percentage + top-3 alternatives
- **Persistence:** `joblib.dump()` → `.pkl` bundle (model + encoder + symptom list)

---

## 🌐 API Endpoints

| Method | Endpoint              | Description                          |
|--------|-----------------------|--------------------------------------|
| GET    | `/`                   | Landing page                         |
| GET/POST | `/register`         | Patient registration                 |
| GET/POST | `/login`            | User login                           |
| GET    | `/logout`             | Clear session                        |
| GET    | `/dashboard`          | Patient dashboard                    |
| GET/POST | `/predict`          | Symptom checker (form-based)         |
| POST   | `/api/predict`        | AJAX prediction endpoint (JSON)      |
| GET    | `/api/symptoms`       | Returns full symptom list as JSON    |
| GET/POST | `/appointment`      | Book appointment                     |
| GET    | `/history`            | Prediction history                   |
| GET    | `/doctor/dashboard`   | Doctor panel                         |
| POST   | `/doctor/appointment/<id>/status` | Update appointment status |
| GET    | `/admin/dashboard`    | Admin panel                          |
| POST   | `/admin/doctor/add`   | Add a new doctor                     |
| POST   | `/admin/doctor/delete/<id>` | Remove a doctor             |

---

## 🛡️ Security Features

- **Password hashing** — SHA-256 (upgrade to bcrypt for production)
- **Session management** — server-side Flask sessions
- **SQL injection prevention** — parameterised queries via `mysql-connector-python`
- **Role-based access** — decorators enforce patient / doctor / admin routes

---

## 🎓 Final Year Project Notes

This system demonstrates:
1. Full-stack web development (Flask REST API + Bootstrap 5 frontend)
2. Machine learning integration (scikit-learn Random Forest)
3. Relational database design (MySQL with FK constraints)
4. User authentication & role-based authorization
5. AJAX / Fetch API for async prediction requests
6. Responsive UI with dark theme design system

---

*For demo purposes only. Not a substitute for professional medical advice.*
