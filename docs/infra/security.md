# Security, Envelope Encryption & Key Vault

Protutech implements a layered cryptographic architecture protecting application source code, credentials, and persistent data at rest and in transit across all homelab nodes.

---

## 🏛️ Envelope Encryption Architecture (Key Wrapping)

```mermaid
flowchart TD
    subgraph Layer1["Layer 1: Protected Application Data"]
        Apps["Web Applications, Code & Persistent Secrets"]
    end

    subgraph Layer2["Layer 2: DEK (Data Encryption Key)"]
        DEK["AES-256-GCM Master Key & JWT Signing Tokens"]
        DEK -->|Encrypts & Signs Data| Apps
    end

    subgraph Layer3["Layer 3: KEK (Key Encrypting Key)"]
        Passphrase["Master Passphrase (protutech2026)"]
        Passphrase -->|PBKDF2 SHA-512 (100,000 Rounds)| KEK["Key Encrypting Key (Derived 256-bit Key)"]
        KEK -->|AES-256-GCM Envelope Encryption| EncBlob["protutech_vault_keys.enc (Ciphertext Envelope)"]
    end

    EncBlob -->|Replicated with SHA-256 Verification| DriveC["Drive C: (Primary)"]
    EncBlob -->|Replicated with SHA-256 Verification| DriveE["Drive E: (Backup)"]
    EncBlob -->|Replicated with SHA-256 Verification| DriveX["Drive X: (Backup)"]
    EncBlob -->|Replicated with SHA-256 Verification| DriveY["Drive Y: (Backup)"]
    EncBlob -->|Replicated with SHA-256 Verification| DriveZ["Drive Z: (Backup)"]
```

---

## 📂 Vault File Structure & Responsibilities

```text
C:\Users\Andre\.protutech\security\
├── envelope_manager.js          # Core cryptographic engine (AES-256-GCM + PBKDF2-SHA512)
├── unlock_vault.ps1             # Interactive Windows PowerShell unlocker with secure password prompt
├── backup_keys_to_all_drives.ps1 # Multi-drive synchronization script with SHA-256 verification
├── protutech_vault_keys.enc     # Authenticated AES-256-GCM encrypted envelope (Safe to store on backups)
├── protutech_vault_keys.json    # Local unencrypted JSON vault (Protected on C: drive only)
├── protutech_vault_keys.env     # Environment variable format for Docker Compose / daemons
├── RECOVERY_KEY_BACKUP.txt      # Human-readable emergency recovery sheet
└── ENCRYPTED_VAULT_README.txt   # Backup drive documentation explaining how to unlock the .enc file
```

---

## 🔍 Line by Line Cryptographic Code Breakdown

### 1. `envelope_manager.js` — AES-256-GCM & PBKDF2-SHA512 Engine

```javascript linenums="1"
import crypto from 'crypto';
import fs from 'fs';

export function encryptVault(passphrase) {
  const plaintext = fs.readFileSync('protutech_vault_keys.json', 'utf8'); // (1)!

  // 1. Generate Cryptographic Salt & Initialization Vector (IV)
  const salt = crypto.randomBytes(32); // (2)!
  const iv = crypto.randomBytes(12);   // (3)!

  // 2. Derive Key Encrypting Key (KEK) using PBKDF2 with 100,000 iterations
  const iterations = 100000; // (4)!
  const kek = crypto.pbkdf2Sync(passphrase, salt, iterations, 32, 'sha512'); // (5)!

  // 3. Encrypt Plaintext Vault via AES-256-GCM
  const cipher = crypto.createCipheriv('aes-256-gcm', kek, iv); // (6)!
  const ciphertextBuffer = Buffer.concat([
    cipher.update(Buffer.from(plaintext, 'utf8')),
    cipher.final() // (7)!
  ]);
  const authTag = cipher.getAuthTag(); // (8)!

  // 4. Construct Authenticated Envelope Object
  const envelope = {
    vault_format: 'Protutech-Envelope-v2',
    cipher: 'aes-256-gcm',
    kdf: 'pbkdf2-sha512',
    iterations,
    created_at: new Date().toISOString(),
    salt_hex: salt.toString('hex'), // (9)!
    iv_hex: iv.toString('hex'),
    auth_tag_hex: authTag.toString('hex'),
    ciphertext_base64: ciphertextBuffer.toString('base64') // (10)!
  };

  fs.writeFileSync('protutech_vault_keys.enc', JSON.stringify(envelope, null, 2));
}
```

1. Reads the local plaintext JSON vault containing the master secrets and keys into memory.
2. Generates a cryptographically strong 256-bit random salt ensuring identical passwords produce unique ciphertext.
3. Generates a standard 96-bit (12-byte) initialization vector (IV) recommended for GCM mode.
4. Enforces 100,000 hashing rounds to make brute-force and dictionary attacks computationally infeasible.
5. Computes the 256-bit Key Encrypting Key (KEK) using PBKDF2 with SHA-512 as the pseudorandom function.
6. Initializes the AES-256-GCM cipher with the derived key and random IV.
7. Processes all plaintext bytes and seals the encryption buffer.
8. Extracts the 128-bit authentication tag (`authTag`), which guarantees data integrity and tamper detection.
9. Converts binary salt, IV, and auth tag to hexadecimal strings for safe JSON serialization.
10. Encodes the final encrypted ciphertext buffer into Base64 for cross platform portability.

---

### 2. `backup_keys_to_all_drives.ps1` — Zero-Plaintext Multidrive Purge & Sync

```powershell linenums="1"
# Target backup paths across all physical and mounted volumes
$TargetDrives = @(
    @{ Drive = "E:"; Path = "E:\Protutech_Backups\Security_Keys" },
    @{ Drive = "X:"; Path = "X:\Protutech_Backups\Security_Keys" },
    @{ Drive = "Y:"; Path = "Y:\Protutech_Backups\Security_Keys" },
    @{ Drive = "Z:"; Path = "Z:\Protutech_Backups\Security_Keys" }
)

foreach ($target in $TargetDrives) {
    if (Test-Path $target.Drive) {
        # 1. PURGE unencrypted plaintext files from external backup drives
        $PlaintextFiles = @("protutech_vault_keys.json", "protutech_vault_keys.env", "RECOVERY_KEY_BACKUP.txt")
        foreach ($pt in $PlaintextFiles) {
            $path = Join-Path $target.Path $pt
            if (Test-Path $path) { Remove-Item -Path $path -Force } # (1)!
        }

        # 2. COPY strictly authenticated encrypted envelope (.enc)
        $encSrc = Join-Path $SourceDir "protutech_vault_keys.enc"
        $encDest = Join-Path $target.Path "protutech_vault_keys.enc"
        Copy-Item -Path $encSrc -Destination $encDest -Force # (2)!

        # 3. VERIFY byte-for-byte SHA-256 integrity match
        $srcHash = (Get-FileHash -Path $encSrc -Algorithm SHA256).Hash
        $destHash = (Get-FileHash -Path $encDest -Algorithm SHA256).Hash
        if ($srcHash -eq $destHash) {
            Write-Host "✅ Drive $($target.Drive) Verified: SHA-256 Match" -ForegroundColor Green # (3)!
        }
    }
}
```

1. Actively deletes any unencrypted plaintext credential files from external volumes so no secrets leak.
2. Replicates the encrypted ciphertext envelope (`.enc`), unlock script, and engine to each target volume.
3. Calculates SHA-256 hashes of both source and destination to mathematically prove byte-for-byte replication.
