
"""
Four endpoints —
/ingest to add a URL,
/query to ask a question,
/documents to see everything saved,
/health to check the system.

The key design decision is one shared store instance passed into both pipelines,
so they read and write to the same ChromaDB collection without conflicts.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from src.vector_store import VectorStore
from src.ingestion    import IngestionPipeline
from src.retriever    import Retriever

app   = Flask(__name__, static_folder="static")
CORS(app)

# Single shared store — both pipelines use the same ChromaDB collection
store     = VectorStore()
ingestor  = IngestionPipeline(store)
retriever = Retriever(store)


@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/ingest", methods=["POST"])
def ingest():
    data = request.get_json()
    url  = data.get("url", "").strip()

    if not url:
        return jsonify({"error": "No URL provided"}), 400

    result = ingestor.ingest_url(url)
    return jsonify(result)


@app.route("/query", methods=["POST"])
def query():
    data       = request.get_json()
    question   = data.get("question", "").strip()
    tag_filter = data.get("tag_filter", "").strip() or None

    if not question:
        return jsonify({"error": "No question provided"}), 400

    result = retriever.query(question, tag_filter=tag_filter)
    return jsonify(result)


@app.route("/documents", methods=["GET"])
def documents():
    return jsonify(store.list_documents())


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status":          "ok",
        "documents_count": len(store.list_documents()),
        "chunks_count":    store.collection.count()
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
