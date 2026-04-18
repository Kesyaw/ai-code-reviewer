from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ReviewHistory(Base):
    __tablename__ = "review_history"
    
    id = Column(Integer, primary_key=True, index=True)
    repo_name = Column(String(255))
    pr_number = Column(Integer)
    pr_title = Column(String(500))
    review_result = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def save_review(repo_name, pr_number, pr_title, review_result):
    db = SessionLocal()
    try:
        review = ReviewHistory(
            repo_name=repo_name,
            pr_number=pr_number,
            pr_title=pr_title,
            review_result=review_result
        )
        db.add(review)
        db.commit()
        print(f"✅ Review tersimpan ke database")
    except Exception as e:
        print(f"❌ Gagal simpan ke database: {e}")
        db.rollback()
    finally:
        db.close()