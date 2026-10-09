# Protutech Engineering Documentation

Welcome to the internal engineering architecture and technical documentation portal for the **Protutech Ecosystem**.

This documentation site provides deep architectural breakdowns, system topologies, component data flows, and code walkthroughs for all self hosted homelab applications and developer platforms.

---

## ⬡ Ecosystem Architecture & Topology

<img src="assets/system-topology.svg" alt="Protutech Enterprise Homelab Architecture" class="overview-architecture-img" />

```mermaid
graph TD
    User["User / Client (Web & Mobile)"] -->|Cloudflare Argo Tunnel| CF["Cloudflare Zero Trust Edge"]
    
    subgraph ProxmoxVE["Proxmox VE 9.2.11 Hypervisor Node"]
        CF --> NginxIngress["Reverse Proxy & SSL Gateway"]
        
        subgraph LXC_Core["LXC 100: Core Services"]
            NginxIngress --> Dash["ProtutechDash (App Launcher)"]
            NginxIngress --> Docs["Docs Portal (MkDocs Material)"]
        end

        subgraph LXC_Gaming["LXC 101: Gaming & Tools"]
            NginxIngress --> CS2["CS2Nades (Vue 3 + WebSocket)"]
            NginxIngress --> Pelican["Pelican Game Panel (Wings)"]
        end

        subgraph LXC_Security["LXC 102: Security & Identity"]
            NginxIngress --> VW["Vaultwarden (Bitwarden Safe)"]
            NginxIngress --> AG["AdGuard Home DNS (DNSfilters)"]
        end

        subgraph LXC_Data["LXC 103: Storage & Media"]
            NginxIngress --> Seafile["Seafile Cloud Drive"]
            NginxIngress --> Navi["Navidrome + Soulseek FLAC"]
        end

        subgraph LXC_AI["LXC 104: AI & Compute"]
            NginxIngress --> aiVault["aiVault (OpenWebUI)"]
        end
    end

    subgraph GPU_Node["Dedicated Workstation Node"]
        aiVault -->|Low Latency LAN 2.5GbE| Ollama["Ollama CUDA Daemon"]
        Dash -->|Custom URI protutech://| Bridge["Local Companion Daemon"]
    end
```

---

## ⬡ Quick Navigation

<div class="grid cards" markdown>

-   ▸ **Protutech Suite Dashboard**

    ---

    Unified cross platform Adobe Creative Cloud style launcher, periodic table cockpit, and custom protocol dispatcher.

    [▸ View Architecture](apps/protutechdash/index.md)

-   ▸ **CS2 Tactical Stratbook**

    ---

    Realtime interactive tactical whiteboard, vector trajectory physics engine, and lineup sync for Counter-Strike 2.

    [▸ View Breakdown](apps/cs2nades/index.md)

-   ▸ **ProtutechChat & Voice Engine**

    ---

    Decentralized Matrix communication hub paired with studio grade LiveKit WebRTC audio and Electron host.

    [▸ View Platform](apps/protutechchat/index.md)

-   ▸ **aiVault & Ollama Pipeline**

    ---

    Distributed local LLM pipeline routing containerized OpenWebUI to remote workstation GPU compute with Qdrant vector memory.

    [▸ View Pipeline](apps/aivault/index.md)

-   ▸ **Security & Envelope Encryption**

    ---

    Double layer AES-256-GCM envelope encryption, client side anti inspection guards, and multidrive backups.

    [▸ View Security Model](infra/security.md)

-   ▸ **Source Code Deep Dive**

    ---

    File by file technical walkthroughs explaining key lines of code, algorithms, and protective architecture.

    [▸ Explore Source Files](code/index.md)

</div>

---

## ⬡ Core Technical Specifications

| Metric / Layer | Specification |
| :--- | :--- |
| **Virtualization** | Proxmox VE 9.2.11 bare metal cluster with unprivileged Debian LXC microservices |
| **Storage Engine** | ZFS Pooled Storage with atomic snapshots and cross-container bind mounts (`mp0`) |
| **Remote Ingress** | Cloudflare Argo Zero Trust Tunnels (Zero open public inbound router ports) |
| **Frontend Frameworks** | Vue.js 3, TypeScript, Vite, Vanilla ESNext, Tailwind CSS |
| **Backend Daemons** | Node.js Express 5, Python 3 RPC Daemons, Go (Wings), Socket.IO WebSockets |
| **Availability Target** | 99.98% cluster uptime with systemd watchdog auto recovery |
