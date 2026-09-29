# DSAapp Local Development Guide

## Prerequisites
* **Python:** 3.11+ (Python 3.13 tested)
* **Node.js:** v20+ (Node.js v24.19 tested)
* **npm:** v10+ (npm 11.17 tested)
* **Git:** 2.40+ (Git 2.50 tested)

---

## 1. Initial Setup

### Clone Repository & Inspect Environment
```bash
git clone <repo-url> dsaapp
cd dsaapp
```

### Configure Environment Variables
Copy the environment template to create your local `.env`:
```bash
cp .env.example .env
```
*(On Windows PowerShell: `Copy-Item .env.example .env`)*

---

## 2. Backend Setup & Startup

### Create & Activate Python Virtual Environment
```bash
python -m venv backend/.venv

# Windows PowerShell:
.\backend\.venv\Scripts\Activate.ps1

# Linux / macOS:
source backend/.venv/bin/activate
```

### Install Backend Dependencies
```bash
pip install -r backend/requirements.txt
```

### Run the FastAPI Development Server
```bash
uvicorn backend.app.main:app --reload --port 8000
```
* **API Endpoint:** `http://localhost:8000`
* **Swagger Documentation:** `http://localhost:8000/docs` (available in development mode)
* **Health Check:** `http://localhost:8000/health` or `http://localhost:8000/api/v1/health`

---

## 3. Frontend Setup & Startup

### Install Dependencies
```bash
cd frontend
npm install
```

### Start Vite Development Server
```bash
npm run dev
```
* **Frontend Application:** `http://localhost:5173`
* Vite automatically proxies `/api` and `/health` requests to `http://localhost:8000`.

---

## 4. Code Standards & Architecture Guidelines
* **Strict Layering:** Routes $\rightarrow$ Schemas $\rightarrow$ Services $\rightarrow$ Repositories $\rightarrow$ Database.
* **No `exec()` / `eval()`:** Never run arbitrary student code inside backend handlers.
* **TypeScript Strict Mode:** Maintain `strict: true` with zero `any` or `@ts-ignore` overrides.
* **Secrets:** Never commit `.env` or plaintext credentials to Git.
