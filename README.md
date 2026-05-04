# Tayyib.io — Halal Ingredient Checker

> **Is it Halal?** Instantly analyze food products by ingredient text, barcode, or label photo — with full madhab-specific rulings.

**Tayyib.io** is a complete Islamic dietary compliance platform consisting of a powerful Django backend API and a modern web interface. It helps Muslims determine whether a food product is **Halal**, **Haram**, or **Questionable** according to the four major madhabs (Hanafi, Maliki, Shafi'i, Hanbali).

**Companion Mobile App:** [tayyib-app](https://github.com/java-rakhmonaliev/tayyib-app)

---

## Features

### Core Analysis
- **Text Analysis** — Paste any ingredient list for instant classification
- **Barcode Lookup** — Fetch product data from Open Food Facts (3M+ products)
- **Image Analysis** — Upload a label photo; Groq Vision extracts ingredients + detects halal logos
- **Madhab-Aware Classification** — Full support for Hanafi, Maliki, Shafi'i, and Hanbali rulings

### Backend
- **150+ Pre-seeded Ingredients** — Including all E-codes with source citations
- **AI Fallback** — Unknown ingredients classified by Groq Llama 3.3 70B
- **JWT Authentication** — Secure user profiles with madhab preference
- **Admin Panel** — Manage ingredient database via Django admin

### Modern Web Interface
- **Beautiful Dark-First UI** — Matches the Flutter mobile app design system
- **Full JWT Auth** — Login, register, and profile management on the web
- **Real-time Analysis** — Instant results with detailed ingredient breakdown
- **Dark/Light Theme Toggle** — Smooth theme switching with localStorage persistence
- **Madhab Selector** — Switch between the four schools of thought on every page
- **Responsive Design** — Works perfectly on desktop and mobile

---

## Tech Stack

| Layer              | Technology                                      |
|--------------------|-------------------------------------------------|
| Framework          | Django 6.0 + Django REST Framework              |
| Database           | PostgreSQL 16                                   |
| Authentication     | SimpleJWT                                       |
| AI (Text)          | Groq Llama 3.3 70B                              |
| AI (Vision)        | Groq Llama 4 Scout Vision                       |
| Barcode Lookup     | Open Food Facts API                             |
| Frontend           | Tailwind CSS + Vanilla JS                       |
| Deployment         | Docker + Gunicorn + Nginx + AWS EC2 + RDS       |
| IaC                | Terraform                                       |
| CI/CD              | GitHub Actions                                  |

---

## Quick Start (Local Development)

### Prerequisites
- Python 3.12+
- PostgreSQL
- Groq API key → [console.groq.com](https://console.groq.com)

### Setup

```bash
git clone https://github.com/java-rakhmonaliev/tayyib.io.git
cd tayyib.io

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your GROQ_API_KEY and database credentials

python manage.py migrate
python manage.py seed_ingredients
python manage.py createsuperuser
python manage.py runserver
```

**Web UI will be available at** `http://127.0.0.1:8000`

---

## Production API

**Live Backend:** `http://13.217.178.63`

All analysis endpoints accept the `madhab` parameter:
- `hanafi`
- `maliki`
- `shafii`
- `hanbali`

---

## Key API Endpoints

| Method | Endpoint                        | Description                              |
|--------|---------------------------------|------------------------------------------|
| POST   | `/api/auth/register/`           | Register new user + return JWT           |
| POST   | `/api/auth/login/`              | Login + JWT tokens                       |
| GET    | `/api/auth/profile/`            | Get current user + madhab                |
| PATCH  | `/api/auth/profile/update/`     | Update madhab or country                 |
| POST   | `/api/analyze/text/`            | Analyze raw ingredient text              |
| POST   | `/api/analyze/barcode/`         | Analyze by barcode (Open Food Facts)     |
| POST   | `/api/analyze/image/`           | Analyze product label photo (OCR + AI)   |

---

## Madhab Differences (Seafood Example)

| Ingredient       | Hanafi     | Maliki     | Shafi'i    | Hanbali    |
|------------------|------------|------------|------------|------------|
| Shrimp / Prawns  | ❌ Haram   | ✅ Halal   | ✅ Halal   | ✅ Halal   |
| Crab / Lobster   | ❌ Haram   | ❌ Haram   | ✅ Halal   | ✅ Halal   |
| Shark            | ❌ Haram   | ✅ Halal   | ✅ Halal   | ✅ Halal   |
| Bony Fish        | ✅ Halal   | ✅ Halal   | ✅ Halal   | ✅ Halal   |

The backend automatically applies the correct ruling based on the user's selected madhab.

---

## Project Structure

```
tayyib.io/
├── core/
│   ├── models.py              # Ingredient, AnalysisResult, UserProfile...
│   ├── classifier.py          # Core classification engine
│   ├── ai_fallback.py         # Groq AI for unknown ingredients
│   ├── ocr.py                 # Groq Vision + halal logo detection
│   ├── barcode.py             # Open Food Facts integration
│   ├── api_views.py           # Main analysis endpoints
│   ├── auth_views.py          # Register, login, profile
│   ├── management/commands/seed_ingredients.py
│   └── templates/             # Modern web UI (dark-first, Flutter-style)
├── tayyib_io/
│   ├── settings.py
│   └── urls.py
├── infra/                     # Terraform (AWS)
├── nginx/nginx.conf
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

## DevOps & Infrastructure

Tayyib.io uses infrastructure as code and automated CI/CD for reliable deployments.

### Infrastructure as Code
- **Terraform** — Complete AWS infrastructure defined as code (EC2 t3.micro + RDS PostgreSQL t3.micro)
- **Reproducible** — One command to provision the entire environment

### CI/CD Pipeline
- **GitHub Actions** — Automatic build and deployment on every push to `main`
- **Docker-based** — Consistent deployment using Docker, Gunicorn, and Nginx

### Current Production
- Live server: `http://13.217.178.63`
- Single EC2 instance + managed PostgreSQL database
- Fully containerized with Docker

---

## Deployment

The project can be fully deployed using Terraform + GitHub Actions. Production is currently live at `http://13.217.178.63`.

---

## Disclaimer

Tayyib.io is an **assistive tool**, not a religious fatwa. Always consult a qualified Islamic scholar or certified halal authority for important dietary decisions.

---

## License

MIT License © 2026 Javokhirbek Rakhmonaliev

---

**Built with Django + Groq AI** — for the Ummah.

*Last updated: May 2026*
