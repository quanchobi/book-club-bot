import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from datetime import datetime
from src.bookdb import Base, Books, Authors, BookAuthors, Reviews, Meetings

@pytest.fixture
def engine():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine('sqlite:///:memory:')

    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def session(engine):
    """Create a new database session for a test"""
    session = Session(engine)
    yield session
    session.close()

class TestBooks:
    def test_create_book(self, session):
        """Test creating a book"""
        book = Books(isbn=1234567890, title="Test Book")
        session.add(book)
        session.commit()
        
        retrieved = session.query(Books).filter_by(isbn=1234567890).first()
        assert retrieved is not None
        assert retrieved.title == "Test Book"
        assert retrieved.isbn == 1234567890
    
    def test_book_title_required(self, session):
        """Test that book title is required (nullable=False)"""
        book = Books(isbn=1234567890, title=None)
        session.add(book)
        
        with pytest.raises(Exception):
            session.commit()
    
    def test_book_isbn_primary_key(self, session):
        """Test that isbn is unique primary key"""
        book1 = Books(isbn=1111111111, title="Book One")
        book2 = Books(isbn=1111111111, title="Book Two")
        
        session.add(book1)
        session.commit()
        session.add(book2)
        
        with pytest.raises(Exception):
            session.commit()

class TestAuthors:
    def test_create_author(self, session):
        """Test creating an author"""
        author = Authors(name="Jane Doe")
        session.add(author)
        session.commit()
        
        retrieved = session.query(Authors).filter_by(name="Jane Doe").first()
        assert retrieved is not None
        assert retrieved.name == "Jane Doe"
        assert retrieved.id is not None
    
    def test_author_name_required(self, session):
        """Test that author name is required"""
        author = Authors(name=None)
        session.add(author)
        
        with pytest.raises(Exception):
            session.commit()

class TestBookAuthors:
    def test_link_book_and_author(self, session):
        """Test linking a book to an author"""
        book = Books(isbn=9876543210, title="Great Novel")
        author = Authors(name="John Smith")
        
        session.add(book)
        session.add(author)
        session.commit()
        
        book_author = BookAuthors(isbn=book.isbn, author_id=author.id)
        session.add(book_author)
        session.commit()
        
        retrieved = session.query(BookAuthors).filter_by(isbn=book.isbn).first()
        assert retrieved is not None
        assert retrieved.author_id == author.id
    
    def test_foreign_key_constraints(self, session):
        """Test that foreign key constraints work"""
        # Try to create BookAuthors with non-existent book
        book_author = BookAuthors(isbn=9999999999, author_id=1)
        session.add(book_author)
        
        with pytest.raises(Exception):
            session.commit()

class TestReviews:
    def test_create_review(self, session):
        """Test creating a review"""
        book = Books(isbn=5555555555, title="Review Test Book")
        session.add(book)
        session.commit()
        
        review = Reviews(
            isbn=book.isbn,
            uuid=1,
            score=85,
            review="Great book!"
        )
        session.add(review)
        session.commit()
        
        retrieved = session.query(Reviews).filter_by(isbn=book.isbn).first()
        assert retrieved is not None
        assert retrieved.score == 85
        assert retrieved.review == "Great book!"
    
    def test_review_foreign_key(self, session):
        """Test that review requires valid book isbn"""
        review = Reviews(isbn=9999999999, score=90)
        session.add(review)
        
        with pytest.raises(Exception):
            session.commit()
    
    def test_multiple_reviews_per_book(self, session):
        """Test that a book can have multiple reviews"""
        book = Books(isbn=7777777777, title="Popular Book")
        session.add(book)
        session.commit()
        
        review1 = Reviews(isbn=book.isbn, uuid=1, score=90)
        review2 = Reviews(isbn=book.isbn, uuid=2, score=75)
        
        session.add(review1)
        session.add(review2)
        session.commit()
        
        reviews = session.query(Reviews).filter_by(isbn=book.isbn).all()
        assert len(reviews) == 2
        assert reviews[0].score != reviews[1].score

class TestMeetings:
    def test_create_meeting(self, session):
        """Test creating a meeting"""
        book = Books(isbn=8888888888, title="Book Club Book")
        session.add(book)
        session.commit()
        
        meeting_time = datetime.now()
        
        meeting = Meetings(
            isbn=book.isbn,
            datetime=meeting_time,
        )
        session.add(meeting)
        session.commit()
        
        retrieved = session.query(Meetings).filter_by(isbn=book.isbn).first()
        assert retrieved is not None
        assert retrieved.datetime == meeting_time
        assert retrieved.id is not None
    
    def test_meeting_autoincrement_id(self, session):
        """Test that meeting IDs auto-increment"""
        book = Books(isbn=3333333333, title="Meeting Book")
        session.add(book)
        session.commit()
        
        meeting1 = Meetings(isbn=book.isbn, datetime=datetime.now())
        meeting2 = Meetings(isbn=book.isbn, datetime=datetime.now())
        
        session.add(meeting1)
        session.add(meeting2)
        session.commit()
        
        assert meeting1.id is not None
        assert meeting2.id is not None
        assert meeting1.id != meeting2.id

class TestRelationships:
    def test_book_with_multiple_authors(self, session):
        """Test a book with multiple authors"""
        book = Books(isbn=4444444444, title="Collaborative Work")
        author1 = Authors(name="Author One")
        author2 = Authors(name="Author Two")
        
        session.add(book)
        session.add(author1)
        session.add(author2)
        session.commit()
        
        ba1 = BookAuthors(isbn=book.isbn, author_id=author1.id)
        ba2 = BookAuthors(isbn=book.isbn, author_id=author2.id)
        
        session.add(ba1)
        session.add(ba2)
        session.commit()
        
        book_authors = session.query(BookAuthors).filter_by(isbn=book.isbn).all()
        assert len(book_authors) == 2
    
    def test_author_with_multiple_books(self, session):
        """Test an author with multiple books"""
        author = Authors(name="Prolific Writer")
        book1 = Books(isbn=1010101010, title="First Novel")
        book2 = Books(isbn=2020202020, title="Second Novel")
        
        session.add(author)
        session.add(book1)
        session.add(book2)
        session.commit()
        
        ba1 = BookAuthors(isbn=book1.isbn, author_id=author.id)
        ba2 = BookAuthors(isbn=book2.isbn, author_id=author.id)
        
        session.add(ba1)
        session.add(ba2)
        session.commit()
        
        author_books = session.query(BookAuthors).filter_by(author_id=author.id).all()
        assert len(author_books) == 2

class TestQueries:
    def test_filter_books_by_title(self, session):
        """Test querying books by title"""
        book1 = Books(isbn=1000000001, title="Alpha Book")
        book2 = Books(isbn=1000000002, title="Beta Book")
        book3 = Books(isbn=1000000003, title="Alpha Book Two")
        
        session.add_all([book1, book2, book3])
        session.commit()
        
        results = session.query(Books).filter(Books.title.like("Alpha%")).all()
        assert len(results) == 2
    
    def test_order_reviews_by_score(self, session):
        """Test ordering reviews by score"""
        book = Books(isbn=6666666666, title="Rated Book")
        session.add(book)
        session.commit()
        
        review1 = Reviews(isbn=book.isbn, uuid=1, score=60)
        review2 = Reviews(isbn=book.isbn, uuid=2, score=90)
        review3 = Reviews(isbn=book.isbn, uuid=3, score=75)
        
        session.add_all([review1, review2, review3])
        session.commit()
        
        top_reviews = session.query(Reviews).filter_by(isbn=book.isbn).order_by(Reviews.score.desc()).all()
        assert top_reviews[0].score == 90
        assert top_reviews[1].score == 75
        assert top_reviews[2].score == 60
