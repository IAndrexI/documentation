# Source Code Deep Dive: `aiVault/server.py`

## File Metadata

- **Subsystem:** aiVault Episodic Vector Memory Gateway
- **Path:** `aiVault/server.py`
- **Language / Runtime:** Python 3 (FastAPI / ASGI / Mem0 SDK / Qdrant)
- **Primary Responsibility:** Exposes an asynchronous REST API that extracts semantic facts from conversations, generates vector embeddings via Ollama, and persists them into Qdrant vector database.

---

## General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `server.py` provides long term memory for your private AI models:
    
    1. **Fact Extraction:** When you chat with an AI model, your message is parsed by Mem0 using an offline LLM to extract key personal facts and homelab configurations.
    2. **Vector Embeddings:** It passes extracted facts to Ollama running `nomic-embed-text`, generating dense 768-dimensional mathematical coordinates.
    3. **Qdrant Storage:** Points are stored in the Rust-powered Qdrant vector database using HNSW graph indexing.
    4. **Semantic Retrieval:** When you ask a question later, the server converts your query into a vector and finds the closest past facts using cosine similarity in milliseconds, allowing the AI to remember you across reboots.

---

## Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full architectural details, data structures, and line by line breakdown required to understand and recreate the vector memory server from scratch.

    ### Vector Ingestion & Search Pipeline
    ```mermaid
    graph TD
        ClientReq["Incoming HTTP Request (/v1/memories or /v1/memories/search)"] --> FastAPIRoute["FastAPI Route Handler"]
        
        subgraph Mem0Orchestrator["Mem0 Engine Initialization"]
            FastAPIRoute --> Mem0Config["Config: Vector Store (Qdrant) + Embedder (Ollama nomic-embed-text)"]
            Mem0Config --> MemoryInstance["Memory.from_config(config)"]
        end

        subgraph Operations["Vector Operations"]
            MemoryInstance -->|add| ExtractFacts["Ollama generates 768-dim float32 embeddings -> Upsert into Qdrant"]
            MemoryInstance -->|search| CosineMatch["Qdrant HNSW Nearest Neighbor Search -> Return top scoring facts"]
        end
    ```

    ---

    ### 1. Vector Store & Embedder Initialization (Lines 11–45)
    ```python linenums="11"
    config: Dict[str, Any] = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "host": os.getenv("QDRANT_HOST", "agent_qdrant"),
                "port": int(os.getenv("QDRANT_PORT", "6333")),
            }
        }
    }

    if llm_provider == "ollama":
        ollama_url = os.getenv("OLLAMA_BASE_URL", "http://agent_ollama:11434")
        config["llm"] = {
            "provider": "ollama",
            "config": {
                "model": os.getenv("OLLAMA_LLM_MODEL", "llama3.2:1b"),
                "ollama_base_url": ollama_url,
            }
        }
        config["embedder"] = {
            "provider": "ollama",
            "config": {
                "model": os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text"),
                "ollama_base_url": ollama_url,
            }
        }

    memory = Memory.from_config(config)
    ```
    - **Lines 11–19**: Injects Qdrant vector configuration targeting internal container hostname `agent_qdrant` on port `6333`.
    - **Lines 21–36**: Sets the LLM and embedder provider to Ollama. Using `nomic-embed-text` produces dense 768-dimensional embeddings offline without cloud dependencies.
    - **Line 45 (`Memory.from_config`)**: Initializes Mem0's internal pipeline for entity resolution, conflict management, and automated deduplication.

    ---

    ### 2. Fact Extraction & Vector Storage Endpoints (Lines 58–77)
    ```python linenums="58"
    @app.post("/v1/memories")
    def add_memory(req: AddMemoryRequest):
        try:
            return memory.add(
                req.messages,
                user_id=req.user_id,
                agent_id=req.agent_id,
                metadata=req.metadata
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/v1/memories/search")
    def search_memory(req: SearchMemoryRequest):
        try:
            return memory.search(
                req.query,
                user_id=req.user_id,
                agent_id=req.agent_id
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
    ```
    - **Lines 58–63 (`add_memory`)**: Ingests new user queries or chat history. Mem0 prompts the configured LLM to extract persistent facts, vectors them, and upserts points into Qdrant.
    - **Lines 72–77 (`search_memory`)**: Calculates the query vector and executes an approximate nearest neighbor search across Qdrant's HNSW index, returning relevant context to inject into LLM prompts.

---

## Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Internal similarity score thresholds, embedding quantization models, and semantic clustering algorithms are isolated within the private container network. External clients cannot directly inspect low level vector coordinates or internal Qdrant collections.
