"""
Bot commands.
"""
import logging
import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

import requests


from dataclasses import dataclass, field
from bookdb import Books, Authors, BookAuthors, Reviews, Meetings, get_session
from sqlalchemy import func

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix="/", intents=intents)

@dataclass
class BookSearchResult:
    title: str
    olid: str
    author_olids: list[str] = field(default_factory=list)

@bot.command
async def list_books(ctx, sort: str="", limit: int=5) -> None:
    """
    show a list of books in the database, sortable by score, alphabetical, date read, etc.
    """
    with get_session() as session:
        match sort:
            case "score":
                avg_score = func.avg(Reviews.score).label('avg_score')

                results = (
                    session.query(avg_score, Books.title)
                    .join(Books, Reviews.olid == Books.olid)
                    .group_by(Reviews.olid, Books.title)
                    .order_by(avg_score.desc())
                    .limit(limit)
                    .all()
                )
                    
            case "recent":
                first_meeting_date = func.min(Meetings.datetime).label('first_meeting_date')

                results = (
                    session.query(Reviews.score, Books.title)
                    .join(Books, Reviews.isbn == Books.isbn)
                    .join(Meetings, Reviews.isbn == Meetings.isbn)
                    .group_by(Meetings.isbn, Books.title)
                    .order_by(first_meeting_date.desc())
                    .limit(limit)
                    .all()
                )

            # default to alphabetical search
            case _:
                results = (
                    session.query(Reviews.score, Books.title)
                    .join(Books, Reviews.isbn == Books.isbn)
                    .group_by(Reviews.isbn == Books.isbn)
                    .order_by(Books.title.desc())
                    .limit(limit)
                    .all()
                )

        table = ""
        for score, title in results:
            table += f"{title}: {score}\n"

        await ctx.send(table)


@bot.command
async def rate_book(ctx, score: float, olid: str|None=None, title: str|None=None, review: str|None=None) -> None:
    """
    rate the specified book, with the specified score, for the user who prompted the bot.
    """
    user_id = ctx.message.author.id
    with get_session() as session:
        # Try and find the book via title
        if olid:
            book = session.query(Books).filter_by(olid=olid).first()
        else:
            book = session.query(Books).filter_by(title=title).first()

        if not book: # book not found, query google books api for an isbn
            matches = search_books(title)
            # TODO: ask the user which of the 5 books it is, instead of assuming it is the first book
            book = matches[0]

        if not book:
            await ctx.send(f"Book {title} not found!")
            return

        review = Reviews(
            olid=book.olid,
            user_id=user_id,
            score=score,
            review=review
        )

        session.add(review)
        session.commit()
    await ctx.send("Review added!")


@bot.command
async def add_book(ctx, olid: str|None=None, isbn: str|None=None, title: str|None=None) -> None:
    """
    find the book from the google books api, add it to local database.
    """
    if isbn is None and title is None:
        await ctx.send("Must supply isbn or title")
        return

    with get_session() as session:
        book = session.query(Books).filter_by(isbn=isbn).first()
        if book:
            await ctx.send(f"Book {book.title} already exists in database")
            return

        # prefer specifier search
        if olid or isbn: 
            book = grab_book(olid, isbn)
            if not book:
                await ctx.send(f"Invalid OLID and ISBN")
                return
        # otherwise search by title and present a list of books to choose from
        else:
            book_list = search_books()
            # TODO: have user select from the list instead of assuming the first book is correct.
            book = book_list[0]
            if not book:
                await ctx.send(f"Book {book.title} not found")
        author_olids = book.author_olids

        new_book = Books(isbn=isbn, title=title)

        for author_olid in author_olids:
            bridge = BookAuthors(book_olid=new_book.olid, author_olid=author_olid)
            session.add(bridge)

        session.add(new_book)
        await ctx.send(f"Added book {title}")


@bot.command
async def remove_book(ctx, olid:str) -> None:
    """
    remove the specified book from the local database.
    """
    with get_session() as session:
        pass

@bot.command
async def schedule(ctx, *args) -> None:
    """
    either shows the schedule of upcoming meetings, 
    or create/remove/reschedule meetings, depending on the arguments 
    provided.
    """
    with get_session() as session:
        pass


def search_books(title: str|None=None, author_name: str|None=None, limit: int=5) -> list[BookSearchResult]:
    """ Takes a book's title and/or author_olid, and returns a list of `limit` matching books """

    if not title and not author_name:
        return []

    base_url = "https://openlibrary.org/search.json"

    params: dict[str, int|str] = {'limit': limit}
    if title:
        params['title'] = title
    if author_name:
        params['author'] = author_name

    try:
        response = requests.get(base_url, params=params)
        data = response.json()
    except requests.RequestException as e:
        print(f"API Error: {e}")
        return []
    
    books_list = []
    for doc in data.get('docs', []):
        path = doc.get('key')
        book_olid = path.split("/")[-1] if path else "Unkown OLID"
        authors = doc.get('authors', [])
        author_olids = []

        for author in authors:
            author_key = author.get('key')
            author_olid = author_key.split("/")[-1] if author_key else "Unkown Author"
            author_olids.append(author_olid)

        books_list.append(BookSearchResult(
            title=doc.get('title', 'Unknown Title'),
            olid=book_olid,
            author_olids=author_olids,
        ))

    return books_list


def grab_book(olid: str|None=None, isbn: str|None=None) -> BookSearchResult|None:
    """ Takes a specifier (olid, and an isbn13 or isbn10), and returns the associated book """

    if olid is None and isbn is None:
        return None

    if olid is not None: # prefer grab by olid 
        base_url = f"https://openlibrary.org/books/{olid}.json"
    else: # fallback grab by isbn
        base_url = f"https://openlibrary.org/isbn/{isbn}.json"

    try:
        response = requests.get(base_url)
        data = response.json()
    except requests.RequestException as e:
        print(f"API Error: {e}")
        return None

    data = response.json()

    title = data.get('title')

    book_key = data.get('key')
    found_olid = book_key.split("/")[-1]

    authors = data.get('authors', [])
    author_olids = []
    for author in authors:
        author_key = author.get('key', '')
        author_olid = author_key.split("/")[-1]
        author_olids.append(author_olid)

    return BookSearchResult(
        title=title, 
        olid=found_olid, 
        author_olids=author_olids
    )


def grab_author(olid: str) -> str|None:
    """ Takes an author-specific OpenLibrary ID and returns the author's name."""
    base_url = f"https://openlibrary.org/authors/{olid}.json"

    try:
        response = requests.get(base_url)
        data = response.json()
    except requests.RequestException as e:
        print(f"API Error: {e}")
        return None

    data = response.json()
    return data.get('name', 'Unknown Author')
    
