#!/usr/bin/env python
"""
Main entry point for the RAG application.

This script initializes the Weaviate database with sample data and starts the API server.
"""

import sys
import argparse
from utils.logger import setup_logger
from services.weaviate_client import WeaviateClient
from services.sample_data import populate_sample_data
from config import settings

logger = setup_logger(__name__)


def init_database():
    """Initialize Weaviate with sample data."""
    logger.info("Initializing Weaviate database...")

    try:
        client = WeaviateClient()

        if not client.health_check():
            logger.error("Weaviate is not healthy. Make sure it's running.")
            return False

        logger.info("Weaviate health check passed")

        populate_sample_data(client)
        logger.info("Database initialization completed successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
        return False


def start_api():
    """Start the FastAPI server."""
    logger.info(
        f"Starting API server on {settings.api_host}:{settings.api_port}...",
        extra={
            "extra_data": {
                "host": settings.api_host,
                "port": settings.api_port,
            }
        },
    )

    try:
        import uvicorn

        uvicorn.run(
            "api:app",
            host=settings.api_host,
            port=settings.api_port,
            reload=False,
            log_config=None,
        )

    except Exception as e:
        logger.error(f"Failed to start API server: {str(e)}", exc_info=True)
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="RAG Application with LangGraph and Mistral AI"
    )
    parser.add_argument(
        "--init-db",
        action="store_true",
        help="Initialize Weaviate with sample data",
    )
    parser.add_argument(
        "--start-api",
        action="store_true",
        help="Start the API server",
    )
    parser.add_argument(
        "--dev",
        action="store_true",
        help="Run in development mode (init DB + start API)",
    )

    args = parser.parse_args()

    logger.info("RAG Application starting...")

    if args.dev:
        args.init_db = True
        args.start_api = True

    if args.init_db:
        success = init_database()
        if not success and args.start_api:
            logger.warning("Database initialization failed, but continuing...")

    if args.start_api:
        start_api()
    elif not args.init_db:
        parser.print_help()


if __name__ == "__main__":
    main()
