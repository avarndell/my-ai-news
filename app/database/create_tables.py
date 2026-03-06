"""Run this script to drop and recreate all database tables."""
import logging
import sys
from pathlib import Path

# python has issues with relative imports in scripts, so we add the project root to the path to allow absolute imports to work
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.database.connection import engine
from app.database.models import Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logger.info("Creating tables...")
    Base.metadata.create_all(engine)
    logger.info("Done — tables created: %s", list(Base.metadata.tables.keys()))
