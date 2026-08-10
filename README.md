# 📦 SendIt API

SendIt API is a secure RESTful backend built with **FastAPI** for document management. It allows authenticated users to upload, organize, search, and manage documents while enriching uploaded files with **real-time weather data** based on the upload location. The API includes role-based access control, JWT authentication, file validation, rate limiting, webhook support, and automatic document versioning. :contentReference[oaicite:0]{index=0}

---

## ✨ Features

### 🔐 Authentication & Authorization

- User Registration
- JWT Authentication
- Password Hashing
- Login Endpoint
- Role-Based Access Control (RBAC)
- User Activation Check

Supported roles:

- Admin
- Manager
- Staff

---

### 📁 Document Management

- Upload documents
- Automatic file validation
- Document versioning
- Update document metadata
- Delete documents
- Retrieve document details
- List all documents
- Search documents using multiple filters

---

### 🌤 Weather Enrichment

Every uploaded document can automatically be enriched with weather information based on the provided city and country.

Features include:

- Automatic weather retrieval
- Manual enrichment
- Weather history
- Weather data endpoint

---

### 📂 File Upload Features

- PDF support
- DOCX support
- JPG/JPEG support
- PNG support
- File size validation
- Safe filename generation
- Asynchronous uploads

---

### 🔔 Webhooks

Administrators can register webhooks to receive notifications for document-related events.

---

### 🛡 Security

- JWT Authentication
- Password Hashing
- Rate Limiting
- Protected Endpoints
- File Validation
- Upload Restrictions

---

# 🚀 Technologies Used

- FastAPI
- SQLModel
- PostgreSQL
- SQLAlchemy
- Uvicorn
- Python 3.12+
- SlowAPI
- Pydantic
- aiofiles
- python-dotenv
- JWT Authentication

---

# 📁 Project Structure

```
sendit-api/
│
├── auth.py
├── main.py
├── requirements.txt
├── .env
│
├── database/
│   └── session.py
│
├── models/
│   ├── user.py
│   ├── document.py
│   └── webhook.py
│
├── services/
│   └── weather.py
│
├── uploads/
│
└── README.md
```

---

# ⚙️ Installation

## 1. Clone the repository

```bash
git clone https://github.com/yourusername/sendit-api.git
cd sendit-api
```

---

## 2. Create a virtual environment

Windows

```bash
python -m venv .venv
```

Activate

```bash
.venv\Scripts\activate
```

Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file.

Example:

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/sendit_db

SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

WEATHER_API_KEY=your-api-key
WEATHER_API_URL=https://api.open-meteo.com/v1/forecast

MAX_UPLOAD_SIZE=5242880
ALLOWED_EXTENSIONS=.pdf,.jpg,.jpeg,.png,.docx
```

---

# 🐳 Running with Docker

### docker-compose.yml

```yaml
services:
  db:
    image: postgres:16
    container_name: sendit_db
    environment:
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
      POSTGRES_DB: sendit_db
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

Start PostgreSQL

```bash
docker compose up -d
```

---

# ▶ Running the API

```bash
uv run uvicorn main:app --reload
```

or

```bash
uvicorn main:app --reload
```

The server will be available at

```
http://127.0.0.1:8000
```

---

# 📖 API Documentation

Swagger UI

```
http://127.0.0.1:8000/docs
```

ReDoc

```
http://127.0.0.1:8000/redoc
```

---

# 🔑 Authentication

Login

```
POST /login
```

Example response

```json
{
    "access_token": "...",
    "token_type": "bearer",
    "role": "manager"
}
```

Use the token

```
Authorization: Bearer YOUR_TOKEN
```

---

# 📄 API Endpoints

## Authentication

| Method | Endpoint |
|---------|----------|
| POST | /register |
| POST | /login |

---

## Documents

| Method | Endpoint |
|---------|----------|
| POST | /documents/upload |
| GET | /documents |
| GET | /documents/search |
| GET | /documents/{id} |
| PATCH | /documents/{id} |
| DELETE | /documents/{id} |

---

## Weather Enrichment

| Method | Endpoint |
|---------|----------|
| POST | /documents/{id}/enrich |
| GET | /documents/{id}/weather |

---

## Webhooks

| Method | Endpoint |
|---------|----------|
| POST | /webhooks/register |

---

# 🔐 User Roles

### Admin

- Manage all users
- Register webhooks
- View every document
- Delete documents
- Trigger enrichment

### Manager

- Manage documents
- Trigger enrichment
- View all documents
- Delete documents

### Staff

- Upload documents
- View only their own documents
- Search their own documents
- View weather information for their own uploads

---

# 📂 Supported File Types

- PDF
- DOCX
- JPG
- JPEG
- PNG

Maximum upload size:

```
5 MB
```

---

# 🚦 Rate Limits

| Endpoint | Limit |
|----------|-------|
| Register | 5 requests/minute |
| Login | 5 requests/minute |
| Upload Document | 10 requests/hour |
| List Documents | 30 requests/minute |
| Search Documents | 20 requests/minute |
| Weather Enrichment | 5 requests/minute |
| Weather Retrieval | 10 requests/minute |

---

# 📈 Future Improvements

- Email notifications
- Background task queue (Celery)
- Document OCR
- Virus scanning
- AWS S3 or Azure Blob Storage
- Document sharing
- Audit logging
- Docker deployment
- CI/CD pipeline
- Automated tests

---

# 👨‍💻 Author

**Francis Mwariri**

Bachelor of Business Information Technology (BBIT)

Dedan Kimathi University of Technology

---

# 📄 License

This project is licensed under the MIT License.