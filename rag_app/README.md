# RAG Application with LangGraph and Mistral AI

A sophisticated multi-agent Retrieval-Augmented Generation (RAG) system built with Python, LangGraph, and Mistral AI. The application uses an intelligent orchestration architecture with specialized agents for routing, document retrieval, and knowledge-based responses.

## Architecture

The system consists of three specialized agents orchestrated by LangGraph:

### Agents

1. **Router Agent**: Analyzes incoming queries to determine if they require external knowledge (RAG) or can be answered from the model's pre-trained knowledge.

2. **RAG Agent**: Retrieves relevant documents from Weaviate and generates responses augmented with external knowledge, citing sources.

3. **LLM Agent**: Generates responses using only the model's general knowledge when RAG is not required.

### Workflow

```
Query Input
    ↓
[Router Agent] - Decides: RAG or LLM?
    ↓ (conditional routing)
    ├→ [RAG Agent] → Retrieve documents → Generate augmented response
    │                                             ↓
    └→ [LLM Agent] → Generate response from knowledge
                                             ↓
                                    [Finalizer]
                                             ↓
                                      Final Response
```

## Features

- **Intelligent Routing**: Router agent intelligently decides when to use RAG vs. pure LLM
- **Structured Logging**: Comprehensive JSON logging with performance metrics
- **Error Handling**: Graceful error handling with detailed error messages
- **REST API**: Clean FastAPI interface for querying
- **Vector Search**: Weaviate integration for semantic document retrieval
- **Mistral AI**: Integration with Mistral AI models for high-quality responses

## Prerequisites

- Python 3.9+
- Mistral API key
- Docker (for running Weaviate)

## Installation

### 1. Clone the Repository

```bash
cd /workspace/rag_app
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables

```bash
cp .env.template .env
```

Edit `.env` and add your Mistral API key:

```
MISTRAL_API_KEY=your_api_key_here
WEAVIATE_HOST=localhost
WEAVIATE_PORT=8080
WEAVIATE_SCHEME=http
LOG_LEVEL=INFO
API_HOST=0.0.0.0
API_PORT=8000
```

### 5. Start Weaviate

The application requires Weaviate to be running. Start it with Docker:

```bash
docker run -p 8080:8080 semitechnologies/weaviate:latest
```

To verify Weaviate is running:

```bash
curl http://localhost:8080/v1/.well-known/ready
```

## Quick Start

### Initialize Database and Start API (Development Mode)

```bash
python main.py --dev
```

This will:
1. Initialize Weaviate with sample documents
2. Start the API server on `http://localhost:8000`

### Or Initialize and Start Separately

1. **Populate Sample Data**:
   ```bash
   python populate_data.py
   ```

2. **Start the API Server**:
   ```bash
   python main.py --start-api
   ```

## API Usage

### Base URL

```
http://localhost:8000
```

### Endpoints

#### Health Check
```bash
curl http://localhost:8000/health
```

#### Query Endpoint
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python and its main features?"}'
```

#### API Documentation
- Interactive Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Example Queries

**Query that triggers RAG:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What does the document say about Machine Learning?"}'
```

**Query that uses LLM knowledge:**
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain the concept of recursion in programming"}'
```

### Request Format

```json
{
  "query": "Your question here",
  "top_k": 3
}
```

- `query` (required): The user's query
- `top_k` (optional): Number of documents to retrieve (default: 3)

### Response Format

```json
{
  "response": "Generated response text",
  "response_type": "rag",
  "sources": ["Document Title 1", "Document Title 2"],
  "routing_decision": {
    "use_rag": true,
    "reasoning": "Query asks about specific documents"
  },
  "error": false,
  "processing_time_ms": 1234.5
}
```

## Project Structure

```
rag_app/
├── agents/                  # Specialized agents
│   ├── __init__.py
│   ├── router_agent.py     # Routes queries to RAG or LLM
│   ├── rag_agent.py        # Retrieves documents and generates augmented responses
│   └── llm_agent.py        # Generates responses from LLM knowledge
├── services/               # Service layer
│   ├── __init__.py
│   ├── weaviate_client.py  # Weaviate database client
│   └── sample_data.py      # Sample document loader
├── utils/                  # Utility modules
│   ├── __init__.py
│   └── logger.py           # Structured logging setup
├── config.py               # Configuration management
├── workflow.py             # LangGraph orchestration
├── api.py                  # FastAPI application
├── main.py                 # Entry point
├── populate_data.py        # Data population script
├── requirements.txt        # Python dependencies
├── .env.template           # Environment template
└── README.md              # This file
```

## Logging

All operations are logged with structured JSON logging. Logs include:

- **Timestamp**: ISO format UTC time
- **Log Level**: DEBUG, INFO, WARNING, ERROR
- **Module & Function**: Where the log originated
- **Message**: Main log message
- **Extra Data**: Additional context specific to the operation

Example log output:
```json
{
  "timestamp": "2024-10-26T15:30:45.123456",
  "level": "INFO",
  "logger": "agents.router_agent",
  "message": "Router decision: use_rag=true",
  "function": "decide",
  "extra_data": {
    "query": "What is Python?",
    "use_rag": true,
    "reasoning": "Query asks about technical details"
  }
}
```

## Configuration

All configuration is managed through `config.py` and environment variables:

### Mistral AI Settings
- `MISTRAL_API_KEY`: Your Mistral API key
- `mistral_model`: Model to use (default: mistral-medium)
- `mistral_temperature`: Response creativity (0-1)
- `mistral_max_tokens`: Maximum response length

### Weaviate Settings
- `WEAVIATE_HOST`: Weaviate host (default: localhost)
- `WEAVIATE_PORT`: Weaviate port (default: 8080)
- `WEAVIATE_SCHEME`: Connection scheme (default: http)

### RAG Settings
- `rag_top_k`: Number of documents to retrieve (default: 3)
- `rag_similarity_threshold`: Minimum similarity score (default: 0.7)

### Application Settings
- `LOG_LEVEL`: Logging level (default: INFO)
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 8000)

## Sample Documents

The application comes with sample documents on:

- Python Programming Basics
- Machine Learning with Scikit-Learn
- Web Development with FastAPI
- Natural Language Processing with NLTK
- Data Analysis with Pandas
- Deep Learning with TensorFlow and Keras
- API Development Best Practices
- Docker Containerization Guide

These are automatically populated when you run `python populate_data.py`.

## Error Handling

The application includes comprehensive error handling:

- **Connection Errors**: Gracefully handles Weaviate connection failures
- **API Errors**: Proper HTTP status codes and error messages
- **Processing Errors**: Falls back to LLM when RAG fails
- **Logging**: All errors are logged with full stack traces

## Performance Monitoring

Each query returns processing time:

```json
{
  "processing_time_ms": 1234.5
}
```

Logs include detailed timing information for each component:
- Router decision time
- Document retrieval time
- Response generation time

## Troubleshooting

### Weaviate Connection Error
```
Error connecting to Weaviate
```

**Solution**: Start Weaviate with Docker:
```bash
docker run -p 8080:8080 semitechnologies/weaviate:latest
```

### Mistral API Key Error
```
Failed to initialize RouterAgent: Authentication failed
```

**Solution**: Verify your API key in `.env`:
```bash
MISTRAL_API_KEY=your_actual_api_key
```

### No Documents Found
If RAG returns no results:
- Check that `populate_data.py` was run successfully
- Verify Weaviate is running and healthy

### API Port Already in Use
```
Address already in use
```

**Solution**: Change the port in `.env`:
```bash
API_PORT=8001
```

## Development

### Running Tests
```bash
# Tests can be added in a tests/ directory
pytest tests/
```

### Code Structure

- **Agents**: Implement specific behaviors (routing, RAG, LLM)
- **Services**: Handle external integrations (Weaviate, API calls)
- **Utils**: Shared utilities (logging, helpers)
- **Workflow**: LangGraph orchestration logic

## Future Enhancements

- [ ] Support for multiple vector databases
- [ ] Document upload API endpoint
- [ ] Advanced filtering and search options
- [ ] Response caching
- [ ] Multi-modal document support (images, tables)
- [ ] Feedback and relevance scoring
- [ ] Performance analytics dashboard

## License

MIT License

## Support

For issues or questions, please refer to the documentation or create an issue in the repository.

## Resources

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph/)
- [Mistral AI API](https://docs.mistral.ai/)
- [Weaviate Documentation](https://weaviate.io/developers/weaviate/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
