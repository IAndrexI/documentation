# proxDiscord & Proxmox RPC Daemon

A background daemon bridging Proxmox VE hypervisor vitals, cluster metrics, and gaming activity directly into Discord Rich Presence with an administrative web telemetry dashboard.

---

## 1. Daemon Architecture

```mermaid
flowchart LR
    subgraph Host["🖥️ Workstation / Proxmox"]
        PVE["Proxmox VE REST API (:8006)"]
        Games["Running Game Detection (Process API)"]
    end

    subgraph Daemon["⚙️ proxDiscord Daemon"]
        RPC["proxmox_rpc.py Core Engine"]
        Cache["Metrics Cache & Giveaway Watcher"]
        WebDash["Web Control Dashboard (:8090)"]
    end

    subgraph Discord["💬 Discord Client & Edge"]
        IPC["Local Discord IPC Pipe"]
        Worker["Cloudflare Worker Relay"]
    end

    PVE -->|Polls CPU, RAM, VMs| RPC
    Games -->|Scans active processes| RPC
    RPC --> Cache
    RPC --> WebDash
    RPC -->|Pushes Rich Presence| IPC
    RPC -->|Webhooks status| Worker
```

---

## 2. Core Operational Metrics

* **Polling Cadence:** Adaptive 15-second metric aggregation loop.
* **Telemetry Endpoints:** Proxmox Node Status (`/api2/json/nodes`), Container Resource Limits (`/api2/json/nodes/{node}/lxc`), Free Games API cache (`free_games_cache.json`).
* **Ingress Protection:** Secured via local binding and Cloudflare Worker token authentication.
