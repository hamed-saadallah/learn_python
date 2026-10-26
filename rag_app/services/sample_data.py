from typing import List, Dict, Any
from utils.logger import setup_logger, log_execution
from services.weaviate_client import WeaviateClient

logger = setup_logger(__name__)

SAMPLE_DOCUMENTS = [
    {
        "title": "Python Programming Basics",
        "source": "tutorial",
        "content": "Python is a high-level, general-purpose programming language. It emphasizes code readability and simplicity. Python supports multiple programming paradigms including procedural, object-oriented, and functional programming. Key features include dynamic typing, automatic memory management, and a comprehensive standard library.",
    },
    {
        "title": "Machine Learning with Scikit-Learn",
        "source": "guide",
        "content": "Scikit-Learn is a popular Python library for machine learning built on NumPy, SciPy, and matplotlib. It provides simple and efficient tools for data mining and data analysis. Scikit-Learn includes algorithms for classification, regression, clustering, and dimensionality reduction. The library is designed for real-world machine learning applications.",
    },
    {
        "title": "Web Development with FastAPI",
        "source": "documentation",
        "content": "FastAPI is a modern, fast web framework for building APIs with Python 3.7+. It is based on standard Python type hints and automatically generates interactive API documentation. FastAPI provides features like automatic validation, serialization, and authentication. It has been noted as one of the fastest Python frameworks available.",
    },
    {
        "title": "Natural Language Processing with NLTK",
        "source": "tutorial",
        "content": "The Natural Language Toolkit (NLTK) is a leading platform for building Python programs to work with human language data. It provides easy-to-use interfaces to over 50 corpora and lexical resources. NLTK includes modules for classification, tokenization, stemming, tagging, parsing, and semantic reasoning.",
    },
    {
        "title": "Data Analysis with Pandas",
        "source": "guide",
        "content": "Pandas is a powerful and flexible open-source data analysis and manipulation library for Python. It provides high-performance, easy-to-use data structures and data analysis tools. Key features include DataFrames for structured data, time series functionality, and integrated I/O tools for reading and writing data in various formats.",
    },
    {
        "title": "Deep Learning with TensorFlow and Keras",
        "source": "documentation",
        "content": "TensorFlow is an open-source machine learning framework developed by Google. Keras is a high-level neural networks API that runs on top of TensorFlow. Together, they provide an easy way to build and train deep neural networks. TensorFlow supports distributed training and deployment on various platforms.",
    },
    {
        "title": "API Development Best Practices",
        "source": "guide",
        "content": "Building robust APIs requires careful consideration of security, performance, and user experience. Key principles include proper authentication and authorization, input validation, rate limiting, and comprehensive error handling. Well-designed APIs follow RESTful principles, use meaningful HTTP status codes, and provide clear documentation.",
    },
    {
        "title": "Docker Containerization Guide",
        "source": "tutorial",
        "content": "Docker is a containerization platform that allows developers to package applications and their dependencies into containers. Containers provide isolation, consistency, and portability across different environments. Docker uses images and containers to simplify deployment and scaling of applications.",
    },
]


@log_execution(logger)
def populate_sample_data(client: WeaviateClient) -> None:
    """Populate Weaviate with sample documents."""
    class_name = "Document"
    
    properties = [
        {"name": "title", "dataType": ["string"]},
        {"name": "source", "dataType": ["string"]},
        {"name": "content", "dataType": ["text"]},
    ]

    try:
        client.create_class(class_name, properties)
        
        for idx, doc in enumerate(SAMPLE_DOCUMENTS):
            try:
                client.add_document(class_name, doc, doc_id=f"doc_{idx}")
                logger.info(
                    f"Added document: {doc['title']}",
                    extra={"extra_data": {"title": doc["title"], "index": idx}},
                )
            except Exception as e:
                logger.error(
                    f"Failed to add document {doc['title']}: {str(e)}",
                    exc_info=True,
                )

        logger.info(
            f"Successfully populated {len(SAMPLE_DOCUMENTS)} sample documents",
            extra={"extra_data": {"document_count": len(SAMPLE_DOCUMENTS)}},
        )

    except Exception as e:
        logger.error(f"Error populating sample data: {str(e)}", exc_info=True)
        raise


def get_sample_documents() -> List[Dict[str, Any]]:
    """Return sample documents for reference."""
    return SAMPLE_DOCUMENTS
