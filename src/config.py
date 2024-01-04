import os
from sqlmodel import SQLModel, Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from dotenv import load_dotenv


ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 1
REFRESH_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7

load_dotenv()
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

    def commit_rollback(self, session: Session):
        try:
            session.commit()
        except Exception as e:
            session.rollback()
            raise e

db = DatabaseSession()
