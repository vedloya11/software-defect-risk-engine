import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Default to SQLite file database in project root, or PostgreSQL via environment variable
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./defect_engine.db")

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    # SQLite requires disabling same-thread checking when used with multi-threaded FastAPI workers
    connect_args = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """
    FastAPI dependency that yields a database session and safely closes it upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Creates all database tables defined in models if they do not exist.
    """
    import src.database.models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    print("[OK] Database initialized successfully.")
