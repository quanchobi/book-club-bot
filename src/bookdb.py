"""Discord book club bot database"""
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, event
from sqlalchemy.orm import Session, declarative_base

Base = declarative_base()

class Books(Base):
    """Table that contains book ISBNs and titles"""
    __tablename__ = "Books"

    olid = Column(String, primary_key=True)
    title = Column(String, nullable=False)


class Authors(Base):
    """Table that contains author names and IDs"""
    __tablename__ = "Authors"

    olid = Column(String, primary_key=True)
    name = Column(String, nullable = False)


class BookAuthors(Base):
    """Bridge table that can map multiple books to multiple authors"""
    __tablename__ = "BookAuthors"
    
    book_olid = Column(Integer, ForeignKey("Books.olid"), primary_key=True)
    author_olid = Column(Integer, ForeignKey("Authors.olid"), primary_key=True)


class Reviews(Base):
    """Table that stores user reviews of a book"""
    __tablename__ = "Reviews"

    olid = Column(String, ForeignKey("Books.olid"), primary_key=True)
    user_id = Column(String, primary_key=True)
    score = Column(Integer, nullable=False)
    review = Column(String)


class Meetings(Base):
    """Table that stores date, time, and book of meeting"""
    __tablename__ = "Meetings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    olid = Column(Integer, ForeignKey("Books.olid"))
    datetime = Column(DateTime(timezone=True), nullable=False)
    details = Column(String)

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
