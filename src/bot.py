import discord
from discord.ext import commands

import logging
import os
from dotenv import load_dotenv

from bookdb import Book, Authors, BookAuthors, Reviews, Meetings, Base, engine
from contextlib import contextmanager
from sqlalchemy.orm import Session

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

bot = commands.Bot(command_prefix="/")

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

@bot.command()
async def list_books(ctx, sort):
    """
    show a list of books in the database, sortable by score, alphabetical, date read, etc.
    """
    pass

@bot.command()
async def rate_book(ctx, book, score):
    """
    rate the specified book, with the specified score, for a given user.
    """
    pass

@bot.command()
async def add_book(ctx, isbn):
    """
    find the book from the google books api, add it to local database.
    """
    pass

@bot.command()
async def remove_book(ctx, isbn):
    """
    remove the specified book from the local database.
    """
    pass

@bot.command()
async def schedule(ctx, *args):
    """
    either shows the schedule of upcoming meetings, or create/remove/reschedule meetings, depending on the arguments provided
    """
    pass
