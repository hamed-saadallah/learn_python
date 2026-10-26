from typing import Dict, Any
from mistralai.client import MistralClient
from mistralai.models.chat_message import ChatMessage
from utils.logger import setup_logger, log_execution
from config import settings

logger = setup_logger(__name__)


class LLMAgent:
    """Agent responsible for generating responses using only LLM knowledge."""

    def __init__(self):
        """Initialize the LLM agent with Mistral client."""
        try:
            self.client = MistralClient(api_key=settings.mistral_api_key)
            self.model = settings.mistral_model
            logger.info("Initialized LLMAgent")
        except Exception as e:
            logger.error(f"Failed to initialize LLMAgent: {str(e)}", exc_info=True)
            raise

    @log_execution(logger)
    def generate_response(self, query: str) -> Dict[str, Any]:
        """
        Generate a response using only the LLM's knowledge.
        
        Args:
            query: The user's query
            
        Returns:
            Dict with 'response' and metadata
        """
        try:
            system_prompt = """You are a helpful and knowledgeable assistant. 
Answer questions based on your training knowledge.
If you're unsure about something, acknowledge the limitation."""

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=query),
            ]

            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=settings.mistral_temperature,
                max_tokens=settings.mistral_max_tokens,
            )

            response_text = response.choices[0].message.content

            logger.info(
                "Generated LLM response",
                extra={
                    "extra_data": {
                        "query": query[:100],
                        "response_length": len(response_text),
                    }
                },
            )

            return {
                "response": response_text,
                "sources": [],
                "is_from_llm_knowledge": True,
            }

        except Exception as e:
            logger.error(f"Error generating LLM response: {str(e)}", exc_info=True)
            return {
                "response": f"Error generating response: {str(e)}",
                "sources": [],
                "error": True,
            }

    @log_execution(logger)
    def process(self, query: str) -> Dict[str, Any]:
        """
        Process a query using only LLM knowledge.
        
        Args:
            query: The query to process
            
        Returns:
            Dict with response and metadata
        """
        try:
            result = self.generate_response(query)
            return result

        except Exception as e:
            logger.error(f"Error in LLM process: {str(e)}", exc_info=True)
            return {
                "response": f"Error processing query: {str(e)}",
                "sources": [],
                "error": True,
            }
