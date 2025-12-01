"""
Bot commands.
"""
import logging
import os
from dotenv import load_dotenv

import discord
from discord.ext import commands

import requests


from bookdb import Books, Authors, BookAuthors, Reviews, Meetings, get_session

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

intents = discord.Intents.default()
intents.typing = False
intents.presences = False
bot = commands.Bot(command_prefix="/", intents=intents)

@bot.command()
async def list_books(ctx, sort):
    """
    show a list of books in the database, sortable by score, alphabetical, date read, etc.
    """
    with get_session() as session:
        match sort:
            case "score":
                pass
            case "time":
                pass
            case _:
                pass # default to alphabetical

@bot.command()
async def rate_book(ctx, title, score, review):
    """
    rate the specified book, with the specified score, for the user who prompted the bot.
    """
    user_id = ctx.message.author.id
    with get_session() as session:
        # Try and find the book via title
        book = session.query(Books).filter_by(title=title).first()

        if not book: # book not found, query google books api for an isbn
            _, _, isbn = search_by_title(title)
            book = session.query(Books).filter_by(isbn=isbn).first()
            if not book:
                await ctx.send(f"Book {title} not found!")

        review = Reviews(
            isbn=book.isbn,
            user_id=user_id,
            score=score,
            review=review
        )

        session.add(review)
        session.commit()
        await ctx.send("Review added!")


@bot.command()
async def add_book(ctx, isbn=None, title=None):
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
        if isbn is not None: # find via isbn preferred
            title, authors, isbn = search_by_isbn(isbn)
        else:
            title, authors, isbn = search_by_title(title)

        for author in authors:

        book = Books(isbn=isbn, title=title)
        bridge = BookAuthors(isbn=book.isbn, author_id=)
        session.add(book)
        await ctx.send(f"Added book {title}")



@bot.command()
async def remove_book(ctx, isbn):
    """
    remove the specified book from the local database.
    """
    with get_session() as session:
        pass

@bot.command()
async def schedule(ctx, *args):
    """
    either shows the schedule of upcoming meetings, 
    or create/remove/reschedule meetings, depending on the arguments 
    provided.
    """
    with get_session() as session:
        pass

def search_by_title(title):
    """
    Find a book via its title from the google books API
    """
    base_url = "https://www.googleapis.com/books/v1/volumes"

    params = {
        'q': f'intitle:{title}',
            'maxResults': 1
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
    except requests.exceptions.Timeout:
        return("response timed out")

    if response.status_code != 200:
        return None, None, None

    data = response.json()

    if data.get('totalItems', 0) == 0:
        return None, None, None

    item = data['items'][0]
    volume_info = item['volumeInfo']

    book_title = volume_info.get('title')
    authors = volume_info.get('authors', [])

    identifiers = volume_info.get('industryIdentifiers', [])
    isbn = None

    # prefer isbn13
    for identifier in identifiers:
        if identifier['type'] == 'ISBN_13':
            isbn = identifier['identifier']
            break
        if identifier['type'] == 'ISBN_10':
            isbn = identifier['identifier']

    return book_title, authors, isbn

def search_by_isbn(isbn):
    """
    Find a book via its isbn from the google books API
    """
    base_url = "https://www.googleapis.com/books/v1/volumes"

    params = {
        'q': f'isbn:{isbn}'
    }

    try:
        response = requests.get(base_url, params=params, timeout=10)
    except requests.exceptions.Timeout:
        return("response timed out")

    if response.status_code != 200:
        return None, None, None

    data = response.json()

    if data.get('totalItems', 0) == 0:
        return None, None, None

    item = data['items'][0]
    volume_info = item['volumeInfo']

    book_title = volume_info.get('title')
    authors = volume_info.get('authors', [])

    return book_title, authors, isbn

