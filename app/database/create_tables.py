"""Run this script to drop and recreate all database tables."""
import logging

from connection import engine
from models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Dropping all tables on: %s", engine.url)
    Base.metadata.drop_all(engine)
    logger.info("Recreating tables...")
    Base.metadata.create_all(engine)
    logger.info("Done — tables created: %s", list(Base.metadata.tables.keys()))
