from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# SQLALCHEMY_DATABASE_URL = "postgresql://customeruser:password@localhost/customerdb"
# SQLALCHEMY_DATABASE_URL = "postgresql://customeruser:password@host.docker.internal:5432/customerdb"
# SQLALCHEMY_DATABASE_URL = "postgresql://customeruser:password@postgres:5432/customerdb"
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://customeruser:password@postgres:5432/customerdb")


engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
