# green-footprint-tracker-0.1

# Greenline Nagpur Portal

A full-stack web application designed for the Greenline Nagpur Portal. The project features a Python-based backend API handling data and routing, paired with a lightweight, responsive frontend interface.

---

## 📁 Project Structure

```text
├── backend/
│   ├── app/
│   │   ├── main.py              # Application configurations
│   │   └── main_backup.py
│   ├── auth.py                  # User authentication & security
│   ├── database.py              # Database connection settings
│   ├── main.py                  # FastAPI / API Entry point
│   ├── models.py                # Database schemas (SQLAlchemy/SQLModel)
│   ├── routing.py               # API endpoint routers
│   └── seed.py                  # Database initialization script
├── data/
│   └── project.db               # SQLite database instance
├── frontend/
│   ├── app.js                   # Client-side logic & API integration
│   └── index.html               # Main user interface
├── greenline.db                 # Main SQLite database
├── requirements.txt             # Python dependencies
├── RESEARCH_DOCUMENTATION.md    # Background research and documentation
└── test_routes.py               # Backend integration and unit tests
```

---

## 🚀 Features

- **Robust Backend API:** Powered by Python and FastAPI/Uvicorn for high-performance routing.
- **Authentication:** Integrated user access control (`auth.py`).
- **Database Architecture:** Structured relational tables managed via SQLAlchemy/SQLite.
- **Dynamic Frontend:** Seamless data fetching and UI rendering with vanilla JavaScript.

---

## 🛠️ Local Development Setup

### Prerequisites
- Python 3.8+
- Git

### 1. Clone the Repository
```bash
git clone https://github.com
cd Greenline-Nagpur-Portal
```

### 2. Set Up a Virtual Environment
```bash
# Windows
python -m venv venv
source venv/Scripts/activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
.\venv\Scripts\python -m uvicorn backend.main:app --host 127.0.0.1 --port 8001

### 4. Seed the Database (Optional)
If your application requires initial baseline data setup, execute the seed script:
```bash
python backend/seed.py
```

### 5. Run the Application Localy
```bash
uvicorn backend.main:app --reload
```
The API documentation will be available locally at `http://127.0.0`.

---

### Deployed Link
https://greenline-nagpur-portal-1.onrender.com/


## 🌐 Deployment on Render

This application is optimized for deployment as a **Web Service** on Render.

- **Runtime:** `Python 3`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

*Note: Since the project uses a local SQLite database (`greenline.db`), data will reset when the free Render instance spins down. For production, consider connecting an external PostgreSQL instance via Environment Variables.*
