import logging
import time
import secrets
from fastapi import FastAPI, Depends, HTTPException, status, APIRouter, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app import crud, models, schemas
from app.database import SessionLocal, engine
from prometheus_fastapi_instrumentator import Instrumentator
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create database tables
models.Base.metadata.create_all(bind=engine)

# FastAPI app initialization
app = FastAPI(
    title="Customer Service API",
    description="Manage customer data with CRUD operations.",
    version="1.0.0",
    openapi_url="/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Middleware for logging requests and responses, masking sensitive data
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log the request method and URL (without sensitive data)
    logger.info(f"Request: {request.method} {request.url}")

    # Process the request
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return JSONResponse(status_code=500, content={"message": "Internal Server Error"})

    # Log the response and processing time
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} for {request.method} {request.url} in {process_time:.4f}s")
    return response

# Authentication setup (masking sensitive credentials)
security = HTTPBasic()
USERNAME = "admin"
PASSWORD = "password"

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    if not (correct_username and correct_password):
        logger.warning(f"Authentication failed for user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    # Log only username, avoid logging the password
    logger.info(f"User authenticated: {credentials.username}")
    return credentials

# Dependency for database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Instrumentation for metrics and tracing
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Set the service name explicitly
resource = Resource.create({"service.name": "APIpotamus"})

# Tracing provider setup
provider = TracerProvider(resource=resource)
jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",  # Ensure this hostname is correct
    agent_port=6831
)
span_processor = BatchSpanProcessor(jaeger_exporter)
provider.add_span_processor(span_processor)
FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)

# Versioned API router
router_v1 = APIRouter(prefix="/v1")

# Mask email address for privacy
def mask_email(email: str) -> str:
    username, domain = email.split("@")
    masked_username = username[0] + "***" + username[-1]
    return masked_username + "@" + domain

# POST: Create a new customer (avoid logging email directly)
@router_v1.post("/customers/", response_model=schemas.Customer, dependencies=[Depends(authenticate)], tags=["Customer Operations"])
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    # Log without exposing sensitive details
    logger.info(f"Creating customer with masked email: {mask_email(customer.email)}")
    db_customer = crud.get_customer_by_email(db, email=customer.email)
    if db_customer:
        logger.warning(f"Email already registered (masked): {mask_email(customer.email)}")
        raise HTTPException(status_code=400, detail="Email already registered")
    created_customer = crud.create_customer(db=db, customer=customer)
    logger.info(f"Customer created (masked): {mask_email(created_customer.email)}")
    return created_customer

# GET: Retrieve all customers (with pagination)
@router_v1.get("/customers/", response_model=list[schemas.Customer], dependencies=[Depends(authenticate)], tags=["Customer Operations"])
def read_customers(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    logger.info(f"Retrieving customers with skip={skip} and limit={limit}")
    customers = crud.get_customers(db, skip=skip, limit=limit)
    logger.info(f"Retrieved {len(customers)} customers")
    return customers

# GET: Retrieve a customer by ID
@router_v1.get("/customers/{customer_id}", response_model=schemas.Customer, dependencies=[Depends(authenticate)], tags=["Customer Operations"])
def read_customer(customer_id: int, db: Session = Depends(get_db)):
    logger.info(f"Retrieving customer with ID: {customer_id}")
    customer = crud.get_customer(db, customer_id=customer_id)
    if not customer:
        logger.warning(f"Customer with ID {customer_id} not found")
        raise HTTPException(status_code=404, detail="Customer not found")
    logger.info(f"Customer found: {mask_email(customer.email)}")
    return customer

# GET: Retrieve a customer by email
@router_v1.get("/customers/email/{email}", response_model=schemas.Customer, dependencies=[Depends(authenticate)], tags=["Customer Operations"])
def read_customer_by_email(email: str, db: Session = Depends(get_db)):
    logger.info(f"Retrieving customer with email: {mask_email(email)}")
    customer = crud.get_customer_by_email(db, email=email)
    if not customer:
        logger.warning(f"Customer with email {mask_email(email)} not found")
        raise HTTPException(status_code=404, detail="Customer not found")
    logger.info(f"Customer found (masked): {mask_email(customer.email)}")
    return customer

# PUT: Update a customer by ID
@router_v1.put("/customers/{customer_id}", response_model=schemas.Customer, dependencies=[Depends(authenticate)], tags=["Customer Operations"])
def update_customer(customer_id: int, customer: schemas.CustomerUpdate, db: Session = Depends(get_db)):
    logger.info(f"Updating customer with ID: {customer_id}")
    db_customer = crud.get_customer(db, customer_id=customer_id)
    if not db_customer:
        logger.warning(f"Customer with ID {customer_id} not found")
        raise HTTPException(status_code=404, detail="Customer not found")
    updated_customer = crud.update_customer(db=db, customer_id=customer_id, customer=customer)
    logger.info(f"Customer updated (masked): {mask_email(updated_customer.email)}")
    return updated_customer

# DELETE: Remove a customer by ID
@router_v1.delete("/customers/{customer_id}", response_model=schemas.Customer, dependencies=[Depends(authenticate)], tags=["Customer Operations"])
def delete_customer(customer_id: int, db: Session = Depends(get_db)):
    logger.info(f"Deleting customer with ID: {customer_id}")
    customer = crud.get_customer(db, customer_id=customer_id)
    if not customer:
        logger.warning(f"Customer with ID {customer_id} not found")
        raise HTTPException(status_code=404, detail="Customer not found")
    crud.delete_customer(db=db, customer_id=customer_id)
    logger.info(f"Customer with ID {customer_id} deleted")
    return customer

# Include the versioned router
app.include_router(router_v1)
