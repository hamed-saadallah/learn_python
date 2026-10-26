import weaviate
from typing import List, Dict, Any, Optional
from utils.logger import setup_logger, log_execution
from config import settings

logger = setup_logger(__name__)


class WeaviateClient:
    """Client for interacting with Weaviate vector database."""

    def __init__(self):
        """Initialize Weaviate client connection."""
        try:
            self.client = weaviate.Client(url=settings.weaviate_url)
            logger.info(
                "Connected to Weaviate",
                extra={"extra_data": {"url": settings.weaviate_url}},
            )
        except Exception as e:
            logger.error(
                f"Failed to connect to Weaviate: {str(e)}",
                exc_info=True,
            )
            raise

    @log_execution(logger)
    def create_class(self, class_name: str, properties: List[Dict[str, Any]]) -> None:
        """Create a new class in Weaviate."""
        try:
            class_obj = {
                "class": class_name,
                "properties": properties,
                "vectorizer": "text2vec-huggingface",
            }
            self.client.schema.create_class(class_obj)
            logger.info(
                f"Created class {class_name}",
                extra={"extra_data": {"class_name": class_name}},
            )
        except Exception as e:
            if "already exists" in str(e):
                logger.info(
                    f"Class {class_name} already exists",
                    extra={"extra_data": {"class_name": class_name}},
                )
            else:
                logger.error(f"Error creating class: {str(e)}", exc_info=True)
                raise

    @log_execution(logger)
    def add_document(
        self, class_name: str, document: Dict[str, Any], doc_id: Optional[str] = None
    ) -> str:
        """Add a document to Weaviate."""
        try:
            result = self.client.data_object.create(
                data_object=document,
                class_name=class_name,
                uuid=doc_id,
            )
            logger.info(
                f"Added document to {class_name}",
                extra={"extra_data": {"class_name": class_name, "doc_id": result}},
            )
            return result
        except Exception as e:
            logger.error(f"Error adding document: {str(e)}", exc_info=True)
            raise

    @log_execution(logger)
    def search(
        self,
        class_name: str,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for documents using vector similarity."""
        try:
            where_filter = where if where else {}

            result = self.client.query.get(
                class_name, ["content", "title", "source", "_additional {distance}"]
            ).with_near_text({"concepts": [query]}).with_limit(top_k)

            if where_filter:
                result = result.with_where(where_filter)

            response = result.do()

            documents = []
            if "data" in response and "Get" in response["data"]:
                documents = response["data"]["Get"].get(class_name, [])

            logger.info(
                f"Found {len(documents)} documents",
                extra={
                    "extra_data": {
                        "class_name": class_name,
                        "query": query,
                        "results_count": len(documents),
                    }
                },
            )
            return documents

        except Exception as e:
            logger.error(f"Error searching documents: {str(e)}", exc_info=True)
            raise

    @log_execution(logger)
    def delete_class(self, class_name: str) -> None:
        """Delete a class from Weaviate."""
        try:
            self.client.schema.delete_class(class_name)
            logger.info(
                f"Deleted class {class_name}",
                extra={"extra_data": {"class_name": class_name}},
            )
        except Exception as e:
            logger.error(f"Error deleting class: {str(e)}", exc_info=True)
            raise

    @log_execution(logger)
    def get_all_documents(self, class_name: str) -> List[Dict[str, Any]]:
        """Get all documents from a class."""
        try:
            result = self.client.query.get(
                class_name, ["content", "title", "source"]
            ).with_limit(1000).do()

            documents = []
            if "data" in result and "Get" in result["data"]:
                documents = result["data"]["Get"].get(class_name, [])

            logger.info(
                f"Retrieved {len(documents)} documents from {class_name}",
                extra={
                    "extra_data": {
                        "class_name": class_name,
                        "count": len(documents),
                    }
                },
            )
            return documents

        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}", exc_info=True)
            raise

    @log_execution(logger)
    def health_check(self) -> bool:
        """Check if Weaviate is healthy."""
        try:
            result = self.client.is_ready()
            logger.info(
                f"Weaviate health check: {result}",
                extra={"extra_data": {"healthy": result}},
            )
            return result
        except Exception as e:
            logger.error(f"Health check failed: {str(e)}", exc_info=True)
            return False
