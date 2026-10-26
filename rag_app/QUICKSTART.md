# Quick Start Guide

Get the RAG application running in 5 minutes!

## Prerequisites

- Python 3.9 or higher
- Docker (for Weaviate)
- Mistral API key (get one at https://console.mistral.ai/)

## Step 1: Start Weaviate

```bash
docker run -p 8080:8080 semitechnologies/weaviate:latest
```

Or use Docker Compose:
```bash
cd /workspace/rag_app
docker-compose up -d
```

Verify it's running:
```bash
curl http://localhost:8080/v1/.well-known/ready
```

## Step 2: Setup Python Environment

```bash
cd /workspace/rag_app
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 3: Configure Environment

```bash
cp .env.template .env
```

Edit `.env` and add your Mistral API key:
```
MISTRAL_API_KEY=sk-xxxxxxxxxxxxx
```

## Step 4: Populate Sample Data

```bash
python populate_data.py
```

You should see logs indicating 8 sample documents were added.

## Step 5: Start the API

```bash
python main.py --start-api
```

The API will be available at `http://localhost:8000`

## Step 6: Make a Query

Open a new terminal and run:

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?"}'
```

Or open the interactive docs:
```
http://localhost:8000/docs
```

## Example Queries to Try

### Queries that trigger RAG:
```bash
# Will search for related documents
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Tell me about FastAPI"}'
```

### Queries that use LLM knowledge:
```bash
# Will use model knowledge
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Explain recursion in programming"}'
```

## One-Command Start (Development)

After initial setup, you can start everything with:

```bash
# Terminal 1: Start Weaviate
docker run -p 8080:8080 semitechnologies/weaviate:latest

# Terminal 2: Activate env and start API with data initialization
cd /workspace/rag_app
source venv/bin/activate
python main.py --dev
```

## Architecture Flow

```
Your Query
    ↓
┌─────────────────┐
│ Router Agent    │ ← Decides: need RAG or LLM knowledge?
└────────┬────────┘
         ↓
      RAG Need?
     /         \
   YES          NO
   ↓            ↓
┌──────────────────────────┐    ┌──────────────────┐
│ Retrieve from Weaviate   │    │ Use LLM Knowledge│
│ + Generate with Context  │    └──────────────────┘
└──────────────────────────┘              ↓
         ↓                                 ↓
    Final Response with Citations    Direct Response
         ↓                                 ↓
         └──────────────┬──────────────────┘
                        ↓
                Your Answer + Metadata
```

## Logs and Monitoring

Check the logs to see the decision-making process:

```bash
# Run and watch logs
python main.py --dev 2>&1 | grep -i "router\|rag\|response"
```

Each query logs:
- Router decision (RAG or LLM)
- Documents retrieved (if RAG)
- Processing time
- Any errors encountered

## Troubleshooting

**Weaviate not responding:**
```bash
docker logs $(docker ps | grep weaviate | awk '{print $1}')
```

**API port in use:**
Edit `.env`:
```
API_PORT=8001
```

**Mistral API key not working:**
- Check your `.env` file has the key
- Verify key is valid at https://console.mistral.ai/
- Keys should start with `sk-`

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the code in `agents/`, `services/`, `workflow.py`
- Customize agents for your use case
- Add your own documents to Weaviate

## Support

For issues:
1. Check logs with `grep -i error`
2. Verify Weaviate is running on port 8080
3. Verify Mistral API key is set correctly
4. Review the full README.md for more details
