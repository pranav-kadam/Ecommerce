import pandas as pd
from sqlalchemy import create_engine
import os


DB_USER = os.getenv("PG_USER", "postgres")
DB_PASSWORD = os.getenv("PG_PASSWORD") # The script will fail if this isn't set
DB_HOST = os.getenv("PG_HOST", "localhost")
DB_PORT = os.getenv("PG_PORT", "5432")
DB_NAME = os.getenv("PG_DBNAME", "ecommerce")


TABLE_NAME = "products"
CSV_FILE_PATH = "products.csv"


db_url = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Create a database engine
engine = create_engine(db_url)

# Read the CSV file into a pandas DataFrame
try:
    df = pd.read_csv(CSV_FILE_PATH)
    print(f"Successfully read {len(df)} rows from {CSV_FILE_PATH}")

    # Load the data into the database
    # 'if_exists="append"' adds data without dropping the table
    # 'index=False' prevents pandas from writing the DataFrame index as a column
    df.to_sql(TABLE_NAME, engine, if_exists='append', index=False)
    
    print(f"Successfully loaded data into the '{TABLE_NAME}' table.")

except FileNotFoundError:
    print(f"Error: The file {CSV_FILE_PATH} was not found.")
except Exception as e:
    print(f"An error occurred: {e}")