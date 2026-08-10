from datetime import datetime
import json
import os
from typing import Optional
from fastapi.responses import RedirectResponse
import aiofiles
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
    Depends,
    Request,
    Form,
)
from fastapi.security import OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlmodel import Session, select

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_admin,
    get_current_manager,
)

from database.session import (
    get_session,
    create_tables,
)

from models.user import (
    User,
    UserCreate,
    UserResponse,
)

from models.document import (
    Document,
    DocumentCreate,
    DocumentUpdate,
)
from models.webhook import Webhook

from services.weather import get_weather

load_dotenv()

app = FastAPI(
    title="C027-01-0888/2024 SendIt API",
    description="",
    version="1.0.0",
)

# ============================================================
# CONFIGURATION
# ============================================================

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE = int(
    os.getenv("MAX_UPLOAD_SIZE", 5 * 1024 * 1024)
)

ALLOWED_EXTENSIONS = [
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png",
    ".docx",
]

# ============================================================
# RATE LIMITING
# ============================================================

limiter = Limiter(key_func=get_remote_address)

app.state.limiter = limiter

app.add_exception_handler(
    RateLimitExceeded,
    _rate_limit_exceeded_handler,
)

# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
def startup():
    create_tables()

# ============================================================
# AUTHENTICATION
# ============================================================
import time
import psutil
import platform
@app.get("/health")
def health_check():
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "uptime": time.time() - start_time,
        "system": {
            "platform": platform.platform(),
            "python": platform.python_version()
        }
    }
@app.get("/metrics")
def get_metrics(current_user: User = Depends(get_current_admin)):
    """Metrics endpoint for monitoring (admin only)."""
    return {
        "cpu_percent": psutil.cpu_percent(),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage('/').percent
    }
import logging
from logging.handlers import RotatingFileHandler
import os
# Configure logging
LOG_FILE = os.getenv("LOG_FILE", "app.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(LOG_FILE, maxBytes=10485760, backupCount=5),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
# Add logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )
    return response
# ============================================================
# ROOT ENDPOINT
# ============================================================
@app.get("/", include_in_schema=False)
def root():
    return RedirectResponse(url="/docs")

@app.post("/register", status_code=201)
@limiter.limit("5/minute")
def register_user(
    request: Request,
    user_data: UserCreate,
    session: Session = Depends(get_session),
):

    existing = session.exec(
        select(User).where(
            User.username == user_data.username
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Username already exists",
        )

    existing = session.exec(
        select(User).where(
            User.email == user_data.email
        )
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Email already exists",
        )

    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hash_password(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
    )

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return {
        "message": "User registered successfully",
        "user": db_user,
    }


@app.post("/login")
@limiter.limit("5/minute")
def login_user(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
):

    user = session.exec(
        select(User).where(
            User.username == form_data.username
        )
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    if not verify_password(
        form_data.password,
        user.hashed_password,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Inactive user",
        )

    user.last_login = datetime.utcnow()

    session.commit()

    token = create_access_token(
        {
            "sub": user.username
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
    }
@app.post("/webhooks/register")
def register_webhook(
    webhook_url: str,
    event_type: str,
    current_user: User = Depends(get_current_admin),
    session: Session = Depends(get_session)
):
    """
    Register a webhook for document events.
    """

    webhook = Webhook(
        webhook_url=webhook_url,
        event_type=event_type
    )

    session.add(webhook)
    session.commit()
    session.refresh(webhook)

    return {
        "message": "Webhook registered successfully",
        "webhook_id": webhook.id,
        "webhook_url": webhook.webhook_url,
        "event_type": webhook.event_type
    }

# ============================================================
# FILE VALIDATION
# ============================================================

def validate_file(file: UploadFile):

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Allowed file types: {', '.join(ALLOWED_EXTENSIONS)}",
        )
 # ============================================================
# GET CURRENT USER
# ============================================================

@app.get(
    "/users/me",
    response_model=UserResponse
)
def get_my_profile(

    current_user: User = Depends(

        get_current_user

    )

):

    return current_user
# ============================================================
# FILE UPLOAD ENDPOINT
# ============================================================
@app.post("/documents/upload")
@limiter.limit("10/hour")
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    city: str = Form(...),
    description: Optional[str] = Form(None),
    country: str = Form("Kenya"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Upload a document with validation and weather enrichment.
    """

    validate_file(file)

    contents = await file.read()
    file_size = len(contents)

    if file_size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"Maximum file size is {MAX_FILE_SIZE // (1024 * 1024)} MB",
        )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    safe_filename = (
        f"{timestamp}_{current_user.id}_"
        f"{file.filename.replace(' ', '_')}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        safe_filename,
    )

    async with aiofiles.open(file_path, "wb") as out_file:
        await out_file.write(contents)

    existing_document = session.exec(
        select(Document)
        .where(Document.original_filename == file.filename)
        .order_by(Document.version.desc())
    ).first()

    version = 1

    if existing_document:
        version = existing_document.version + 1

    document = Document(
        filename=safe_filename,
        original_filename=file.filename,
        version=version,
        file_size=file_size,
        file_type=file.content_type or "application/octet-stream",
        status="processing",
        city=city,
        country=country,
        description=description,
        uploader_id=current_user.id,
        uploaded_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        file_path=file_path,
    )

    session.add(document)
    session.commit()
    session.refresh(document)

    try:
        weather = await get_weather(city, country)

        if weather:
            document.weather_data = json.dumps(weather)
            document.weather_fetched_at = datetime.utcnow()
            document.status = "enriched"
        else:
            document.status = "uploaded"

        session.commit()

    except Exception as e:
        print(f"Weather API Error: {e}")
        document.status = "uploaded"
        session.commit()

    return {
        "message": "Document uploaded successfully",
        "document_id": document.id,
        "filename": document.original_filename,
        "status": document.status,
    }
    # ============================================================
# DOCUMENT ENDPOINTS
# ============================================================

@app.get("/documents")
@limiter.limit("30/minute")
def list_documents(
    request: Request,
    status: Optional[str] = None,
    city: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    List documents.
    Admins and managers see all documents.
    Staff only see documents they uploaded.
    """

    query = select(Document)

    if current_user.role not in ["admin", "manager"]:
        query = query.where(
            Document.uploader_id == current_user.id
        )

    if status:
        query = query.where(
            Document.status == status
        )

    if city:
        query = query.where(
            Document.city == city
        )

    return session.exec(query).all()
@app.get("/documents/search")
@limiter.limit("20/minute")
def search_documents(
    request: Request,
    q: Optional[str] = None,
    city: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """
    Search documents with multiple filters.
    """
    query = select(Document)

    # Staff can only see their own documents
    if current_user.role not in ["admin", "manager"]:
        query = query.where(Document.uploader_id == current_user.id)

    # Search by filename or description
    if q:
        query = query.where(
            (Document.original_filename.contains(q)) |
            (Document.description.contains(q))
        )

    # Filter by city
    if city:
        query = query.where(Document.city == city)

    # Filter by status
    if status:
        query = query.where(Document.status == status)

    # Filter by upload date
    if date_from:
        query = query.where(Document.uploaded_at >= date_from)

    if date_to:
        query = query.where(Document.uploaded_at <= date_to)

    documents = session.exec(query).all()

    return {
        "count": len(documents),
        "documents": documents
    }


@app.get("/documents/{document_id}")
@limiter.limit("30/minute")
def get_document(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get one document.
    """

    document = session.get(
        Document,
        document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if (
        current_user.role not in ["admin", "manager"]
        and document.uploader_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied",
        )

    return document


@app.patch("/documents/{document_id}")
def update_document(
    document_id: int,
    document_update: DocumentUpdate,
    current_user: User = Depends(get_current_manager),
    session: Session = Depends(get_session),
):
    """
    Update document details.
    """

    document = session.get(
        Document,
        document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    update_data = document_update.dict(
        exclude_unset=True
    )

    for key, value in update_data.items():
        setattr(document, key, value)

    document.updated_at = datetime.utcnow()

    session.commit()
    session.refresh(document)

    return document


@app.delete("/documents/{document_id}")
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_manager),
    session: Session = Depends(get_session),
):
    """
    Delete a document.
    Only managers and admins can delete.
    """

    document = session.get(
        Document,
        document_id,
    )

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if os.path.exists(document.file_path):
        os.remove(document.file_path)

    session.delete(document)
    session.commit()

    return {
        "message": "Document deleted successfully"
    }



    # ============================================================
# DOCUMENT ENRICHMENT ENDPOINTS
# ============================================================

@app.post("/documents/{document_id}/enrich")
@limiter.limit("5/minute")
async def enrich_document(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_manager),
    session: Session = Depends(get_session),
):
    """
    Manually trigger weather enrichment for a document.
    Useful for documents that failed initial enrichment.
    """

    document = session.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    if document.status == "enriched":
        return {
            "message": "Document already enriched"
        }

    weather_data = await get_weather(
        document.city,
        document.country
    )

    if weather_data and "error" not in weather_data:
        document.weather_data = json.dumps(weather_data)
        document.weather_fetched_at = datetime.utcnow()
        document.status = "enriched"

        session.commit()

        return {
            "message": "Document enriched successfully",
            "weather": weather_data
        }

    document.status = "failed"
    session.commit()

    raise HTTPException(
        status_code=500,
        detail="Failed to enrich document with weather data"
    )


@app.get("/documents/{document_id}/weather")
@limiter.limit("10/minute")
def get_document_weather(
    request: Request,
    document_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Get the weather data associated with a document.
    """

    document = session.get(Document, document_id)

    if not document:
        raise HTTPException(
            status_code=404,
            detail="Document not found"
        )

    # Staff can only view their own documents
    if (
        current_user.role not in ["admin", "manager"]
        and document.uploader_id != current_user.id
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied"
        )

    if not document.weather_data:
        raise HTTPException(
            status_code=404,
            detail="No weather data available for this document"
        )

    return {
        "document_id": document.id,
        "city": document.city,
        "country": document.country,
        "weather": json.loads(document.weather_data),
    }
