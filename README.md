# Chore Manager API

A lightweight self-hosted FastAPI backend that exposes a personal Obsidian vault through a secure HTTP API.

This backend is designed to:

* Authenticate users via UUID
* Read and write Markdown files inside an Obsidian vault
* Serve data to a static frontend (GitHub Pages)
* Run locally and be exposed via Cloudflare Tunnel

For the purpose of:

* Personal use/household chore management
* Learning FastAPI and secure local development

---

## Architecture Overview

Frontend (GitHub Pages → Deployed to chores.lillywhite.dev)

↓

Cloudflare Tunnel

↓

FastAPI (localhost)

↓

Obsidian Vault (local storage)

The vault is **not committed to this repository**.

---

## Tech Stack

* Python 3.11+
* FastAPI
* Uvicorn
* python-frontmatter
* Cloudflare Tunnel (deployment)

---

## Project Structure

```
Chore-Manager/
├── application/
│   ├── __init__.py
│   ├── app_backend.py
│   ├── app_runtime.py
│   └── main.py
├── vault/  # Local Obsidian vault (excluded from version control, included for reference)
│   ├── .obsidian/
│   │   ├── app.json
│   │   ├── appearance.json
│   │   ├── core-plugins.json
│   │   ├── graph.json
│   │   └── workspace.json
│   ├── chores/
│   │   └── 2026/
│   │       └── 10/  # Year/Week-based organization
│   │           ├── 2026-03-02.md
│   │           ├── 2026-03-03.md
│   │           └── 2026-03-04.md
│   ├── data/
│   │   ├── users/
│   │   │   ├── foo.md
│   │   │   └── bar.md
│   │   └── variables/
│   │       ├── ALGORITHM.md
│   │       └── SECRET_KEY.md
│   └── people/
│       └── 2026/ 
│           └── 10/
│               ├── foo.md
│               └── bar.md
├── requirements.txt
└── README.md

I am aware this could probably be improved. 
This is just a starting point for the project structure. 

The `vault/` directory is included here for reference but should be excluded from version control in practice.
```

---

## Local Setup

### 1. Clone the repo

```
git clone https://github.com/SophiaLilly/Chore-Manager
cd Chore-Manager
```

### 2. Create a virtual environment

```
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### 3. Install dependencies

```
pip install -r requirements.txt
```

### 4. Run the server

```
uvicorn app:app --reload
```

Server will be available at:

```
http://localhost:8000
```

---

## Authentication Model

* Users are stored as Markdown files in the Obsidian vault
* Each user file contains YAML frontmatter:

```
---
best_streak: 0
current_streak: 0
display_name: Test_User
last_completion_date: '1970-01-01'
last_streak_check: '1970-01-01'
permissions:
- admin
uuid: 12345678-9abc-def1-2345-6789abcdef12
---
```

---

## Deployment

This backend is intended to run locally and be exposed using:

Cloudflare Tunnel → HTTPS public endpoint

Example:

```
cloudflared tunnel --url http://localhost:8000
```

---

## Security Notes

* The Obsidian vault is not version controlled
* CORS must be configured for the frontend origin

---

## License

Public Open-Source Project. Do whatever you want with it.
