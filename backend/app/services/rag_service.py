import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from pypdf import PdfReader
import io
import uuid
import os

# Configuration ChromaDB persistent local
CHROMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/chroma"))
os.makedirs(CHROMA_PATH, exist_ok=True)
chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)

# Modèle d'embeddings léger et multilingue
embedding_model = None
def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        MODEL_PATH = os.path.join(os.path.dirname(__file__), "../../models/embedding_model")
        try:
            embedding_model = SentenceTransformer(MODEL_PATH)
        except Exception:
            embedding_model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
            try:
                os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
                embedding_model.save(MODEL_PATH)
            except Exception as e:
                print("Could not save embedding model:", e)
    return embedding_model


def extract_text_from_pdf(file_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text.strip()

def chunk_page_text(page_text: str, page_number: int, chunk_size: int = 400, overlap: int = 50) -> list:
    words = page_text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + chunk_size])
        chunks.append({
            "text": chunk,
            "page": page_number
        })
        i += chunk_size - overlap
    return chunks

def index_document(session_id: str, file_bytes: bytes, filename: str) -> dict:
    try:
        reader = PdfReader(io.BytesIO(file_bytes))
        all_chunks = []
        for idx, page in enumerate(reader.pages):
            page_number = idx + 1
            page_text = page.extract_text() or ""
            if page_text.strip():
                chunks = chunk_page_text(page_text, page_number)
                all_chunks.extend(chunks)

        if not all_chunks:
            return {
                "status": "error",
                "message": "Aucun texte extractible dans ce PDF."
            }

        # Créer une collection ChromaDB par session
        collection = chroma_client.get_or_create_collection(
            name=f"session_{session_id}"
        )

        # Générer les embeddings et indexer
        documents = [c["text"] for c in all_chunks]
        metadatas = [{"page": c["page"], "filename": filename} for c in all_chunks]
        embeddings = get_embedding_model().encode(documents).tolist()
        ids = [str(uuid.uuid4()) for _ in documents]

        collection.add(
            documents=documents,
            embeddings=embeddings,
            ids=ids,
            metadatas=metadatas
        )

        return {
            "status": "ok",
            "chunks_indexed": len(documents),
            "filename": filename
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def retrieve_context_with_sources(session_id: str, question: str, top_k: int = 4) -> tuple[str, list[dict]]:
    try:
        collection = chroma_client.get_collection(
            name=f"session_{session_id}"
        )
        question_embedding = get_embedding_model().encode([question]).tolist()
        results = collection.query(
            query_embeddings=question_embedding,
            n_results=top_k
        )
        
        fragments = results["documents"][0]
        metadatas = results["metadatas"][0]
        
        sources = []
        for doc, meta in zip(fragments, metadatas):
            sources.append({
                "page": meta.get("page", 1),
                "text": doc
            })
            
        context = "\n\n---\n\n".join(fragments)
        return context, sources
    except Exception as e:
        return "", []

def retrieve_context(session_id: str, question: str, top_k: int = 4) -> str:
    context, _ = retrieve_context_with_sources(session_id, question, top_k)
    return context

def summarize_document(session_id: str) -> str:
    try:
        collection = chroma_client.get_collection(
            name=f"session_{session_id}"
        )
        # Récupère les 6 premiers chunks pour le résumé
        results = collection.get(limit=6)
        fragments = results["documents"]
        return "\n\n".join(fragments)
    except Exception as e:
        return ""