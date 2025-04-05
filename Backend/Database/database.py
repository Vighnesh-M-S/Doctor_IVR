from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv() 

dburl = os.getenv("DATABASE_URL")

DATABASE_URL = dburl

async_engine = create_async_engine(DATABASE_URL, echo=True)
async_sessionmaker = async_sessionmaker(bind=async_engine, expire_on_commit=False)