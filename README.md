# Tayyib.io — Halal Ingredient Checker

> **Is it Halal?** Instantly analyze food products by ingredient text, barcode, or label photo.

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square)
![Django](https://img.shields.io/badge/Django-6.0-green?style=flat-square)
![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED?style=flat-square)
![AWS](https://img.shields.io/badge/AWS-EC2%20%2B%20RDS-FF9900?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat-square)

---

## Overview

**Tayyib.io** is an Islamic dietary compliance checker that helps Muslims determine whether a food product is **Halal**, **Haram**, or **Questionable**. It supports both **Hanafi** and **Shafi'i** madhabs, accounting for their differences in ruling on seafood and other ingredients.

### Features

- **Text Analysis** — Paste any ingredient list for instant classification
- **Barcode Scanner** — Fetch product info from Open Food Facts (3M+ products)
- **Image Analysis** — Upload a label photo; AI reads and classifies ingredients
- **Madhab Toggle** — Switch between Hanafi and Shafi'i rulings
- **Halal Logo Detection** — Automatically detects halal certification logos on packaging
- **Source Citations** — Every verdict includes an Islamic dietary reference
- **AI Fallback** — Unknown ingredients sent to Llama 3 via Groq for classification
- **Admin Panel** — Manage ingredient database via Django admin

---

## Tech Stack

### Application
| Layer | Technology |
|---|---|
| Backend | Django 6.0 + Gunicorn |
| Database | PostgreSQL 16 |
| AI Classification | Groq API (Llama 3.3 70B + Llama 4 Scout Vision) |
| Barcode Lookup | Open Food Facts API |
| Image Analysis | Groq Vision (Llama 4 Scout) |
| Frontend | Django Templates (Neo-brutalism UI) |

### DevOps
| Layer | Technology |
|---|---|
| Containerization | Docker + Docker Compose |
| Reverse Proxy | Nginx |
| Infrastructure | AWS EC2 + RDS (Terraform) |
| CI/CD | GitHub Actions |
| IaC | Terraform |

---

## Architecture

```
User Request
     │
     ▼
  Nginx (port 80/443)
     │
     ▼
  Gunicorn (port 8000)
     │
     ▼
  Django Application
     │
     ├── DB Lookup (PostgreSQL/RDS)
     │     └── 150+ pre-seeded ingredients + E-codes
     │
     └── AI Fallback (Groq API)
           ├── Text: Llama 3.3 70B
           └── Image: Llama 4 Scout Vision
```

### Classification Logic

```
Input (text / barcode / image)
        │
        ▼
   Parse Ingredients
        │
        ▼
   DB Lookup ──── Found ──── Apply Madhab Rules ──── Verdict
        │
      Not Found
        │
        ▼
   Groq AI Fallback
        │
        ▼
   Verdict: halal / questionable / haram
```

---

## Local Development

### Prerequisites
- Python 3.12+
- PostgreSQL
- Groq API key (free at [console.groq.com](https://console.groq.com))

### Setup

```bash
# Clone the repository
git clone https://github.com/java-rakhmonaliev/tayyib.io.git
cd tayyib.io

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env
# Edit .env with your values

# Create database
createdb tayyib_io

# Run migrations
python manage.py migrate

# Seed ingredient database
python manage.py seed_ingredients

# Create admin user
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Environment Variables

```env
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost 127.0.0.1

DB_NAME=tayyib_io
DB_USER=your_db_user
DB_PASSWORD=
DB_HOST=localhost
DB_PORT=5432

GROQ_API_KEY=your-groq-api-key
```

---

## Deployment

Infrastructure is provisioned with Terraform on AWS. CI/CD is handled by GitHub Actions.

### Infrastructure (Terraform)

```bash
cd infra

# Initialize
terraform init

# Preview changes
terraform plan

# Apply (provisions EC2 + RDS + VPC + Security Groups)
terraform apply
```

**Provisioned Resources:**
- VPC with public/private subnets
- EC2 t3.micro (application server)
- RDS PostgreSQL t3.micro (managed database)
- Security groups (ports 22, 80, 443, 5432)
- Elastic IP

### CI/CD (GitHub Actions)

Every push to `main` triggers automatic deployment:

```
Push to main
     │
     ▼
GitHub Actions
     │
     ├── SSH into EC2
     ├── git pull origin main
     ├── docker compose down
     ├── docker compose up -d --build
     ├── python manage.py migrate
     └── python manage.py collectstatic
```

**Required GitHub Secrets:**
| Secret | Value |
|---|---|
| `EC2_HOST` | EC2 public IP address |
| `EC2_SSH_KEY` | Private SSH key content |

### Manual Deployment

```bash
# SSH into server
ssh -i ~/.ssh/id_ed25519 ubuntu@your-ec2-ip

# Clone and configure
git clone https://github.com/java-rakhmonaliev/tayyib.io.git /app/tayyib.io
cd /app/tayyib.io
nano .env  # Add production environment variables

# Start services
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py seed_ingredients
docker compose exec web python manage.py createsuperuser
```

---

## Ingredient Database

The app ships with 150+ pre-seeded ingredients including:

- **E-codes** (E100–E968) with halal status
- **Animal derivatives** (gelatin, glycerin, lard, carmine etc.)
- **Seafood** with madhab-specific rulings
- **Additives and emulsifiers** with source analysis
- **Common ingredients** (grains, oils, spices, sweeteners)

To expand the database, add entries to `core/management/commands/seed_ingredients.py` and re-run:

```bash
python manage.py seed_ingredients
```

---

## Madhab Differences

| Ingredient | Hanafi | Shafi'i |
|---|---|---|
| Shrimp / Prawns | ❌ Haram | ✅ Halal |
| Crab / Lobster | ❌ Haram | ✅ Halal |
| Shellfish | ❌ Haram | ✅ Halal |
| Shark | ❌ Haram | ✅ Halal |
| Bony Fish | ✅ Halal | ✅ Halal |
| Eggs | ✅ Halal | ✅ Halal |

---

## Project Structure

```
tayyib.io/
├── core/
│   ├── models.py           # Ingredient, AnalysisResult
│   ├── views.py            # All request handlers
│   ├── classifier.py       # Core classification engine
│   ├── ai_fallback.py      # Groq AI for unknown ingredients
│   ├── ocr.py              # Groq Vision for image analysis
│   ├── barcode.py          # Open Food Facts integration
│   ├── admin.py            # Django admin configuration
│   └── management/
│       └── commands/
│           └── seed_ingredients.py
├── templates/
│   ├── base.html
│   └── core/
│       ├── index.html
│       └── result.html
├── infra/
│   ├── main.tf             # AWS infrastructure
│   ├── variables.tf
│   └── outputs.tf
├── nginx/
│   └── nginx.conf
├── .github/
│   └── workflows/
│       └── deploy.yml
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

---

## Disclaimer

Tayyib.io is a tool to assist in identifying potentially problematic ingredients. It is **not a fatwa** and should not replace consultation with a qualified Islamic scholar for critical dietary decisions. Always verify with certified halal authorities when in doubt.

---

## License

MIT License — feel free to use, modify, and distribute.

---

*Built with Django, deployed on AWS, powered by Groq AI.*
