from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import engine, Column, Integer, String, Numeric, ForeignKey, func
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




SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. SQLAlchemy ORM Models ---
class DepartmentModel(Base):
    __tablename__ = "departments"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, index=True)

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
    department_id = Column(Integer, ForeignKey("departments.id"))
    department = relationship("DepartmentModel")

# --- 3. Pydantic Models ---
class Department(BaseModel):
    id: int
    name: str
    class Config: from_attributes = True

class DepartmentWithCount(Department):
    product_count: int

class Product(BaseModel):
    id: int
    cost: float
    category: str
    name: str
    brand: str
    retail_price: float
    department: Department
    sku: str
    distribution_center_id: int
    class Config: from_attributes = True

# --- 4. FastAPI App Initialization ---
app = FastAPI(
    title="Products & Departments API",
    description="A RESTful API for managing products and departments.",
    version="3.0.0"
)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# --- 5. Dependency ---
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- 6. API Endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the API. Go to /docs for documentation."}

# --- Product Endpoints ---
@app.get("/api/products", response_model=List[Product], tags=["Products"])
def get_all_products(skip: int = 0, limit: int = 25, db: Session = Depends(get_db)):
    products = db.query(ProductModel).options(joinedload(ProductModel.department)).offset(skip).limit(limit).all()
    return products

@app.get("/api/products/{product_id}", response_model=Product, tags=["Products"])
def get_product_by_id(product_id: int, db: Session = Depends(get_db)):
    db_product = db.query(ProductModel).options(joinedload(ProductModel.department)).filter(ProductModel.id == product_id).first()
    if db_product is None: raise HTTPException(status_code=404, detail="Product not found")
    return db_product

# --- Department Endpoints ---
# --- Department Endpoints ---
@app.get("/api/departments", response_model=List[DepartmentWithCount], tags=["Departments"])
def get_all_departments(db: Session = Depends(get_db)):
    """
    List all departments and include a count of products in each.
    This query performs a LEFT JOIN from departments to products and then groups
    by department to count the associated products.
    """
    results = db.query(
        DepartmentModel.id,
        DepartmentModel.name,
        func.count(ProductModel.id).label("product_count")
    ).outerjoin(
        ProductModel, DepartmentModel.id == ProductModel.department_id
    ).group_by(
        DepartmentModel.id, DepartmentModel.name
    ).order_by(
        DepartmentModel.name
    ).all()

    # The query returns tuples, so we map them to our Pydantic model
    return [DepartmentWithCount(id=r.id, name=r.name, product_count=r.product_count) for r in results]


@app.get("/api/departments/{department_id}", response_model=Department, tags=["Departments"])
def get_department_by_id(department_id: int, db: Session = Depends(get_db)):
    """
    Get details for a specific department.
    """
    db_department = db.query(DepartmentModel).filter(DepartmentModel.id == department_id).first()
    if db_department is None:
        raise HTTPException(status_code=404, detail="Department not found")
    return db_department


@app.get("/api/departments/{department_id}/products", response_model=List[Product], tags=["Departments"])
def get_products_in_department(department_id: int, db: Session = Depends(get_db)):
    """
    Get a list of all products belonging to a specific department.
    """
    # First, check if the department exists
    db_department = db.query(DepartmentModel).filter(DepartmentModel.id == department_id).first()
    if db_department is None:
        raise HTTPException(status_code=404, detail="Department not found")

    # If it exists, fetch all products with the matching department_id
    # We still use joinedload here so the nested department object is included in each product
    products = db.query(ProductModel).options(
        joinedload(ProductModel.department)
    ).filter(ProductModel.department_id == department_id).all()
    
    return products