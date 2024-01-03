import os
from sqlmodel import SQLModel, Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv


load_dotenv()

# SECRET_KEY = "49965ba36dd915c9f80ed23e1c111190b8bf9c7c33ffe895f1a68bbcd019e566"
# REFRESH_SECRET_KEY = "09475a6fdef6a1273a3d85b275df9e62eb7a2811f70e4b97e96b113266e743d6"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 1
# REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7
# DB_CONFIG = 'postgresql://postgres:041101@localhost:5432/sharecv'
# engine = create_engine(DB_CONFIG)
DATABASE_URL = os.environ.get("DATABASE_URL")


class DatabaseSession:

    def __init__(self) -> None:
        self.session = None
        self.engine = None

    def init(self):
        self.engine = create_engine(DATABASE_URL, echo=True)
        
    def create_all(self):
        SQLModel.metadata.create_all(self.engine)

    def get_session(self):
        with Session(self.engine) as session:
            yield session

db = DatabaseSession()

def commit_rollback(session: Session):
    try:
        session.commit()
    except Exception:
        session.rollback()
        raise
