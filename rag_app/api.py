from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from workflow import RAGWorkflow
from utils.logger import setup_logger
from config import settings

logger = setup_logger(__name__)

app = FastAPI(
    title="RAG Application with LangGraph",
    description="A multi-agent RAG system using LangGraph and Mistral AI",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    workflow = RAGWorkflow()
except Exception as e:
    logger.error(f"Failed to initialize workflow: {str(e)}", exc_info=True)
    workflow = None


class QueryRequest(BaseModel):
    """Request model for query endpoint."""

    query: str = Field(..., description="The user's query")
    top_k: Optional[int] = Field(
        default=None, description="Number of documents to retrieve in RAG"
    )

    class Config:
        example = {
            "query": "What is Python and its main features?",
            "top_k": 3,
        }


class QueryResponse(BaseModel):
    """Response model for query endpoint."""

    response: str
    response_type: str = Field(..., description="Type of response: 'rag' or 'llm'")
    sources: List[str] = Field(default_factory=list, description="Source documents used")
    routing_decision: Dict[str, Any] = Field(
        default_factory=dict, description="Router decision details"
    )
    error: bool = Field(default=False, description="Whether an error occurred")
    processing_time_ms: float = Field(
        ..., description="Time taken to process the query in milliseconds"
    )

    class Config:
        example = {
            "response": "Python is a high-level programming language...",
            "response_type": "rag",
            "sources": ["Python Programming Basics", "Python Best Practices"],
            "routing_decision": {
                "use_rag": True,
                "reasoning": "Query asks about Python features",
            },
            "error": False,
            "processing_time_ms": 1234.5,
        }


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "RAG Application with LangGraph",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "query": "/query",
            "health": "/health",
            "docs": "/docs",
        },
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    if workflow is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Workflow not initialized",
        )

    return {
        "status": "healthy",
        "workflow_initialized": workflow is not None,
    }


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def process_query(request: QueryRequest):
    """
    Process a query through the RAG workflow.

    This endpoint:
    1. Routes the query to determine if RAG is needed
    2. If RAG: retrieves relevant documents and augments response
    3. If LLM: generates response from model knowledge
    4. Returns the final response with metadata
    """
    if workflow is None:
        logger.error("Workflow not initialized")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Workflow not initialized",
        )

    start_time = time.time()

    try:
        logger.info(
            f"Processing query: {request.query[:100]}",
            extra={
                "extra_data": {
                    "query": request.query[:100],
                    "top_k": request.top_k,
                }
            },
        )

        result = workflow.process(request.query)

        processing_time_ms = (time.time() - start_time) * 1000

        response = QueryResponse(
            response=result.get("response", "No response generated"),
            response_type=result.get("response_type", "unknown"),
            sources=result.get("sources", []),
            routing_decision=result.get("routing_decision", {}),
            error=result.get("error", False),
            processing_time_ms=processing_time_ms,
        )

        logger.info(
            "Query processed successfully",
            extra={
                "extra_data": {
                    "query": request.query[:100],
                    "response_type": response.response_type,
                    "processing_time_ms": processing_time_ms,
                    "has_error": response.error,
                }
            },
        )

        return response

    except Exception as e:
        processing_time_ms = (time.time() - start_time) * 1000
        logger.error(
            f"Error processing query: {str(e)}",
            exc_info=True,
            extra={
                "extra_data": {
                    "query": request.query[:100],
                    "processing_time_ms": processing_time_ms,
                }
            },
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing query: {str(e)}",
        )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler with logging."""
    logger.error(
        f"HTTP Exception: {exc.detail}",
        extra={
            "extra_data": {
                "status_code": exc.status_code,
                "detail": exc.detail,
            }
        },
    )
    return {
        "error": True,
        "message": exc.detail,
        "status_code": exc.status_code,
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler with logging."""
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"extra_data": {"exception_type": type(exc).__name__}},
    )
    return {
        "error": True,
        "message": "Internal server error",
        "status_code": 500,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=settings.api_host,
        port=settings.api_port,
        log_config=None,
    )
