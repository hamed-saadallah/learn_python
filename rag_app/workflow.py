from typing import Dict, Any, TypedDict, Literal
from langgraph.graph import StateGraph, END
from agents.router_agent import RouterAgent
from agents.rag_agent import RAGAgent
from agents.llm_agent import LLMAgent
from utils.logger import setup_logger, log_execution

logger = setup_logger(__name__)


class WorkflowState(TypedDict):
    """State structure for the workflow."""
    query: str
    router_decision: Dict[str, Any]
    use_rag: bool
    rag_result: Dict[str, Any]
    llm_result: Dict[str, Any]
    final_response: Dict[str, Any]
    error: bool


class RAGWorkflow:
    """Orchestrates the RAG workflow using LangGraph."""

    def __init__(self):
        """Initialize the workflow with agents and build the graph."""
        try:
            self.router_agent = RouterAgent()
            self.rag_agent = RAGAgent()
            self.llm_agent = LLMAgent()

            self.graph = self._build_graph()
            logger.info("Initialized RAGWorkflow")
        except Exception as e:
            logger.error(f"Failed to initialize RAGWorkflow: {str(e)}", exc_info=True)
            raise

    @log_execution(logger)
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state graph."""
        workflow = StateGraph(WorkflowState)

        workflow.add_node("router", self._router_node)
        workflow.add_node("rag_processor", self._rag_node)
        workflow.add_node("llm_processor", self._llm_node)
        workflow.add_node("finalizer", self._finalizer_node)

        workflow.set_entry_point("router")

        workflow.add_conditional_edges(
            "router",
            self._route_decision,
            {
                "rag": "rag_processor",
                "llm": "llm_processor",
            },
        )

        workflow.add_edge("rag_processor", "finalizer")
        workflow.add_edge("llm_processor", "finalizer")
        workflow.add_edge("finalizer", END)

        return workflow.compile()

    @log_execution(logger)
    def _router_node(self, state: WorkflowState) -> WorkflowState:
        """Router node: decides whether to use RAG or LLM."""
        try:
            decision = self.router_agent.decide(state["query"])
            state["router_decision"] = decision
            state["use_rag"] = decision.get("use_rag", False)

            logger.info(
                "Router node completed",
                extra={
                    "extra_data": {
                        "query": state["query"][:100],
                        "use_rag": state["use_rag"],
                    }
                },
            )
            return state

        except Exception as e:
            logger.error(f"Error in router node: {str(e)}", exc_info=True)
            state["error"] = True
            state["use_rag"] = False
            return state

    @log_execution(logger)
    def _rag_node(self, state: WorkflowState) -> WorkflowState:
        """RAG node: processes query using external knowledge."""
        try:
            rag_result = self.rag_agent.process(state["query"])
            state["rag_result"] = rag_result

            logger.info(
                "RAG node completed",
                extra={
                    "extra_data": {
                        "query": state["query"][:100],
                        "has_error": rag_result.get("error", False),
                        "source_count": len(rag_result.get("sources", [])),
                    }
                },
            )
            return state

        except Exception as e:
            logger.error(f"Error in RAG node: {str(e)}", exc_info=True)
            state["error"] = True
            state["rag_result"] = {
                "response": f"Error processing with RAG: {str(e)}",
                "sources": [],
                "error": True,
            }
            return state

    @log_execution(logger)
    def _llm_node(self, state: WorkflowState) -> WorkflowState:
        """LLM node: processes query using LLM knowledge."""
        try:
            llm_result = self.llm_agent.process(state["query"])
            state["llm_result"] = llm_result

            logger.info(
                "LLM node completed",
                extra={
                    "extra_data": {
                        "query": state["query"][:100],
                        "has_error": llm_result.get("error", False),
                    }
                },
            )
            return state

        except Exception as e:
            logger.error(f"Error in LLM node: {str(e)}", exc_info=True)
            state["error"] = True
            state["llm_result"] = {
                "response": f"Error processing with LLM: {str(e)}",
                "sources": [],
                "error": True,
            }
            return state

    @log_execution(logger)
    def _finalizer_node(self, state: WorkflowState) -> WorkflowState:
        """Finalizer node: prepares the final response."""
        try:
            if state.get("use_rag"):
                result = state.get("rag_result", {})
                response_type = "rag"
            else:
                result = state.get("llm_result", {})
                response_type = "llm"

            state["final_response"] = {
                "response": result.get("response", "No response generated"),
                "sources": result.get("sources", []),
                "response_type": response_type,
                "error": state.get("error", False),
                "routing_decision": state.get("router_decision", {}),
            }

            logger.info(
                "Finalizer node completed",
                extra={
                    "extra_data": {
                        "response_type": response_type,
                        "has_error": state.get("error", False),
                        "source_count": len(result.get("sources", [])),
                    }
                },
            )
            return state

        except Exception as e:
            logger.error(f"Error in finalizer node: {str(e)}", exc_info=True)
            state["final_response"] = {
                "response": f"Error finalizing response: {str(e)}",
                "sources": [],
                "response_type": "error",
                "error": True,
            }
            return state

    def _route_decision(self, state: WorkflowState) -> Literal["rag", "llm"]:
        """Conditional edge: route based on router decision."""
        use_rag = state.get("use_rag", False)
        route = "rag" if use_rag else "llm"
        logger.info(
            f"Routing to {route}",
            extra={"extra_data": {"use_rag": use_rag}},
        )
        return route

    @log_execution(logger)
    def process(self, query: str) -> Dict[str, Any]:
        """
        Process a query through the entire workflow.

        Args:
            query: The user's query

        Returns:
            The final response with metadata
        """
        try:
            initial_state: WorkflowState = {
                "query": query,
                "router_decision": {},
                "use_rag": False,
                "rag_result": {},
                "llm_result": {},
                "final_response": {},
                "error": False,
            }

            final_state = self.graph.invoke(initial_state)

            logger.info(
                "Workflow execution completed",
                extra={
                    "extra_data": {
                        "query": query[:100],
                        "response_type": final_state.get("final_response", {}).get(
                            "response_type", "unknown"
                        ),
                        "has_error": final_state.get("error", False),
                    }
                },
            )

            return final_state["final_response"]

        except Exception as e:
            logger.error(f"Error in workflow process: {str(e)}", exc_info=True)
            return {
                "response": f"Error processing query: {str(e)}",
                "sources": [],
                "response_type": "error",
                "error": True,
            }
