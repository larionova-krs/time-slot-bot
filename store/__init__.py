from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from store.models import Base
from contextlib import contextmanager

engine = create_engine("sqlite:///data.db")
Session = sessionmaker(bind=engine, expire_on_commit=False)
Base.metadata.create_all(engine)

@contextmanager
def db_session():
    session = Session()
    try:
        yield session
        session.commit()  # Commit if no errors
    except:
        session.rollback()  # Rollback on error
        raise
    finally:
        session.close()  # Always close the session
