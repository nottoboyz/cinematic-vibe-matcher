from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

load_dotenv()

def get_engine():
    """
    สร้าง SQLAlchemy engine สำหรับเชื่อมต่อ PostgreSQL
    
    ทำไมใช้ SQLAlchemy แทน psycopg2 ตรงๆ?
    → SQLAlchemy จัดการ connection pool ให้อัตโนมัติ
    → pandas มี .to_sql() ที่รับ engine ได้เลย
    → เขียน SQL หรือ Python ORM ก็ได้
    """
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")

    # connection string format:
    # postgresql://user:password@host:port/dbname
    url = f"postgresql://{user}:{password}@{host}:{port}/{name}"

    engine = create_engine(url)
    return engine


def test_connection():
    """ทดสอบว่าเชื่อมต่อ DB ได้จริง"""
    engine = get_engine()

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        version = result.fetchone()[0]
        print(f"✅ เชื่อมต่อสำเร็จ!")
        print(f"PostgreSQL: {version}")


if __name__ == "__main__":
    test_connection()