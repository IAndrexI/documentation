# Soulseek & Navidrome Lossless Audio Hub

An automated private music streaming pipeline linking a headless Soulseek daemon (`slskd`) to a Navidrome streaming server through shared Proxmox storage mountpoints.

---

## 1. Storage & Pipeline Topology

```mermaid
flowchart LR
    subgraph CT105["Proxmox LXC 105: slskd"]
        Soulseek["Headless Soulseek Daemon"]
        Downloader["Automated FLAC Ingestion"]
    end

    subgraph HostZFS["ZFS Storage Pool (Host)"]
        MusicStorage[("/mnt/tank/music - Lossless FLAC Archive")]
    end

    subgraph CT103["Proxmox LXC 103: Navidrome"]
        Scanner["Navidrome Tag & Library Scanner"]
        Streamer["Subsonic Streaming Server"]
    end

    subgraph Clients["Playback Clients"]
        Mobile["Feishin / Symfonium (Mobile)"]
        Desktop["Desktop Hi-Fi Client (ASIO)"]
    end

    Soulseek --> Downloader
    Downloader -->|Writes Audio| MusicStorage
    MusicStorage -->|Direct Host Bind Mount mp0| Scanner
    Scanner --> Streamer
    Streamer -->|Lossless 24-bit Stream| Clients
```

---

## 2. Proxmox Shared Mountpoint Architecture

Shared storage avoids network overhead (NFS/SMB) by mounting directly at the hypervisor kernel level:

```ini
# Proxmox LXC Container Configuration (/etc/pve/lxc/103.conf)
mp0: /mnt/tank/music,mp=/opt/navidrome/music,ro=0
```
