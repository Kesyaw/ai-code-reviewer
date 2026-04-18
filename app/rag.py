from sentence_transformers import SentenceTransformer
from sqlalchemy import Column, Integer, String, Text, text
from pgvector.sqlalchemy import Vector
from app.database import Base, SessionLocal, engine
import numpy as np

model = SentenceTransformer('all-MiniLM-L6-v2')

class CodeEmbedding(Base):
    __tablename__ = "code_embeddings"
    
    id = Column(Integer, primary_key=True)
    pr_number = Column(Integer)
    pr_title = Column(String(500))
    code_chunk = Column(Text)
    review_summary = Column(Text)
    embedding = Column(Vector(384))

def init_rag():
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    Base.metadata.create_all(bind=engine)

def save_embedding(pr_number, pr_title, code_chunk, review_summary):
    embedding = model.encode(code_chunk).tolist()
    db = SessionLocal()
    try:
        record = CodeEmbedding(
            pr_number=pr_number,
            pr_title=pr_title,
            code_chunk=code_chunk,
            review_summary=review_summary,
            embedding=embedding
        )
        db.add(record)
        db.commit()
        print("✅ Embedding tersimpan")
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

def find_similar_code(code_chunk, top_k=3):
    embedding = model.encode(code_chunk).tolist()
    db = SessionLocal()
    try:
        results = db.execute(
            text("""SELECT pr_title, code_chunk, review_summary,
               embedding <=> :emb AS distance
               FROM code_embeddings
               ORDER BY distance LIMIT :k"""),
            {"emb": str(embedding), "k": top_k}
        ).fetchall()
        return results
    except Exception as e:
        print(f"Error: {e}")
        return []
    finally:
        db.close()