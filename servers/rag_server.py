import os
import re
from pathlib import Path
from typing import List, Dict, Any

import chromadb
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from mcp.server.mcpserver import MCPServer


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

DOCUMENTS_DIR = BASE_DIR / "sample_docs"
CHROMA_DIR = BASE_DIR / "chroma_db"

EMBEDDING_MODEL = "text-embedding-3-small"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 80

DEFAULT_TOP_K = 5
MAX_TOP_K = 10

CANDIDATE_MULTIPLIER = 4


# ============================================================
# OPENAI
# ============================================================

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "OPENAI_API_KEY is missing. "
        "Please add it to your .env file."
    )

client = OpenAI(api_key=API_KEY)


# ============================================================
# CHROMADB
# ============================================================

chroma_client = chromadb.PersistentClient(
    path=str(CHROMA_DIR)
)

COLLECTION_NAME = "testnexus_documents"


# ============================================================
# MCP SERVER
# ============================================================

mcp = MCPServer("TestNexus RAG Server")


# ============================================================
# STOP WORDS
# ============================================================

STOP_WORDS = {
    "what",
    "is",
    "are",
    "was",
    "were",
    "the",
    "a",
    "an",
    "for",
    "to",
    "of",
    "in",
    "on",
    "and",
    "or",
    "when",
    "how",
    "why",
    "which",
    "does",
    "do",
    "did",
    "can",
    "could",
    "would",
    "should",
    "returned",
    "return",
    "expected",
    "response",
    "result",
    "code",
}


# ============================================================
# IMPORTANT QA TERMS
# ============================================================

IMPORTANT_TERMS = {
    "wrong",
    "password",
    "credentials",
    "authentication",
    "unauthorized",
    "authorized",
    "login",
    "token",
    "error",
    "status",
    "401",
    "403",
    "404",
    "429",
    "500",
    "200",
}


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text: str) -> str:

    if not text:
        return ""

    text = text.replace("\x00", " ")

    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text: str) -> List[str]:

    if not text:
        return []

    words = re.findall(
        r"\b[a-zA-Z0-9_-]+\b",
        text.lower(),
    )

    return [
        word
        for word in words
        if word not in STOP_WORDS
    ]


# ============================================================
# KEYWORD SCORE
# ============================================================

def calculate_keyword_score(
    query: str,
    document: str,
) -> float:

    query_tokens = tokenize(query)
    document_tokens = set(
        tokenize(document)
    )

    if not query_tokens:
        return 0.0

    matched = sum(
        1
        for token in query_tokens
        if token in document_tokens
    )

    return matched / len(query_tokens)


# ============================================================
# IMPORTANT TERM SCORE
# ============================================================

def calculate_important_term_score(
    query: str,
    document: str,
) -> float:

    query_lower = query.lower()
    document_lower = document.lower()

    query_important_terms = [
        term
        for term in IMPORTANT_TERMS
        if term in query_lower
    ]

    if not query_important_terms:
        return 0.0

    matched = sum(
        1
        for term in query_important_terms
        if term in document_lower
    )

    return matched / len(
        query_important_terms
    )


# ============================================================
# EXACT PHRASE SCORE
# ============================================================

def calculate_phrase_score(
    query: str,
    document: str,
) -> float:

    query_lower = query.lower()
    document_lower = document.lower()

    phrases = [
        "wrong credentials",
        "wrong password",
        "invalid password",
        "invalid credentials",
        "status code",
        "authentication failed",
        "no token",
        "unauthorized",
        "rate limiting",
    ]

    matched_phrases = [
        phrase
        for phrase in phrases
        if phrase in query_lower
        and phrase in document_lower
    ]

    if matched_phrases:
        return 1.0

    # Also check meaningful consecutive
    # query words.
    query_tokens = tokenize(query)

    if len(query_tokens) >= 2:

        document_tokens = tokenize(
            document
        )

        for i in range(
            len(query_tokens) - 1
        ):

            phrase = (
                query_tokens[i]
                + " "
                + query_tokens[i + 1]
            )

            if phrase in document_lower:
                return 0.8

    return 0.0


# ============================================================
# STATUS CODE BOOST
# ============================================================

def calculate_status_code_boost(
    query: str,
    document: str,
) -> float:

    query_lower = query.lower()
    document_lower = document.lower()

    # If user asks about status code,
    # prioritize documents containing
    # explicit HTTP status codes.
    asks_status_code = (
        "status code" in query_lower
        or "http status" in query_lower
        or "response code" in query_lower
    )

    if not asks_status_code:
        return 0.0

    status_codes = re.findall(
        r"\b(?:200|201|400|401|403|404|409|422|429|500|502|503)\b",
        document_lower,
    )

    if status_codes:
        return 1.0

    return 0.0


# ============================================================
# PDF EXTRACTION
# ============================================================

def extract_pdf_pages(
    pdf_path: Path,
) -> List[Dict[str, Any]]:

    pages = []

    try:

        reader = PdfReader(
            str(pdf_path)
        )

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):

            try:

                text = (
                    page.extract_text()
                    or ""
                )

                text = clean_text(text)

                if text:

                    pages.append(
                        {
                            "text": text,
                            "page": page_number,
                        }
                    )

            except Exception as error:

                print(
                    f"Warning: Could not read "
                    f"page {page_number} from "
                    f"{pdf_path.name}: {error}"
                )

    except Exception as error:

        print(
            f"Error reading PDF "
            f"{pdf_path.name}: {error}"
        )

    return pages


# ============================================================
# CHUNKING
# ============================================================

def split_into_chunks(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[str]:

    text = clean_text(text)

    if not text:
        return []

    if chunk_size <= 0:
        raise ValueError(
            "chunk_size must be greater than 0"
        )

    if overlap < 0:
        raise ValueError(
            "overlap cannot be negative"
        )

    if overlap >= chunk_size:
        raise ValueError(
            "overlap must be smaller than chunk_size"
        )

    paragraphs = [
        paragraph.strip()
        for paragraph in re.split(
            r"\n\s*\n",
            text,
        )
        if paragraph.strip()
    ]

    chunks = []

    current = ""

    for paragraph in paragraphs:

        if len(paragraph) > chunk_size:

            if current:

                chunks.append(
                    current.strip()
                )

                current = ""

            start = 0

            while start < len(paragraph):

                end = (
                    start + chunk_size
                )

                chunk = paragraph[
                    start:end
                ].strip()

                if chunk:
                    chunks.append(chunk)

                if end >= len(paragraph):
                    break

                start = (
                    end - overlap
                )

            continue

        if not current:

            current = paragraph

        elif (
            len(current)
            + 2
            + len(paragraph)
            <= chunk_size
        ):

            current += (
                "\n\n"
                + paragraph
            )

        else:

            chunks.append(
                current.strip()
            )

            overlap_text = (
                current[-overlap:]
                if overlap
                else ""
            )

            if overlap_text:

                current = (
                    overlap_text
                    + "\n\n"
                    + paragraph
                )

            else:

                current = paragraph

    if current.strip():

        chunks.append(
            current.strip()
        )

    return chunks


# ============================================================
# EMBEDDINGS
# ============================================================

def create_embeddings(
    texts: List[str],
    batch_size: int = 100,
) -> List[List[float]]:

    if not texts:
        return []

    embeddings = []

    for start in range(
        0,
        len(texts),
        batch_size,
    ):

        batch = texts[
            start:start + batch_size
        ]

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=batch,
        )

        embeddings.extend(
            item.embedding
            for item in response.data
        )

    return embeddings


# ============================================================
# COLLECTION
# ============================================================

def get_collection(
    create: bool = True,
):

    if create:

        return chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={
                "description":
                    "TestNexus PDF knowledge base"
            },
        )

    try:

        return chroma_client.get_collection(
            name=COLLECTION_NAME
        )

    except Exception:

        return None


# ============================================================
# INDEX DOCUMENTS
# ============================================================

def index_documents() -> Dict[str, Any]:

    if not DOCUMENTS_DIR.exists():

        return {
            "status": "error",
            "message":
                f"Documents directory does not exist: "
                f"{DOCUMENTS_DIR}",
        }

    pdf_files = sorted(
        DOCUMENTS_DIR.glob("*.pdf")
    )

    if not pdf_files:

        return {
            "status": "error",
            "message":
                "No PDF files found.",
        }

    all_documents = []
    all_metadatas = []
    all_ids = []

    document_count = 0

    for pdf_path in pdf_files:

        pages = extract_pdf_pages(
            pdf_path
        )

        if not pages:

            print(
                f"Skipping empty/unreadable PDF: "
                f"{pdf_path.name}"
            )

            continue

        document_count += 1

        for page_data in pages:

            page_text = page_data[
                "text"
            ]

            page_number = page_data[
                "page"
            ]

            chunks = split_into_chunks(
                page_text
            )

            for chunk_number, chunk in enumerate(
                chunks,
                start=1,
            ):

                if not chunk.strip():
                    continue

                document_id = (
                    f"{pdf_path.stem}"
                    f"_page_{page_number}"
                    f"_chunk_{chunk_number}"
                )

                all_documents.append(
                    chunk
                )

                all_metadatas.append(
                    {
                        "source":
                            pdf_path.name,
                        "page":
                            page_number,
                        "chunk":
                            chunk_number,
                    }
                )

                all_ids.append(
                    document_id
                )

    if not all_documents:

        return {
            "status": "error",
            "message":
                "No readable text found.",
        }

    # Create embeddings first.
    # This protects the old index if
    # OpenAI embedding creation fails.
    try:

        embeddings = create_embeddings(
            all_documents
        )

    except Exception as error:

        return {
            "status": "error",
            "message":
                f"Embedding creation failed: {error}",
        }

    try:

        try:

            chroma_client.delete_collection(
                name=COLLECTION_NAME
            )

        except Exception:

            pass

        collection = get_collection(
            create=True
        )

        collection.add(
            ids=all_ids,
            documents=all_documents,
            embeddings=embeddings,
            metadatas=all_metadatas,
        )

    except Exception as error:

        return {
            "status": "error",
            "message":
                f"ChromaDB indexing failed: {error}",
        }

    return {
        "status": "success",
        "documents": document_count,
        "chunks": len(all_documents),
        "collection":
            COLLECTION_NAME,
        "message":
            "PDF documents indexed successfully.",
    }


# ============================================================
# LIST DOCUMENTS TOOL
# ============================================================

@mcp.tool()
def list_documents() -> str:

    try:

        if not DOCUMENTS_DIR.exists():

            return (
                "Documents directory does not exist."
            )

        pdf_files = sorted(
            DOCUMENTS_DIR.glob("*.pdf")
        )

        if not pdf_files:

            return "No PDF documents found."

        output = [
            "AVAILABLE PDF DOCUMENTS",
            "========================",
        ]

        valid_count = 0

        for pdf_path in pdf_files:

            size = pdf_path.stat().st_size

            if size > 0:

                status = "available"
                valid_count += 1

            else:

                status = "empty"

            output.append(
                f"- {pdf_path.name} "
                f"({size} bytes, {status})"
            )

        output.append("")
        output.append(
            f"Valid PDFs: {valid_count}"
        )

        return "\n".join(output)

    except Exception as error:

        return (
            f"Error listing documents: {error}"
        )


# ============================================================
# SEARCH DOCUMENTS
# ============================================================

@mcp.tool()
def search_documents(
    query: str,
    top_k: int = DEFAULT_TOP_K,
) -> str:
    """
    Hybrid RAG retrieval:

    1. Semantic search
    2. Keyword matching
    3. Important QA term matching
    4. Exact phrase matching
    5. HTTP status-code boost
    6. Final reranking
    """

    query = query.strip()

    if not query:

        return "Please provide a search query."

    top_k = max(
        1,
        min(
            top_k,
            MAX_TOP_K,
        ),
    )

    try:

        collection = get_collection(
            create=False
        )

        if collection is None:

            result = index_documents()

            if result.get("status") != "success":

                return (
                    "Unable to create document index.\n"
                    f"{result.get('message', '')}"
                )

            collection = get_collection(
                create=False
            )

        if collection is None:

            return (
                "Document collection is unavailable."
            )

        count = collection.count()

        if count == 0:

            result = index_documents()

            if result.get("status") != "success":

                return (
                    "Document index is empty.\n"
                    f"{result.get('message', '')}"
                )

            collection = get_collection(
                create=False
            )

            count = collection.count()

        if count == 0:

            return (
                "No indexed documents available."
            )

        # ----------------------------------------------------
        # QUERY EMBEDDING
        # ----------------------------------------------------

        query_embedding = create_embeddings(
            [query]
        )[0]

        # Retrieve extra candidates
        # before reranking.
        candidate_count = min(
            count,
            max(
                top_k * CANDIDATE_MULTIPLIER,
                10,
            ),
        )

        results = collection.query(
            query_embeddings=[
                query_embedding
            ],
            n_results=candidate_count,
            include=[
                "documents",
                "metadatas",
                "distances",
            ],
        )

    except Exception as error:

        return (
            f"Document search failed: {error}"
        )

    documents = results.get(
        "documents",
        [[]],
    )[0]

    metadatas = results.get(
        "metadatas",
        [[]],
    )[0]

    distances = results.get(
        "distances",
        [[]],
    )[0]

    if not documents:

        return (
            "No relevant information found."
        )

    # ========================================================
    # RERANK
    # ========================================================

    ranked_results = []

    for index, document in enumerate(
        documents
    ):

        metadata = (
            metadatas[index]
            if index < len(metadatas)
            else {}
        )

        distance = (
            distances[index]
            if index < len(distances)
            else 999.0
        )

        # Semantic score
        semantic_score = (
            1.0
            / (
                1.0
                + float(distance)
            )
        )

        # Keyword score
        keyword_match = (
            calculate_keyword_score(
                query,
                document,
            )
        )

        # Important QA term score
        important_match = (
            calculate_important_term_score(
                query,
                document,
            )
        )

        # Phrase score
        phrase_match = (
            calculate_phrase_score(
                query,
                document,
            )
        )

        # Status code boost
        status_boost = (
            calculate_status_code_boost(
                query,
                document,
            )
        )

        # ----------------------------------------------------
        # FINAL SCORE
        # ----------------------------------------------------

        final_score = (
            0.45 * semantic_score
            + 0.20 * keyword_match
            + 0.15 * important_match
            + 0.10 * phrase_match
            + 0.10 * status_boost
        )

        ranked_results.append(
            {
                "document":
                    document,

                "metadata":
                    metadata,

                "distance":
                    distance,

                "semantic_score":
                    semantic_score,

                "keyword_score":
                    keyword_match,

                "important_score":
                    important_match,

                "phrase_score":
                    phrase_match,

                "status_boost":
                    status_boost,

                "final_score":
                    final_score,
            }
        )

    # Highest score first
    ranked_results.sort(
        key=lambda item:
            item["final_score"],
        reverse=True,
    )

    ranked_results = ranked_results[
        :top_k
    ]

    # ========================================================
    # OUTPUT
    # ========================================================

    output = [
        "RAG SEARCH RESULTS",
        "==================",
        f"Query: {query}",
        "",
    ]

    for index, result in enumerate(
        ranked_results,
        start=1,
    ):

        metadata = result[
            "metadata"
        ]

        source = metadata.get(
            "source",
            "Unknown",
        )

        page = metadata.get(
            "page",
            "Unknown",
        )

        chunk = metadata.get(
            "chunk",
            "Unknown",
        )

        output.append(
            f"Result {index}"
        )

        output.append(
            f"Source: {source}"
        )

        output.append(
            f"Page: {page}"
        )

        output.append(
            f"Chunk: {chunk}"
        )

        output.append(
            f"Distance: "
            f"{result['distance']:.4f}"
        )

        output.append(
            f"Semantic Score: "
            f"{result['semantic_score']:.4f}"
        )

        output.append(
            f"Keyword Score: "
            f"{result['keyword_score']:.4f}"
        )

        output.append(
            f"Important Term Score: "
            f"{result['important_score']:.4f}"
        )

        output.append(
            f"Phrase Score: "
            f"{result['phrase_score']:.4f}"
        )

        output.append(
            f"Status Code Boost: "
            f"{result['status_boost']:.4f}"
        )

        output.append(
            f"Final Score: "
            f"{result['final_score']:.4f}"
        )

        output.append(
            f"Content:\n"
            f"{result['document']}"
        )

        output.append(
            "-" * 60
        )

    return "\n".join(output)


# ============================================================
# REBUILD INDEX TOOL
# ============================================================

@mcp.tool()
def rebuild_index() -> str:

    result = index_documents()

    if result.get("status") == "success":

        return (
            "INDEX REBUILD SUCCESSFUL\n"
            "========================\n"
            f"Documents: "
            f"{result.get('documents')}\n"
            f"Chunks: "
            f"{result.get('chunks')}\n"
            f"Collection: "
            f"{result.get('collection')}\n"
        )

    return (
        "INDEX REBUILD FAILED\n"
        "=====================\n"
        f"{result.get('message', 'Unknown error')}"
    )


# ============================================================
# SERVER START
# ============================================================

if __name__ == "__main__":
    mcp.run()