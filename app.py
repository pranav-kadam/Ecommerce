# app.py

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, Numeric
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel
from typing import List
import os
# --- 1. Database Configuration ---

# IMPORTANT: Replace with your actual database credentials.
# Use your password if you have one, or leave it empty if not.
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


# --- 2. SQLAlchemy ORM Model (Represents the 'products' table) ---

class ProductModel(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    cost = Column(Numeric(10, 5))
    category = Column(String, index=True)
    name = Column(String, index=True)
    brand = Column(String)
    retail_price = Column(Numeric(10, 2))
    department = Column(String, index=True)
    sku = Column(String, unique=True, index=True)
    distribution_center_id = Column(Integer)


# --- 3. Pydantic Model (Defines the shape of the API response) ---

class Product(BaseModel):
    id: int
    cost: float
    category: str
    name: str
    brand: str
    retail_price: float
    department: str
    sku: str
    distribution_center_id: int

    # This allows the model to be created from an ORM object
    class Config:
        from_attributes = True


# --- 4. FastAPI App Initialization & CORS ---

app = FastAPI(
    title="Products API",
    description="A RESTful API for reading product data.",
    version="1.0.0"
)

# Add CORS middleware to allow cross-origin requests (e.g., from a frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


# --- 5. Dependency for Database Session ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 6. API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Welcome to the Products API. Go to /docs for documentation."}


@app.get("/api/products", response_model=List[Product], tags=["Products"])
def get_all_products(skip: int = 0, limit: int = 25, db: Session = Depends(get_db)):
    """
    List all products with pagination.
    - **skip**: Number of records to skip for pagination.
    - **limit**: Maximum number of records to return.
    """
    products = db.query(ProductModel).offset(skip).limit(limit).all()
    return products


@app.get("/api/products/{product_id}", response_model=Product, tags=["Products"])
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    """
    Get a specific product by its ID.
    """
    db_product = db.query(ProductModel).filter(ProductModel.id == product_id).first()
    if db_product is None:
        # Returns a 404 Not Found error if the ID does not exist
        raise HTTPException(status_code=404, detail="Product not found")
    return db_product