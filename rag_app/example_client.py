#!/usr/bin/env python
"""
Example client script to interact with the RAG API.

Usage:
    python example_client.py
"""

import requests
import json
import time
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

EXAMPLE_QUERIES = [
    {
        "query": "What is Python and its main features?",
        "description": "General Python question - might use RAG",
    },
    {
        "query": "Tell me about machine learning with scikit-learn",
        "description": "Specific to document - will use RAG",
    },
    {
        "query": "Explain the concept of recursion",
        "description": "General programming concept - will use LLM",
    },
    {
        "query": "What is FastAPI and how does it work?",
        "description": "Specific framework - will use RAG",
    },
    {
        "query": "How do I containerize a Python application?",
        "description": "Docker/containerization question - will use RAG",
    },
]


def check_health() -> bool:
    """Check if the API is healthy."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception as e:
        print(f"Error checking health: {e}")
        return False


def query_api(query: str, top_k: int = 3) -> Dict[str, Any]:
    """
    Send a query to the API.

    Args:
        query: The question to ask
        top_k: Number of documents to retrieve

    Returns:
        API response
    """
    try:
        payload = {"query": query, "top_k": top_k}
        response = requests.post(
            f"{BASE_URL}/query",
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"Error: Cannot connect to API at {BASE_URL}")
        print("Make sure the API is running: python main.py --start-api")
        return None
    except Exception as e:
        print(f"Error querying API: {e}")
        return None


def print_response(query: str, response: Dict[str, Any]) -> None:
    """Pretty print the API response."""
    if response is None:
        return

    print("\n" + "=" * 80)
    print(f"QUERY: {query}")
    print("=" * 80)

    print(f"\nRESPONSE TYPE: {response.get('response_type', 'unknown')}")
    print(f"PROCESSING TIME: {response.get('processing_time_ms', 0):.2f}ms")

    print("\nROUTING DECISION:")
    routing = response.get("routing_decision", {})
    print(f"  - Use RAG: {routing.get('use_rag', 'N/A')}")
    print(f"  - Reasoning: {routing.get('reasoning', 'N/A')}")

    print("\nRESPONSE:")
    print("-" * 80)
    response_text = response.get("response", "No response")
    # Wrap long responses
    words = response_text.split()
    line = ""
    for word in words:
        if len(line) + len(word) + 1 > 80:
            print(line)
            line = word
        else:
            line = f"{line} {word}" if line else word
    if line:
        print(line)
    print("-" * 80)

    sources = response.get("sources", [])
    if sources:
        print("\nSOURCES:")
        for i, source in enumerate(sources, 1):
            print(f"  {i}. {source}")
    else:
        print("\nSOURCES: None (LLM knowledge only)")

    if response.get("error"):
        print(f"\nERROR: {response.get('response', 'Unknown error')}")

    print()


def main():
    """Main function."""
    print("RAG Application Client")
    print("=" * 80)

    # Check health
    print("Checking API health...")
    if not check_health():
        print("ERROR: API is not healthy or not running")
        print("Start it with: python main.py --start-api")
        return

    print("✓ API is healthy\n")

    # Run example queries
    print("Running example queries...\n")

    for example in EXAMPLE_QUERIES:
        query = example["query"]
        description = example["description"]

        print(f"Query: {query}")
        print(f"Description: {description}")

        response = query_api(query)
        if response:
            print_response(query, response)
        else:
            print("Failed to get response\n")

        time.sleep(1)  # Small delay between requests

    print("\n" + "=" * 80)
    print("Examples completed!")
    print("\nTo try custom queries, modify EXAMPLE_QUERIES or add:")
    print("  response = query_api('Your custom query')")
    print("  print_response('Your custom query', response)")


if __name__ == "__main__":
    main()
