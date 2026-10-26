from typing import Dict, Any, List
from mistralai.client import MistralClient
from mistralai.models.chat_message import ChatMessage
from utils.logger import setup_logger, log_execution
from services.weaviate_client import WeaviateClient
from config import settings

logger = setup_logger(__name__)


class RAGAgent:
    """Agent responsible for retrieving documents and augmenting responses with external knowledge."""

    def __init__(self):
        """Initialize the RAG agent with Mistral client and Weaviate connection."""
        try:
            self.client = MistralClient(api_key=settings.mistral_api_key)
            self.model = settings.mistral_model
            self.weaviate = WeaviateClient()
            logger.info("Initialized RAGAgent")
        except Exception as e:
            logger.error(f"Failed to initialize RAGAgent: {str(e)}", exc_info=True)
            raise

    @log_execution(logger)
    def retrieve_documents(self, query: str, top_k: int = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents from Weaviate based on the query.
        
        Args:
            query: The search query
            top_k: Number of documents to retrieve
            
        Returns:
            List of relevant documents
        """
        if top_k is None:
            top_k = settings.rag_top_k

        try:
            documents = self.weaviate.search(
                class_name="Document",
                query=query,
                top_k=top_k,
            )

            logger.info(
                f"Retrieved {len(documents)} documents for query",
                extra={
                    "extra_data": {
                        "query": query[:100],
                        "document_count": len(documents),
                    }
                },
            )

            return documents

        except Exception as e:
            logger.error(f"Error retrieving documents: {str(e)}", exc_info=True)
            return []

    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        """Format retrieved documents into context string."""
        if not documents:
            return "No relevant documents found."

        context_parts = ["Retrieved documents:"]
        for idx, doc in enumerate(documents, 1):
            title = doc.get("title", "Untitled")
            content = doc.get("content", "")
            source = doc.get("source", "unknown")
            distance = doc.get("_additional", {}).get("distance", "N/A")

            context_parts.append(
                f"\n[Document {idx}] Title: {title}\nSource: {source}\nContent: {content[:500]}..."
            )

        return "\n".join(context_parts)

    @log_execution(logger)
    def generate_response(self, query: str, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate a response augmented with retrieved documents.
        
        Args:
            query: The original query
            documents: Retrieved documents
            
        Returns:
            Dict with 'response' and 'sources'
        """
        try:
            context = self._format_context(documents)

            system_prompt = """You are a helpful assistant that answers questions based on provided documents.
Always cite the sources of your information from the retrieved documents.
If the documents don't contain relevant information, say so explicitly."""

            user_message = f"""Based on the following documents, please answer the user's query.

{context}

User Query: {query}

Provide a comprehensive answer using the information from the documents."""

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=user_message),
            ]

            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=settings.mistral_temperature,
                max_tokens=settings.mistral_max_tokens,
            )

            response_text = response.choices[0].message.content

            sources = [doc.get("title", "Unknown") for doc in documents]

            logger.info(
                "Generated RAG response",
                extra={
                    "extra_data": {
                        "query": query[:100],
                        "document_count": len(documents),
                        "response_length": len(response_text),
                    }
                },
            )

            return {
                "response": response_text,
                "sources": sources,
                "document_count": len(documents),
            }

        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}", exc_info=True)
            return {
                "response": f"Error generating response: {str(e)}",
                "sources": [],
                "error": True,
            }

    @log_execution(logger)
    def process(self, query: str, top_k: int = None) -> Dict[str, Any]:
        """
        Process a query end-to-end: retrieve documents and generate response.
        
        Args:
            query: The query to process
            top_k: Number of documents to retrieve
            
        Returns:
            Dict with response and metadata
        """
        try:
            documents = self.retrieve_documents(query, top_k)
            result = self.generate_response(query, documents)
            return result

        except Exception as e:
            logger.error(f"Error in RAG process: {str(e)}", exc_info=True)
            return {
                "response": f"Error processing query: {str(e)}",
                "sources": [],
                "error": True,
            }
