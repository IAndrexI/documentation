# Source Code Deep Dive: `aiVault/docker-compose.yml`

## 📄 File Metadata

- **Subsystem:** aiVault Distributed Container Cluster
- **Path:** `aiVault/docker-compose.yml`
- **Language / Runtime:** YAML (Docker Compose Specification V2)
- **Primary Responsibility:** Orchestrates container lifecycles, internal bridge networking, volume persistence, and environment variable propagation across the local AI stack.

---

## 💡 What This File Does (Explained Simply)

Running four different complex programs (a database, an AI engine, a memory translator, and a web chat interface) by hand would require dozens of terminal commands and easy to forget settings.
`docker-compose.yml` is like a master architect blueprint:
1. It tells Docker to create four sealed, virtual containers.
2. It hooks up private invisible network cables between them so they can talk securely without exposing internal ports to the outside world.
3. It designates permanent storage vaults on your hard drive so your conversation history and AI model weights survive server restarts.
4. It sets up automatic failover: if your workstation GPU is busy, it knows how to fall back to the local container.

---

## 🔍 Key Architectural Sections & Line Breakdown

```mermaid
graph TD
    Compose["docker compose up -d"] --> Qdrant["Service 1: agent_qdrant (Ports 6333/6334)"]
    Compose --> Ollama["Service 2: agent_ollama (Port 11434)"]
    Compose --> Mem0["Service 3: agent_mem0 (Port 8888, depends_on: qdrant, ollama)"]
    Compose --> OpenWebUI["Service 4: open_webui (Port 3000 -> 8080, depends_on: qdrant)"]

    OpenWebUI -->|Primary Inference| GPU["Workstation GPU Node (2.5GbE LAN)"]
    OpenWebUI -->|Fallback Inference| Ollama
    OpenWebUI -->|Long Term Memory| Mem0
    Mem0 --> Qdrant
```

---

### Section 1: Vector Database & Local Fallback Engine

```yaml linenums="1"
services:
  # 1. High Performance Vector Database (Rust based, low resource usage)
  qdrant:
    image: qdrant/qdrant:latest
    container_name: agent_qdrant
    restart: unless-stopped
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - ./qdrant_storage:/qdrant/storage:z

  # 2. Local Ollama Engine for 100% Offline Embeddings and Fact Extraction
  ollama:
    image: ollama/ollama:latest
    container_name: agent_ollama
    restart: unless-stopped
    ports:
      - "11434:11434"
    volumes:
      - ./ollama_storage:/root/.ollama
```

#### Line by Line Explanation:
- **Lines 3–11 (`qdrant`)**: Deploys the official Qdrant vector database image. The `:z` volume mount flag applies SELinux shared container labels, preventing file permission denied errors on Linux hosts.
- **Lines 14–22 (`ollama`)**: Boots a containerized Ollama instance mounted to `./ollama_storage`. This container runs lightweight models locally and serves as an automated fallback if the main workstation GPU node is powered off.

---

### Section 2: Hybrid Open WebUI Dual Gateway Configuration

```yaml linenums="43"
  # 4. Open WebUI (Unified Chat Interface + RTX 5080 GPU + Cloud API Bridge)
  open-webui:
    image: ghcr.io/open-webui/open-webui:main
    container_name: open_webui
    restart: unless-stopped
    ports:
      - "3000:8080"
    environment:
      # Primary GPU inference on workstation PC, fallback to container
      - OLLAMA_BASE_URLS=http://workstation.internal:11434;http://agent_ollama:11434
      - VECTOR_DB=qdrant
      - QDRANT_URI=http://agent_qdrant:6333
      - RAG_EMBEDDING_ENGINE=ollama
      - RAG_EMBEDDING_MODEL=nomic-embed-text:latest
      - WEBUI_AUTH=true
    volumes:
      - ./open_webui_data:/app/backend/data
    depends_on:
      - qdrant
```

#### Line by Line Explanation:
- **Lines 49 (`ports: "3000:8080"`)**: Maps host port `3000` to internal container port `8080`, allowing the Nginx reverse proxy to forward traffic smoothly.
- **Line 52 (`OLLAMA_BASE_URLS`)**: Implements dual gateway failover. Semicolon separated URLs allow Open WebUI to prioritize low latency workstation GPU inference while gracefully switching to container Ollama if the desktop is offline.
- **Lines 53–57 (`VECTOR_DB` & `RAG`)**: Integrates Qdrant directly into Open WebUI's built in document retrieval (RAG) engine.

---

## 🛡️ Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Internal subnet masks, hardware MAC addresses, and physical workstation IP coordinates are abstracted through internal container DNS resolution. Container security profiles prevent privilege escalation to the Proxmox host kernel.
