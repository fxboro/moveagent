import os
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv

load_dotenv(Path(__file__).with_name('.env'))
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///' + str(Path(__file__).with_name('premium_consultancy.db')))
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False, 'timeout': 20})
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)

@event.listens_for(engine, 'connect')
def configure_sqlite(dbapi_connection, _):
    dbapi_connection.execute('PRAGMA foreign_keys=ON')
    dbapi_connection.execute('PRAGMA journal_mode=WAL')

class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        yield db
