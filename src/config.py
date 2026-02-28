import os
from dotenv import load_dotenv

load_dotenv()

# Anthropic
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Haiku for tagging — simple classification task
CLAUDE_MODEL_FAST  = "claude-haiku-4-5-20251001"

# Sonnet for answering questions — quality matters here
CLAUDE_MODEL_SMART = "claude-sonnet-4-6"

# Embeddings
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Vector store
VECTORSTORE_PATH = "vectorstore"
COLLECTION_NAME  = "personal_kb"

# Chunking
CHUNK_SIZE    = 800   # slightly larger than HP RAG — articles have more context
CHUNK_OVERLAP = 100

# Retrieval
TOP_K = 5

# Tagging
MAX_TAGS = 5   # maximum number of tags per document
