#!/usr/bin/env python
"""
Script to populate Weaviate with sample data.

Usage:
    python populate_data.py
"""

from services.weaviate_client import WeaviateClient
from services.sample_data import populate_sample_data
from utils.logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Populate Weaviate with sample documents."""
    logger.info("Starting data population...")

    try:
        client = WeaviateClient()

        if not client.health_check():
            logger.error("Weaviate is not healthy. Make sure it's running.")
            logger.error(
                "Start Weaviate with: docker run -p 8080:8080 semitechnologies/weaviate:latest"
            )
            return False

        logger.info("Weaviate health check passed")

        populate_sample_data(client)
        logger.info("Data population completed successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to populate data: {str(e)}", exc_info=True)
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
