# aiVault & Distributed Local LLM Pipeline

A hybrid private LLM compute architecture connecting containerized OpenWebUI instances on Proxmox LXC with dedicated high-performance workstation GPU compute nodes running Ollama over low-latency 2.5GbE LAN.

---

## 1. Pipeline Architecture

```mermaid
graph TD
    Client["User Query (Browser / Mobile)"] --> OpenWebUI["OpenWebUI Interface (Proxmox LXC 104)"]
    OpenWebUI -->|LAN Request / 2.5GbE| Auth["mTLS / LAN Firewall Filter"]
    Auth --> OllamaServer["Dedicated GPU Compute Node (RTX GPU)"]
    OllamaServer --> ModelWeights["Quantized GGUF Models (Llama 3, DeepSeek, Qwen)"]
    ModelWeights --> InferenceEngine["CUDA / Tensor Core Acceleration"]
    InferenceEngine -->|Streaming Token Response| OpenWebUI
    OpenWebUI -->|WebSocket Token Stream| Client
```

---

## 2. Infrastructure Highlights

* **100% Data Sovereignty:** Zero queries leave the local physical network.
* **Separation of Concerns:** The web UI runs in an unprivileged, lightweight container; the inference engine runs directly bare-metal on CUDA hardware.
* **Network Speed:** Sub-1ms latency transfer between host and container across 2.5GbE switch routing.
