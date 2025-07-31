from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import sessionmaker, Session, relationship, joinedload, declarative_base
from pydantic import BaseModel
from typing import List
import os


DB_USER = os.getenv("PG_USER", "postgres")
DB_PASSWORD = os.getenv("PG_PASSWORD") # The script will fail if this isn't set
DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = os.getenv("PG_PORT", "5432")
DB_NAME = os.getenv("PG_DBNAME", "ecommerce")

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# SQLAlchemy setup
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# --- 2. SQLAlchemy ORM Models (Updated for Normalization) ---

# NEW: Model for the `departments` table
class DepartmentModel(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)

# UPDATED: The ProductModel now uses a relationship to departments
class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    cost = Column(Numeric(10, 5))
    category = Column(String, index=True)
    name = Column(String, index=True)
    brand = Column(String)
    retail_price = Column(Numeric(10, 2))
    sku = Column(String, unique=True, index=True)
    distribution_center_id = Column(Integer)
    
    # Foreign Key that links to the 'departments' table
    department_id = Column(Integer, ForeignKey("departments.id"))
    
    # Relationship that allows SQLAlchemy to automatically join and load department data
    department = relationship("DepartmentModel")


# --- 3. Pydantic Models (Updated for Normalization) ---

# NEW: Pydantic model for the Department to define API response shape
class Department(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

# UPDATED: The Product model now expects a nested Department object
class Product(BaseModel):
    id: int
    cost: float
    category: str
    name: str
    brand: str
    retail_price: float
    department: Department  # This now expects the Department model, not a string
    sku: str
    distribution_center_id: int

    class Config:
        from_attributes = True


# --- 4. FastAPI App Initialization & CORS ---

app = FastAPI(
    title="Products API",
    description="A RESTful API for reading product data with normalized tables.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- 5. Dependency for Database Session ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 6. API Endpoints (Updated for Normalization) ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Products API v2. Go to /docs for documentation."}


@app.get("/api/products", response_model=List[Product], tags=["Products"])
def get_all_products(skip: int = 0, limit: int = 25, db: Session = Depends(get_db)):
    """
    List all products with pagination. Department information is joined automatically.
    """
    # UPDATED QUERY: Use `options(joinedload(...))` for an efficient Eager Load JOIN.
    # This prevents the "N+1 query problem".
    products = db.query(ProductModel).options(
        joinedload(ProductModel.department)
    ).offset(skip).limit(limit).all()
    return products


@app.get("/api/products/{product_id}", response_model=Product, tags=["Products"])
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    """
    Get a specific product by its ID. Department information is joined automatically.
    """
    # UPDATED QUERY: Use `options(joinedload(...))` for an efficient Eager Load JOIN.
    db_product = db.query(ProductModel).options(
        joinedload(ProductModel.department)
    ).filter(ProductModel.id == product_id).first()
    
    if db_product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product