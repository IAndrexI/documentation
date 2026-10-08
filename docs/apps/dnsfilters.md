# DNSfilters Automated Blocklist CI/CD

An automated pipeline compiling, deduplicating, and validating hundreds of thousands of domain rules for network-wide privacy protection and telemetry blocking on AdGuard Home.

---

## 1. Automated CI/CD Workflow

```mermaid
flowchart TD
    ScheduledTrigger["⏰ Daily Scheduled Trigger (GitHub Actions)"] --> FetchSources["Fetch Upstream Threat & Telemetry Feeds"]
    FetchSources --> Ingestion["Raw Feed Ingestion (350,000+ Domains)"]
    Ingestion --> Dedupe["Deduplication & Regex Syntax Normalizer"]
    Dedupe --> FalsePositives["False-Positive Filter & Allowlist Check"]
    FalsePositives --> BuildOptimized["Compile Optimized AdGuard Blocklist"]
    BuildOptimized --> DeployRelease["Tag Release & Deploy to Edge CDN"]
    DeployRelease --> AdGuard["AdGuard Home Sync (Proxmox LXC 102)"]
```

---

## 2. Key Performance Metrics

* **Domain Throughput:** 350,000+ domain entries processed in under 45 seconds.
* **Latency Overhead:** Zero network latency impact via native local DNS cache lookups.
* **Network Coverage:** Protects all IoT devices, Smart TVs, gaming consoles, and Proxmox containers across Gigabit LAN.
