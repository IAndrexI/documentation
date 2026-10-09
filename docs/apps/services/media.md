# Navidrome & Soulseek Lossless Audio Pipeline

The Protutech audio infrastructure provides sovereign, decentralized, studio-quality music acquisition, indexing, and multi-device streaming. It replaces third-party commercial music subscription platforms with a private lossless streaming engine operating directly on Proxmox VE. The system pairs **Navidrome** (written in Go with SQLite caching) with **slskd** (a headless Soulseek P2P daemon), automated acoustic fingerprinting via **Beets**, and on-the-fly multi-threaded transcoding.

---

## 1. End-to-End Pipeline Architecture

```mermaid
graph TD
    ClientMobile["Mobile Device (Substreamer / Amperfy / Feishin)"]
    ClientDesktop["Desktop Workstation (Native Music Player / Web)"]

    subgraph ProxmoxMediaNode["Proxmox Media Node (LXC 103)"]
        Slskd["slskd Daemon (Soulseek P2P Engine / Port 5030)"]
        Watchdir["Ingestion Watchdir (/var/lib/slskd/downloads)"]
        Beets["Beets Audio Ingestion & AcoustID Fingerprinter"]
        
        Slskd -->|Completed FLAC Downloads| Watchdir
        Watchdir -->|inotifywait Event Trigger| Beets
        
        subgraph ZFSPool["ZFS Persistent Storage (/music)"]
            MusicDataset["ZFS Dataset: tank-zfs/music (recordsize=1M)"]
            MusicDataset --> ArtistDirs["/music/Artist/Year - Album/Track.flac"]
        end

        Beets -->|Tag, Clean & Move| MusicDataset
        
        subgraph NavidromeEngine["Navidrome Core Engine (Go)"]
            Scanner["Filesystem Scanner & Metadata Indexer"]
            SubsonicAPI["Subsonic REST API v1.16 Gateway"]
            Transcoder["FFmpeg Transcoder Pipeline (Opus / AAC / Passthrough)"]
            
            MusicDataset --> Scanner
            Scanner --> SQLite["Local SQLite Cache (navidrome.db)"]
            SQLite <--> SubsonicAPI
            MusicDataset --> Transcoder --> SubsonicAPI
        end
    end

    ClientMobile <-->|Subsonic 2.0 API (Transcoded Opus 160k)| SubsonicAPI
    ClientDesktop <-->|Subsonic 2.0 API (Bit-Perfect FLAC 24/96)| SubsonicAPI
```

---

## 2. P2P Ingestion Engine (`slskd` & Soulseek Protocol)

To acquire rare master recordings and high resolution audio without web scrapers or third-party download lockers, we deploy `slskd`, a modern containerized implementation of the decentralized Soulseek peer-to-peer file sharing protocol:

### Technical Ingestion Characteristics

| Parameter | Configuration | Engineering Rationale |
| :--- | :--- | :--- |
| **Peer Protocol** | Soulseek Distributed Mesh | Direct socket-to-socket transfers between decentralized peer nodes |
| **Default Ports** | `5030/tcp` (Web UI), `50300/tcp` (Peer Listening) | Static port mapping through Cloudflare tunnel or private wireguard |
| **Format Filtering** | Strictly `.flac`, `.wav` (Regex: `\.(flac\|wav)$`) | Filters out lossy MP3/AAC uploads automatically |
| **Download Staging** | Local NVMe SSD scratch directory | Prevents fragmentation on high-capacity spinning disk pools |
| **Transfer Throttling** | 100 Mbps downstream / 20 Mbps upstream | Preserves bandwidth for low latency gaming and voice servers |

---

## 3. Acoustic Fingerprinting & Automated Cataloging (`Beets`)

Once tracks finish downloading, an automated daemon executes **Beets** to inspect file integrity and correct metadata before the files enter the public music library:

### Ingestion Workflow
1. **Chromaprint Waveform Analysis**: Calculates an AcoustID hash directly from the audio waveform. Even if an upload has incorrect ID3 tags or misnamed files, the acoustic fingerprint matches the master recording against the MusicBrainz database.
2. **Lossless Verification**: Uses `flac -t` to test the internal MD5 checksum of every compressed audio frame. Corrupted transfers are immediately rejected.
3. **Canonical Directory Normalization**: Reorganizes files into a deterministic directory structure:

```text
/music/
└── Pink Floyd/
    └── (1973) The Dark Side of the Moon [FLAC 24-96]/
        ├── 01 - Speak to Me.flac
        ├── 02 - Breathe.flac
        ├── cover.jpg
        └── album.nfo
```

---

## 4. Subsonic REST API v1.16 Implementation (Navidrome)

Navidrome provides complete compatibility with the battle-tested **Subsonic API**, enabling connection with hundreds of third-party mobile apps (including Substreamer, Feishin, Symfonium, and Amperfy):

### Core API Wire Contracts

#### 1. Authentication Handshake (`/rest/ping.view`)
Clients authenticate using MD5 salt hashing to avoid transmitting plain text passwords across the wire:
$$\text{token} = \operatorname{md5}(\text{password} + \text{salt})$$

```http
GET /rest/ping.view?u=andrew&t=c9281a7b04424f119a18xxxxxxxxxxxx&s=3b8e4f21&v=1.16.1&c=feishin&f=json HTTP/1.1
Host: music.protutech.vip
```

#### 2. Streaming Audio Track (`/rest/stream.view`)
```http
GET /rest/stream.view?id=4820a&maxBitRate=160&format=opus HTTP/1.1
Host: music.protutech.vip
```

If the client requests an uncompressed stream on a local network connection, Navidrome streams the raw FLAC bytes directly with HTTP range requests (`Accept-Ranges: bytes`), enabling instant scrubbing and zero quality degradation.

---

## 5. Dynamic On-the-Fly FFmpeg Transcoding Pipeline

When streaming over cellular networks, transmitting raw $96\text{kHz} / 24\text{-bit}$ FLAC files consumes excessive mobile data (over $30\text{ MB}$ per track). Navidrome transparently pipe-transcodes audio using multi-threaded FFmpeg:

```bash
# Navidrome Internal Transcoding Command Execution
ffmpeg -i /music/Artist/Album/track.flac \
  -map 0:0 \
  -v 0 \
  -b:a 160k \
  -c:a libopus \
  -vbr on \
  -compression_level 10 \
  -f opus -
```

### Audio Quality & Bandwidth Efficiency Matrix

| Stream Mode | Source Format | Wire Codec | Bitrate | 5-Minute Song Transfer |
| :--- | :--- | :--- | :--- | :--- |
| **Studio Master (LAN / Wi-Fi)** | FLAC 24-bit / 96kHz | Bit-Perfect FLAC | $\approx 3,200\text{ kbps}$ | $120.0\text{ MB}$ |
| **Standard Lossless (LAN)** | FLAC 16-bit / 44.1kHz | Bit-Perfect FLAC | $\approx 850\text{ kbps}$ | $31.8\text{ MB}$ |
| **Mobile Cellular High** | Any Lossless Input | Opus VBR (libopus) | $160\text{ kbps}$ | $6.0\text{ MB}$ (95% reduction) |
| **Mobile Cellular Low** | Any Lossless Input | Opus VBR (libopus) | $96\text{ kbps}$ | $3.6\text{ MB}$ (97% reduction) |

---

## 6. ZFS Dataset Tuning for Audio Streaming

Because media streaming involves sequential reads of large audio files rather than random 4KB database mutations, the underlying ZFS pool dataset is tuned specifically for streaming workloads:

```bash
# Proxmox Host Dataset Configuration for Media
zfs set recordsize=1M tank-zfs/music
zfs set atime=off tank-zfs/music
zfs set compression=zstd-3 tank-zfs/music
```

- **`recordsize=1M`**: Matching the record size to 1 MB allows the storage controller to read entire audio tracks in a fraction of the I/O operations required by standard 128 KB blocks, reducing drive head thrashing on spinning disks.
- **`atime=off`**: Disables access-time metadata writes every time a track is listened to, preventing unnecessary write wear.
- **Cross-Container Bind Mount**: The dataset is mounted directly into container 103 via Proxmox mountpoint configuration (`mp0: /tank/music,mp=/music`), avoiding network filesystem (NFS/SMB) latency overhead.
