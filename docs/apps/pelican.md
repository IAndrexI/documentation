# Pelican Game Server Panel & Node Daemon

A next-generation game server container orchestration node on Proxmox LXC providing sandboxed Docker runtimes for Minecraft, CS2, and Unturned dedicated servers.

---

## 1. Container & Daemon Architecture

```mermaid
graph TD
    User["Game Server Admin"] --> Panel["Pelican Web Panel (Proxmox LXC 101)"]
    Panel -->|gRPC / REST API| Wings["Wings Daemon (Go Runtime)"]
    Wings --> DockerEngine["Docker Engine (Isolated Sandboxes)"]
    
    subgraph Instances["Sandboxed Game Instances"]
        DockerEngine --> MC["Minecraft Paper Instance (Core Pinned)"]
        DockerEngine --> CS["CS2 Dedicated Server (Tick Stable)"]
        DockerEngine --> UN["Unturned Server Instance"]
    end

    Wings --> StoragePool["ZFS Storage Pool (Automated World Snapshots)"]
    Wings --> SFTP["Secure SFTP Bridge (Port 2022)"]
```

---

## 2. Resource Quotas & Isolation

* **Core Pinning:** CPU affinity pinning prevents game tick stutters during heavy background operations.
* **Storage Snapshots:** Daily atomic ZFS snapshots backup world and player state without taking servers offline.
