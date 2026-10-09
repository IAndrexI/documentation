# Architectural Concepts & Standards Reference

This section catalogs the core mathematical models, cryptographic standards, networking protocols, and kernel subsystems implemented across the Protutech ecosystem. Rather than treating our services as black boxes, we document the underlying specifications, wire formats, and engineering trade-offs that govern their runtime behavior.

Every concept listed here links directly to its standalone deep dive page. Throughout the documentation, key terms are styled with an interactive preview: hovering over any highlighted concept (e.g. <a href="envelope-encryption.md" class="pt-concept" data-tooltip="AES-256-GCM authenticated cipher wrapping with PBKDF2 key derivation.">Envelope Encryption</a>) for at least three seconds reveals a concise architectural summary without leaving your reading position.

---

## Core Technical Concepts

<div class="grid cards" markdown>

-   __Cryptographic Ciphers & Envelope Storage__
    
    ---
    
    Authentication tag validation, per-secret Data Encryption Keys (DEKs), Key Encryption Keys (KEKs), and tamper-evident storage using NIST SP 800-38D standards.
    
    [Read Envelope Encryption Deep Dive](envelope-encryption.md)

-   __Ballistic Trajectory & Bézier Physics__
    
    ---
    
    Mathematical interpolation of grenade throws, Bernstein cubic polynomials, Hammer unit projection matrices, and collision vector estimation in CS2.
    
    [Read Ballistics & Physics Deep Dive](cubic-bezier-physics.md)

-   __Matrix Federated Protocol & State Engines__
    
    ---
    
    Decentralized event graphs, State Resolution v2 DAG sorting, MSC3575 Sliding Sync subscriptions, and immutable `mxc://` content addressable storage.
    
    [Read Matrix Protocol Deep Dive](matrix-protocol.md)

-   __WebRTC Selective Forwarding Units (SFU)__
    
    ---
    
    Selective audio/video forwarding, zero-transcode forwarding topologies, adaptive dynacast streams, and Windows WASAPI low-latency loopback audio capture.
    
    [Read WebRTC & SFU Deep Dive](webrtc-sfu.md)

-   __HNSW Graphs & Vector Embeddings__
    
    ---
    
    Hierarchical Navigable Small World geometric graphs, cosine metric distance calculations, Qdrant payload filtering, and sub-millisecond nearest neighbor search.
    
    [Read HNSW & Embeddings Deep Dive](vector-embeddings-hnsw.md)

-   __LXC Namespaces & Hypervisor Isolation__
    
    ---
    
    Unprivileged container isolation, UID/GID remapping (`UID 0 -> 100000`), Linux cgroups v2 resource accounting, and ZFS recordsize tuning on Proxmox VE.
    
    [Read Proxmox Virtualization Deep Dive](proxmox-virtualization.md)

</div>

---

## Standards, RFCs & Engineering Citations

Our architecture adheres to established academic research and international specifications:

| Concept / Domain | Formal Standard / Paper | Primary RFC / Spec | Implementation Target |
| :--- | :--- | :--- | :--- |
| **Authenticated Ciphers** | NIST Special Publication 800-38D | RFC 5116 / RFC 2898 | `src/security-guard.js`, `envelope_manager.js` |
| **Federated Messaging** | Matrix Foundation Specification | Matrix Client-Server API v1.11 | `src/services/matrix.ts` |
| **Low Latency Media** | W3C WebRTC 1.0 & IETF RFC 8825 | RFC 7675 (STUN) / RFC 8866 (SDP) | `src/services/livekit.ts` |
| **Vector Similarity** | Malkov & Yashunin (IEEE TPAMI 2018) | HNSW Graph Indexing | `aiVault` Qdrant Engine |
| **Kinematic Curves** | P. Bézier / Bernstein Polynomials | Valve Hammer Map View System | `useCanvas.ts`, `coordinateMapper.ts` |
| **Container Security** | Linux Kernel User Namespaces | POSIX 1003.1 / cgroups v2 | Proxmox VE 9.2 LXC Containers |

---

## Interactive Concept Tooltips

Throughout our documentation, technical keywords are marked with a cyan dotted underline. If you are reading about an architecture and encounter a concept you want a refresher on, you have two options:

1. **Hover for 3 Seconds**: Hold your mouse cursor over the dotted term. An architectural overview tooltip will smoothly reveal itself after a 3-second delay, preventing accidental popups while reading.
2. **Direct Click**: Click the underlined term to immediately jump to its dedicated technical specification page in this reference library.
