import discord
from discord.ext import commands

import requests

import logging
import os
from dotenv import load_dotenv

from bookdb import Book, Authors, BookAuthors, Reviews, Meetings, Base, get_session

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot = commands.Bot(command_prefix="/")

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
async def rate_book(ctx, book, score):
    """
    rate the specified book, with the specified score, for a given user.
    """
    with get_session() as session:
        pass

@bot.command()
async def add_book(ctx, isbn):
    """
    find the book from the google books api, add it to local database.
    """
    book = session=query(Book).filter_by(isbn=isbn).first()
    if book:
        await ctx.send(f"Book {book.title} already exists in database")
    else:
        with get_session() as session:
            book = Book(isbn=isbn, title="TODO: query title from google books", score=0)
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
    either shows the schedule of upcoming meetings, or create/remove/reschedule meetings, depending on the arguments provided
    """
    with get_session() as session:
        pass

def search_by_title(title):
    base_url = "https://googleapis.com/books/v1/volumes"

    params = {
        'q': f'intitle:{title}'
            'maxResults': 1
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()

        if data.get('totalItems', 0) > 0:
            item = data['items'][0]
            volume_info = item['volumeInfo']

            book_title = volume_info.get('title')
            authors = volume_info.get('authors', ['N/A'])
            isbn = volume_info.get('isbn')

            return book_title, authors, isbn

def search_by_isbn(isbn):
    base_url = "https://www.googleapis.com/books/v1/volumes"

    params = {
        'q': f'isbn:isbn'
    }

    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        if data.get('totalItems', 0) > 0:
            item = data['items'][0]
            volume_info = item['volumeInfo']

            book_title = volume_info.get('title')
            authors = volume_info.get('authors', ['N/A'])

            return book_title, authors, isbn

