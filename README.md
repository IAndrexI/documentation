# Protutech Engineering Documentation

[![MkDocs Material](https://img.shields.io/badge/Material_for_MkDocs-v9.7-blue?logo=materialformkdocs)](https://squidfunk.github.io/mkdocs-material/)
[![Proxmox VE](https://img.shields.io/badge/Hosted_on-Proxmox_VE_9.2-E57000?logo=proxmox)](https://www.proxmox.com/)
[![Cloudflare Zero Trust](https://img.shields.io/badge/Security-Cloudflare_Argo-F38020?logo=cloudflare)](https://cloudflare.com/)

Central technical architecture, system topologies, component data flows, and code breakdowns for all applications in the **Protutech Ecosystem**.

---

## Applications Covered

* **[Protutech Suite Dashboard](docs/apps/protutechdash.md)**: Unified launcher, periodic table cockpit, and custom protocol dispatcher (`protutech://`).
* **[CS2 Tactical Stratbook](docs/apps/cs2nades.md)**: 2D vector whiteboard, lineup library, and real-time multiplayer drawing sync.
* **[proxDiscord & RPC Daemon](docs/apps/proxdiscord.md)**: Background Python daemon bridging Proxmox telemetry into Discord Presence.
* **[aiVault Local LLM Engine](docs/apps/aivault.md)**: Distributed LLM pipeline connecting OpenWebUI to remote workstation GPU inference via 2.5GbE LAN.
* **[DNSfilters CI/CD](docs/apps/dnsfilters.md)**: Automated ingestion and deduplication of 350,000+ domain blocklists for AdGuard Home.
* **[Pelican Game Server Panel](docs/apps/pelican.md)**: Next-gen container orchestration node and Wings daemon.
* **[Soulseek & Navidrome Audio](docs/apps/media.md)**: Automated FLAC ingestion and lossless streaming across shared Proxmox mountpoints.

---

## Local Development

### 1. Requirements
* Python 3.10+
* `pip install mkdocs-material mkdocs-minify-plugin`

### 2. Live Preview Server
```bash
python -m mkdocs serve
```
Open **`http://localhost:8000`** in your browser. Live hot-reloading is active.

### 3. Build Static Site
```bash
python -m mkdocs build --clean
```

---

## Proxmox Deployment

### Option 1: Turnkey Proxmox Host Shell Script
Run directly in your Proxmox host shell:
```bash
curl -fsSL https://raw.githubusercontent.com/IAndrexI/documentation/main/deploy-proxmox.sh | bash
```

### Option 2: Docker Compose
```bash
docker compose up -d
```
Runs at `http://localhost:8085`.

---

## License
Copyright © 2026 Andrew (Protutech / IAndrexI). Built for personal homelab architecture and engineering documentation.
