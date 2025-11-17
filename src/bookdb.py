from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, UniqueConstraint, event
from sqlalchemy.ext.declarative import declarative_base
from contextlib import contextmanager
from sqlalchemy.orm import Session

Base = declarative_base()

class Book(Base):
    """Table that contains book ISBNs and titles"""
    __tablename__ = "Books"

    isbn = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    score = Column(Integer)


class Authors(Base):
    """Table that contains author names and IDs"""
    __tablename__ = "Authors"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable = False)


class BookAuthors(Base):
    """Bridge table that can map multiple books to multiple authors"""
    __tablename__ = "BookAuthors"
    
    isbn = Column(Integer, ForeignKey("Books.isbn"), primary_key=True)
    author_id = Column(Integer, ForeignKey("Authors.id"), primary_key=True)


class Reviews(Base):
    """Table that stores user reviews of a book"""
    __tablename__ = "Reviews"

    isbn = Column(Integer, ForeignKey("Books.isbn"), primary_key=True)
    uuid = Column(Integer, primary_key=True)
    score = Column(Integer, nullable=False)
    review = Column(String)


class Meetings(Base):
    """Table that stores date, time, and book of meeting"""
    __tablename__ = "Meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    isbn = Column(Integer, ForeignKey("Books.isbn"))
    datetime = Column(DateTime(timezone=True), nullable=False)
    notes = Column(String)

def engine():
    """Create the database"""
    engine = create_engine('sqlite:///bookbot.db')

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine

@contextmanager
def get_session():
    session = Session(engine)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
