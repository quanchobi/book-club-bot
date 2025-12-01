"""Discord book club bot database"""
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, event
from sqlalchemy.orm import Session, declarative_base

Base = declarative_base()

class Books(Base):
    """Table that contains book ISBNs and titles"""
    __tablename__ = "Books"

    isbn = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    score = Column(Integer)


class Authors(Base):
    """Table that contains author names and IDs"""
    __tablename__ = "Authors"

    open_library_id = Column(String, primary_key=True)
    name = Column(String, nullable = False)


class BookAuthors(Base):
    """Bridge table that can map multiple books to multiple authors"""
    __tablename__ = "BookAuthors"
    
    isbn = Column(Integer, ForeignKey("Books.isbn"), primary_key=True)
    author_id = Column(Integer, ForeignKey("Authors.id"), primary_key=True)


class Reviews(Base):
    """Table that stores user reviews of a book"""
    __tablename__ = "Reviews"

    isbn = Column(String, ForeignKey("Books.isbn"), primary_key=True)
    user_id = Column(String, primary_key=True)
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
    sqlengine = create_engine('sqlite:///bookbot.db')

    @event.listens_for(sqlengine, "connect")
    def set_sqlite_pragma(dbapi_conn):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(sqlengine)
    return sqlengine

@contextmanager
def get_session():
    """Get the SQLite session"""
    session = Session(engine)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()
