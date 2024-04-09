import os
import dotenv
from sqlalchemy import create_engine

def database_connection_url():
    dotenv.load_dotenv()

    url = os.environ.get("POSTGRES_URI")
    if url is None:
        raise ValueError("POSTGRES_URI environment variable is not set")
    return url

engine = create_engine(database_connection_url(), pool_pre_ping=True)