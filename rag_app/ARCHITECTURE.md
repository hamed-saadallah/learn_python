# RAG Application Architecture

This document provides a detailed overview of the application architecture, design decisions, and component interactions.

## System Overview

The RAG application is a sophisticated multi-agent system that orchestrates specialized agents to provide intelligent responses to user queries. It combines retrieval-augmented generation with language model knowledge using LangGraph for orchestration.

## Component Architecture

### 1. Agent Layer

The agent layer consists of three specialized agents, each with a specific responsibility:

#### Router Agent (`agents/router_agent.py`)

**Responsibility**: Determines whether a query requires external knowledge (RAG) or can be answered from the model's pre-trained knowledge.

**Process**:
1. Receives user query
2. Sends to Mistral with routing prompt
3. Parses JSON response to extract decision
4. Returns routing decision with reasoning

**Decision Logic**:
- RAG used for: specific documents, domain knowledge, recent information
- LLM used for: general concepts, definitions, creative content

**Key Methods**:
- `decide(query: str)`: Analyzes query and returns routing decision

#### RAG Agent (`agents/rag_agent.py`)

**Responsibility**: Retrieves relevant documents and generates responses augmented with external knowledge.

**Process**:
1. Accepts query from router
2. Queries Weaviate for relevant documents
3. Formats documents as context
4. Sends query + context to Mistral
5. Returns response with source citations

**Key Methods**:
- `retrieve_documents(query, top_k)`: Searches Weaviate
- `_format_context(documents)`: Prepares documents for LLM
- `generate_response(query, documents)`: Creates augmented response
- `process(query, top_k)`: End-to-end RAG pipeline

#### LLM Agent (`agents/llm_agent.py`)

**Responsibility**: Generates responses using only the model's general knowledge.

**Process**:
1. Receives query from router
2. Sends to Mistral with system prompt
3. Returns response with metadata

**Key Methods**:
- `generate_response(query)`: Generates LLM response
- `process(query)`: Wraps response generation

### 2. Service Layer

The service layer handles external integrations and data operations.

#### Weaviate Client (`services/weaviate_client.py`)

**Responsibility**: Manages all interactions with Weaviate vector database.

**Capabilities**:
- Connection management
- Class creation and deletion
- Document addition and retrieval
- Vector similarity search
- Health checks

**Key Methods**:
- `create_class(class_name, properties)`: Creates schema
- `add_document(class_name, document, doc_id)`: Inserts document
- `search(class_name, query, top_k)`: Performs similarity search
- `health_check()`: Verifies Weaviate availability

#### Sample Data (`services/sample_data.py`)

**Responsibility**: Manages sample document population.

**Features**:
- 8 pre-defined sample documents
- Automatic schema creation
- Bulk document insertion
- Error handling for existing data

### 3. Orchestration Layer

#### LangGraph Workflow (`workflow.py`)

**Responsibility**: Orchestrates agent execution using LangGraph's StateGraph.

**Architecture**:
```
StateGraph with 4 nodes:
  - Router Node: Makes routing decision
  - RAG Node: Processes with RAG
  - LLM Node: Processes with LLM knowledge
  - Finalizer Node: Prepares final response
```

**State Structure**:
```python
WorkflowState(TypedDict):
    query: str
    router_decision: Dict[str, Any]
    use_rag: bool
    rag_result: Dict[str, Any]
    llm_result: Dict[str, Any]
    final_response: Dict[str, Any]
    error: bool
```

**Execution Flow**:
1. Entry → Router Node
2. Conditional Edge → RAG or LLM Node
3. Processing → Finalizer Node
4. Exit

**Key Methods**:
- `_build_graph()`: Constructs StateGraph
- `_router_node()`: Router execution
- `_rag_node()`: RAG execution
- `_llm_node()`: LLM execution
- `_finalizer_node()`: Response preparation
- `_route_decision()`: Conditional routing logic
- `process(query)`: Main workflow invocation

### 4. API Layer

#### FastAPI Application (`api.py`)

**Responsibility**: Exposes REST API for workflow access.

**Features**:
- POST `/query`: Process user queries
- GET `/health`: Health checks
- GET `/`: API information
- CORS support
- Request/response validation
- Exception handling
- Comprehensive logging

**Request Model**:
```json
{
  "query": "string",
  "top_k": "integer (optional)"
}
```

**Response Model**:
```json
{
  "response": "string",
  "response_type": "rag|llm",
  "sources": ["string"],
  "routing_decision": {},
  "error": "boolean",
  "processing_time_ms": "float"
}
```

### 5. Infrastructure Layer

#### Configuration (`config.py`)

**Responsibility**: Centralized configuration management.

**Configuration Areas**:
- Mistral AI settings (key, model, temperature, tokens)
- Weaviate settings (host, port, scheme)
- RAG settings (top_k, similarity threshold)
- Application settings (logging, API host/port)

**Retrieval**: Environment variables with defaults

#### Logging (`utils/logger.py`)

**Responsibility**: Structured JSON logging throughout application.

**Features**:
- JSON formatted logs
- Timestamp and metadata
- Function execution decorator
- Performance timing
- Error tracking

**Log Fields**:
```json
{
  "timestamp": "ISO format",
  "level": "DEBUG|INFO|WARNING|ERROR",
  "logger": "module.name",
  "message": "log message",
  "module": "module",
  "function": "function_name",
  "line": 123,
  "exception": "stack trace if error",
  "extra_data": {}
}
```

## Data Flow

### Query Processing Flow

```
┌─────────────────────────────────────────────────────┐
│ HTTP POST /query                                    │
│ {query: "What is Python?", top_k: 3}              │
└────────────────────┬────────────────────────────────┘
                     ↓
        ┌────────────────────────────┐
        │   API Request Validation    │
        │   & Logging                 │
        └────────────┬─────────────────┘
                     ↓
        ┌────────────────────────────┐
        │  Workflow.process(query)   │
        └────────────┬─────────────────┘
                     ↓
        ┌────────────────────────────┐
        │  [Router Node]              │
        │  Router.decide(query)       │
        │  ↓ Decision: use RAG?       │
        └────────────┬─────────────────┘
                     ↓
         ┌───────────┴────────────┐
         ↓                        ↓
    [RAG Path]            [LLM Path]
    RAG.process()         LLM.process()
         ↓                        ↓
    Weaviate.search()    Mistral.chat()
         ↓                        ↓
    [retrieve docs]       [generate]
         ↓                        ↓
    Format context        Raw response
         ↓                        ↓
    Mistral.chat()        Return result
         ↓                        ↓
    [generate augmented]          ↓
         ↓                        ↓
         └────────────┬───────────┘
                      ↓
         ┌────────────────────────────┐
         │  [Finalizer Node]           │
         │  Prepare final response     │
         │  Add metadata               │
         └────────────┬─────────────────┘
                      ↓
         ┌────────────────────────────┐
         │  Response with:             │
         │  - Response text            │
         │  - Response type            │
         │  - Sources (if RAG)         │
         │  - Routing decision         │
         │  - Processing time          │
         │  - Error flag               │
         └────────────┬─────────────────┘
                      ↓
         ┌────────────────────────────┐
         │  HTTP 200 OK                │
         │  Return JSON response       │
         └────────────────────────────┘
```

## Integration Points

### Weaviate Integration

**When Used**: RAG Node execution

**Operations**:
1. Schema Definition: "Document" class with title, source, content
2. Document Insertion: Added during initialization
3. Vector Search: Semantic similarity search on content
4. Results: Top K documents retrieved and formatted

### Mistral AI Integration

**When Used**: All agent nodes (Router, RAG, LLM)

**Operations**:
- Router: Analyzes query intent
- RAG: Augments documents with context
- LLM: Generates raw responses

**API Calls**: One per agent node per query

### LangGraph Integration

**Graph Construction**: StateGraph with conditional edges

**State Management**: Maintains query, decisions, and results across nodes

**Execution**: Manages node execution order and data flow

## Error Handling Strategy

### Levels of Error Handling

1. **Initialization Level**
   - Validates API keys
   - Tests Weaviate connectivity
   - Catches configuration errors

2. **Processing Level**
   - Try-catch in each agent
   - Logs full exception details
   - Returns error metadata

3. **Fallback Level**
   - RAG failure → still attempt response
   - LLM failure → return error message
   - Partial results → return what's available

4. **API Level**
   - HTTPException for HTTP errors
   - Generic exception handler
   - Logs all exceptions

### Error Recovery

- Router failure: Falls back to LLM
- Weaviate unavailable: Returns error
- Mistral API error: Returns error
- Parsing error: Logs and continues

## Performance Considerations

### Optimization Strategies

1. **Caching** (Future): Cache frequently asked questions
2. **Batching**: Could batch multiple queries
3. **Indexing**: Weaviate handles vector indexing
4. **Async**: Could make API calls asynchronous

### Performance Metrics

- Router decision time: ~500-1000ms
- Document retrieval: ~200-500ms
- Response generation: ~1000-3000ms
- Total query time: ~2000-5000ms

### Bottlenecks

- Mistral API latency (primary)
- Weaviate search latency (secondary)
- Document formatting (negligible)

## Security Considerations

1. **API Keys**: Stored in .env, loaded via config
2. **Input Validation**: Pydantic models validate requests
3. **Error Messages**: Don't leak sensitive information
4. **Logging**: Masks sensitive data where possible
5. **CORS**: Configured for local development

## Scalability Architecture

### Horizontal Scaling Options

1. **Multiple API Instances**: Load balance behind reverse proxy
2. **Weaviate Cluster**: Multi-node Weaviate setup
3. **Agent Pool**: Multiple agent instances
4. **Caching Layer**: Redis for response caching

### Vertical Scaling Options

1. **Larger Mistral Model**: mistral-large for better quality
2. **Larger Weaviate Instance**: More memory for larger datasets
3. **Batch Processing**: Handle multiple queries simultaneously

## Extension Points

### Easy Customizations

1. **Custom Agents**: Add new agent types
2. **Different LLMs**: Swap Mistral for another provider
3. **Different Vector DB**: Replace Weaviate with alternatives
4. **Custom Routing Logic**: Modify router decision criteria
5. **Additional Data Sources**: Extend sample_data.py

### Advanced Customizations

1. **Multi-turn Conversations**: Add chat history
2. **Document Upload**: Dynamic document addition
3. **User Feedback**: Collect relevance feedback
4. **A/B Testing**: Test different routing strategies
5. **Analytics**: Track query patterns and performance

## Deployment Architecture

### Development
- Local Weaviate (Docker)
- FastAPI dev server
- Direct Python execution

### Production
- Containerized Weaviate (Docker/Kubernetes)
- Gunicorn/Uvicorn for ASGI
- Load balancer for API
- Monitoring and logging infrastructure

## Monitoring and Observability

### Metrics Tracked
- Query count and types
- Router decisions (RAG vs LLM ratio)
- Document retrieval success rate
- Response generation time
- Error rates and types

### Logging Coverage
- All agent decisions
- All API calls
- Performance metrics
- Error stack traces

### Health Checks
- Weaviate availability
- API responsiveness
- Configuration validation
