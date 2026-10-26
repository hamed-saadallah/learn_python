from typing import Dict, Any
from mistralai.client import MistralClient
from mistralai.models.chat_message import ChatMessage
from utils.logger import setup_logger, log_execution
from config import settings

logger = setup_logger(__name__)


class RouterAgent:
    """Agent responsible for routing queries to RAG or LLM based on query analysis."""

    def __init__(self):
        """Initialize the router agent with Mistral client."""
        try:
            self.client = MistralClient(api_key=settings.mistral_api_key)
            self.model = settings.mistral_model
            logger.info("Initialized RouterAgent")
        except Exception as e:
            logger.error(f"Failed to initialize RouterAgent: {str(e)}", exc_info=True)
            raise

    @log_execution(logger)
    def decide(self, query: str) -> Dict[str, Any]:
        """
        Analyze a query and decide if it requires RAG or can be answered from LLM knowledge.
        
        Returns:
            Dict with 'use_rag' (bool) and 'reasoning' (str)
        """
        try:
            system_prompt = """You are a query router. Analyze the user's query and decide if it requires 
external knowledge lookup (RAG) or if it can be answered from general LLM knowledge.

Respond with a JSON object containing:
- "use_rag": boolean (true if external knowledge needed, false for general knowledge)
- "reasoning": string (brief explanation of your decision)

Use RAG when:
- Query asks about specific documents, articles, or reference materials
- Query requires domain-specific information not in general training data
- Query asks about recent events or specific facts

Use LLM knowledge when:
- Query is about general concepts, definitions, or explanations
- Query asks for advice, brainstorming, or creative content
- Query is answerable from common knowledge"""

            messages = [
                ChatMessage(role="system", content=system_prompt),
                ChatMessage(role="user", content=f"Query: {query}"),
            ]

            response = self.client.chat(
                model=self.model,
                messages=messages,
                temperature=settings.mistral_temperature,
                max_tokens=256,
            )

            response_text = response.choices[0].message.content

            import json

            try:
                decision = json.loads(response_text)
                use_rag = decision.get("use_rag", False)
                reasoning = decision.get("reasoning", "No reasoning provided")
            except json.JSONDecodeError:
                logger.warning(
                    "Failed to parse router response as JSON, defaulting to RAG",
                    extra={"extra_data": {"response": response_text}},
                )
                use_rag = True
                reasoning = "JSON parsing failed, defaulting to RAG"

            logger.info(
                f"Router decision: use_rag={use_rag}",
                extra={
                    "extra_data": {
                        "query": query[:100],
                        "use_rag": use_rag,
                        "reasoning": reasoning,
                    }
                },
            )

            return {
                "use_rag": use_rag,
                "reasoning": reasoning,
                "query": query,
            }

        except Exception as e:
            logger.error(f"Error in router decision: {str(e)}", exc_info=True)
            return {
                "use_rag": False,
                "reasoning": f"Error in routing: {str(e)}",
                "query": query,
                "error": True,
            }
