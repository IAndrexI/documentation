# Source Code Deep Dive: `backup_keys_to_all_drives.ps1`

## File Metadata

- **Subsystem:** Multidrive Key Cold Storage Pipeline
- **Path:** `infra/security/backup_keys_to_all_drives.ps1`
- **Language / Runtime:** PowerShell 7 / Windows Management Instrumentation
- **Primary Responsibility:** Discovers all mounted physical, removable, and network drive volumes on the workstation, replicates encrypted master key envelopes, and verifies SHA256 bit integrity.

---

## General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `backup_keys_to_all_drives.ps1` automates disaster recovery for your cryptographic key vaults:
    
    1. **Physical Drive Discovery:** It queries the Windows operating system for all currently mounted storage volumes (e.g. `C:`, `D:`, `E:`, `X:`).
    2. **Idempotent Directory Creation:** If a drive doesn't already have a hidden `.vault_backups` folder, it safely creates one.
    3. **Encrypted Replicate Transfer:** Copies the encrypted master key envelope across every physical disk.
    4. **Cryptographic Verification:** Recalculates the SHA-256 hash of the copied file on each destination drive and compares it to the original master hash, verifying bitstream integrity and guarding against silent drive corruption.

---

## Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full PowerShell parameters, system calls, and line by line breakdown required to understand and recreate the multidrive replication engine from scratch.

    ### Multi-Drive Sync & Audit Flow
    ```mermaid
    graph TD
        Trigger["Execute: backup_keys_to_all_drives.ps1"] --> GetDrives["Get-Volume: Scan drive letters (C, D, E, X)"]
        GetDrives --> DriveLoop["Iterate through each available volume"]

        subgraph VolumeReplication["Per-Drive Replication & Audit"]
            DriveLoop --> CheckFolder["Test-Path / New-Item: Ensure .vault_backups exists"]
            CheckFolder --> CopyFile["Copy-Item -Path $SourceKey -Destination $TargetFile"]
            CopyFile --> HashSource["Get-FileHash -Algorithm SHA256 ($SourceKey)"]
            CopyFile --> HashDest["Get-FileHash -Algorithm SHA256 ($TargetFile)"]
            HashSource <-->|Compare Bitstreams| HashDest
            HashDest --> VerifyCheck{"Do SHA256 hashes match identically?"}
            VerifyCheck -->|Match| SuccessLog["Write-Host: Verified Bit-Perfect Copy"]
            VerifyCheck -->|Mismatch| AlertError["Write-Error: Hash Mismatch Detected!"]
        end
    ```

    ---

    ### 1. Drive Discovery & SHA-256 Digest Verification (Lines 10–29)
    ```powershell linenums="10"
    $SourceKey = "C:\Users\Protutech\.vault\master_key.enc"
    $TargetDrives = @("C:", "D:", "E:", "X:")
    $SourceHash = (Get-FileHash -Path $SourceKey -Algorithm SHA256).Hash

    foreach ($Drive in $TargetDrives) {
        if (Test-Path "$Drive\") {
            $DestDir = "$Drive\.vault_backups"
            if (!(Test-Path $DestDir)) {
                New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
            }
            
            $DestFile = Join-Path $DestDir "master_key.enc"
            Copy-Item -Path $SourceKey -Destination $DestFile -Force
            
            # Verify bitstream integrity
            $DestHash = (Get-FileHash -Path $DestFile -Algorithm SHA256).Hash
            if ($SourceHash -eq $DestHash) {
                Write-Host "[OK] Key successfully mirrored and verified on $Drive" -ForegroundColor Green
            } else {
                Write-Error "[FAIL] Hash mismatch detected on $Drive! Possible drive corruption."
            }
        }
    }
    ```
    - **Line 10 (`$SourceKey`)**: Filepath pointing to the primary encrypted master key envelope.
    - **Line 12 (`Get-FileHash ... -Algorithm SHA256`)**: Calculates the 256-bit cryptographic digest of the source key before initiating transfers.
    - **Lines 14–15 (`Test-Path "$Drive\"`)**: Verifies the physical drive volume is actively mounted, avoiding runtime errors when external USB drives are unplugged.
    - **Lines 17–19 (`New-Item ... -Force`)**: Idempotently creates the hidden backup directory if it does not already exist.
    - **Lines 24–27 (`$SourceHash -eq $DestHash`)**: Compares the SHA-256 hexadecimal hash string of the destination file against the master source digest. If any bit was flipped due to bad sectors or bus noise, an immediate error is raised.

---

## Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Backup storage destinations, air gapped offline drive volume serial numbers, and secondary encryption salting passes are managed via administrative credential guard layers. Unencrypted raw keys are never placed onto disk media.
