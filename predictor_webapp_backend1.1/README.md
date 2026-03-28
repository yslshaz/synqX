# synqX — AI Fatigue Detection & AI Coach for Athletes

> **Predict athlete fatigue in real-time using heart rate, body temperature and blood-oxygen data, powered by a trained ML model and a Flask web dashboard.**

---

## 📋 Prerequisites

Before you start, make sure you have these installed:

| Tool | Minimum version | Download |
|------|----------------|---------|
| **Python** | 3.10 or newer | https://www.python.org/downloads/ |
| **Git** | any recent version | https://git-scm.com/downloads |

> **Windows users:** when installing Python, tick **"Add Python to PATH"** on the first installer screen.

---

## 🚀 Step-by-step: run the app locally

### Step 1 — Clone the repository

Open a terminal (PowerShell on Windows, Terminal on Mac/Linux) and run:

```bash
git clone https://github.com/yslshaz/synqX.git
cd synqX
```

---

### Step 2 — Go into the backend folder

```bash
cd predictor_webapp_backend1
```

---

### Step 3 — Create a virtual environment

```bash
# Windows
python -m venv venv

# Mac / Linux
python3 -m venv venv
```

---

### Step 4 — Activate the virtual environment

```bash
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Mac / Linux
source venv/bin/activate
```

You will see `(venv)` appear at the start of your terminal prompt — that means it worked. ✅

---

### Step 5 — Install dependencies

```bash
pip install -r requirements.txt
```

This installs Flask, scikit-learn, pandas, SQLAlchemy and everything else the app needs.

---

### Step 6 — Start the Flask server

```bash
# Windows
python app.py

# Mac / Linux
python3 app.py
```

You should see output like:

```
 * Running on http://0.0.0.0:5000
 * Running on http://127.0.0.1:5000
```

---

### Step 7 — Open the app in your browser

Open your browser and go to:

```
http://127.0.0.1:5000
```

You will land on the **Welcome** page of SYNQ. 🎉

---

## 🖱️ Running from VS Code (easiest — just click a button!)

If you use **Visual Studio Code**, you can skip most of the terminal steps. The repository includes `.vscode/` config files that add run buttons directly to the editor.

### Option A — The ▶ Play / F5 button

1. Open the `synqX` folder in VS Code (`File → Open Folder`)
2. Activate your virtual environment first (Step 4 above, in the VS Code integrated terminal)
3. Click the **Run and Debug** icon in the left sidebar (or press `Ctrl+Shift+D` / `⇧⌘D` on Mac)
4. At the top of the panel, select **"▶ Run Flask App"** from the dropdown
5. Click the big green **▶** button (or press **`F5`**)

The integrated terminal opens, the server starts, and you visit `http://127.0.0.1:5000` in your browser.

### Option B — Terminal → Run Task menu

1. In the top menu bar click **Terminal**
2. Click **Run Task…**
3. Choose one of:
   - **Install Dependencies** — runs `pip install -r requirements.txt`
   - **Run Flask App** — starts the server on port 5000
   - **Test GET /api/athletes** — fires a test request to the athletes API

> **Keyboard shortcut:** Press `Ctrl+Shift+B` (Windows/Linux) or `⇧⌘B` (Mac) to launch **"Run Flask App"** instantly without opening any menu.

---

## 🗂️ Project structure

```
synqX/
└── predictor_webapp_backend1/   ← main app (run this)
    ├── app.py                   ← Flask server entry point
    ├── requirements.txt         ← Python dependencies
    ├── predictor.pkl            ← trained ML fatigue model
    ├── backend/
    │   ├── models.py            ← database table definitions
    │   ├── database.py          ← SQLite connection setup
    │   └── schemas.py           ← data validation
    ├── templates/               ← HTML pages served by Flask
    │   ├── welcome.html
    │   ├── dashboard.html
    │   ├── athletes.html
    │   ├── athleteprofile.html
    │   ├── onboarding.html
    │   └── mlpage.html
    └── static/
        ├── shared.css
        └── shared.js
```

---

## 🔌 API endpoints

| Method | URL | Description |
|--------|-----|-------------|
| `GET` | `/` | Welcome page |
| `GET` | `/dashboard` | Coach dashboard |
| `GET` | `/athletes` | Athlete list |
| `GET` | `/athleteprofile` | Athlete detail |
| `GET` | `/onboarding` | Onboarding wizard |
| `GET` | `/mlpage` | ML prediction page |
| `GET/POST` | `/api/athletes` | Fetch / add athletes (JSON) |
| `POST` | `/api/predict` | Run fatigue prediction (JSON) |
| `POST` | `/api/live_vitals` | Receive live sensor data (JSON) |

---

## 🛑 Stop the server

Press **`Ctrl + C`** in the terminal to stop the Flask server.

---

## ❓ Common issues

| Problem | Fix |
|---------|-----|
| `python: command not found` | Use `python3` instead of `python`, or re-install Python and tick "Add to PATH" |
| `ModuleNotFoundError: No module named 'flask'` | Make sure you activated the venv (Step 4) before running pip install |
| `Address already in use` (port 5000) | Another app is using port 5000. Stop it, or change the port in `app.py`: `app.run(port=5001)` |
| Browser shows "Connection refused" | The Flask server isn't running — go back to Step 6 |
| `No such file: predictor.pkl` | Make sure you are inside the `predictor_webapp_backend1/` folder before running `python app.py` |
