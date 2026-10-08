# Security, Envelope Encryption & Key Vault

Protutech implements a layered cryptographic architecture protecting application source code, credentials, and persistent data at rest and in transit.

---

## 1. Envelope Encryption Architecture (Key Wrapping)

```mermaid
flowchart TD
    subgraph Layer1["Layer 1: Protected Assets"]
        Apps["Web Applications, Code & Persistent Secrets"]
    end

    subgraph Layer2["Layer 2: DEK (Data Encryption Key)"]
        DEK["AES-256-GCM Master Key & JWT Tokens"]
        DEK -->|Encrypts & Signs| Apps
    end

    subgraph Layer3["Layer 3: KEK (Key Encrypting Key)"]
        Passphrase["Master Passphrase (protutech2026)"]
        Passphrase -->|PBKDF2 SHA-512 (100,000 Rounds)| KEK["Key Encrypting Key"]
        KEK -->|AES-256-GCM Envelope Encryption| EncBlob["protutech_vault_keys.enc (Ciphertext Envelope)"]
    end

    EncBlob -->|Replicated across 5 drives| Backups[("Multi-Drive Targets: C:, E:, X:, Y:, Z:")]
```

---

## 2. Multi-Drive Redundancy & Zero-Plaintext Policy

All external drive backups (`E:`, `X:`, `Y:`, `Z:`) store **strictly authenticated AES-256-GCM ciphertext**. Plaintext secrets are purged from external storage volumes, preventing credential compromise if a physical disk is removed or mounted on an untrusted device.
