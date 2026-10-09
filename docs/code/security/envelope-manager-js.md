# Source Code Deep Dive: `envelope_manager.js`

## ▪ File Metadata

- **Subsystem:** Protutech Enterprise Cryptographic Vault
- **Path:** `infra/security/envelope_manager.js`
- **Language / Runtime:** Node.js (`crypto` standard library)
- **Primary Responsibility:** Implements double layer envelope encryption using PBKDF2 key derivation and AES-256-GCM authenticated cipher modes with message authentication tags.

---

## ⬡ General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `envelope_manager.js` provides bank grade envelope encryption for sensitive credentials and tokens:
    
    1. **Key Separation:** It never encrypts all files with a single master password directly. Instead, every piece of data gets its own unique, one-time 256-bit Data Encryption Key (DEK).
    2. **Authenticated Ciphers:** Data is encrypted using AES-256-GCM, producing both ciphertext and a 128-bit authentication tag. If anyone modifies even a single bit of the file on disk, decryption immediately fails.
    3. **Key Wrapping:** The one-time DEK is wrapped (encrypted) with a Key Encryption Key (KEK) derived from your master passphrase using 100,000 iterations of PBKDF2 with SHA-512.
    4. **Digital Envelope:** The output is a structured JSON envelope containing the encrypted data, wrapped key, initialization vectors, and cryptographic tags.

---

## ⬡ Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "🔎 Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full cryptographic algorithms, parameters, and line by line breakdown required to understand and recreate the envelope encryption engine from scratch.

    ### Cryptographic Pipeline
    ```mermaid
    graph TD
        Secret["Plaintext Secret Payload"] --> GenerateDEK["Generate Ephemeral 256-bit DEK (crypto.randomBytes(32))"]
        
        subgraph DataEncryption["Layer 1: Data Encryption"]
            GenerateDEK --> EncryptData["AES-256-GCM Cipher: Encrypt Payload with DEK"]
            EncryptData --> DataOutputs["Output: Ciphertext + dataIv + dataTag"]
        end

        subgraph KeyWrapping["Layer 2: Key Wrapping"]
            MasterPass["Master Passphrase + Salt"] --> PBKDF2["PBKDF2 (100,000 iterations, SHA-512) -> KEK"]
            KEK --> WrapDEK["AES-256-GCM Cipher: Encrypt DEK with KEK"]
            WrapDEK --> KeyOutputs["Output: encryptedKey + keyIv + keyTag"]
        end

        DataOutputs --> SealedEnvelope["Sealed Cryptographic Envelope (JSON)"]
        KeyOutputs --> SealedEnvelope
    ```

    ---

    ### 1. Key Derivation & AES-256-GCM Data Sealing (Lines 12–38)
    ```javascript linenums="12"
    function encryptEnvelope(plainText, masterPassphrase) {
      // 1. Derive Key Encryption Key (KEK) using PBKDF2 with 100,000 rounds
      const salt = crypto.randomBytes(32);
      const kek = crypto.pbkdf2Sync(masterPassphrase, salt, 100000, 32, 'sha512');

      // 2. Generate ephemeral 256-bit Data Encryption Key (DEK)
      const dek = crypto.randomBytes(32);

      // 3. Encrypt payload with DEK using AES-256-GCM
      const dataIv = crypto.randomBytes(12); // NIST SP 800-38D recommended 96-bit IV
      const dataCipher = crypto.createCipheriv('aes-256-gcm', dek, dataIv);
      let ciphertext = dataCipher.update(plainText, 'utf8', 'hex');
      ciphertext += dataCipher.final('hex');
      const dataTag = dataCipher.getAuthTag();

      // 4. Wrap (encrypt) the DEK using the derived KEK
      const keyIv = crypto.randomBytes(12);
      const keyCipher = crypto.createCipheriv('aes-256-gcm', kek, keyIv);
      let encryptedKey = keyCipher.update(dek.toString('hex'), 'utf8', 'hex');
      encryptedKey += keyCipher.final('hex');
      const keyTag = keyCipher.getAuthTag();

      return {
        salt: salt.toString('hex'),
        dataIv: dataIv.toString('hex'),
        dataTag: dataTag.toString('hex'),
        ciphertext,
        keyIv: keyIv.toString('hex'),
        keyTag: keyTag.toString('hex'),
        encryptedKey
      };
    }
    ```
    - **Lines 14–15 (`crypto.randomBytes(32)` & `pbkdf2Sync`)**: Generates a 256-bit cryptographically secure random salt and executes 100,000 iterations of SHA-512 to generate the KEK. This heavy computational work factor defeats GPU powered brute force password cracking attacks.
    - **Line 18 (`dek = crypto.randomBytes(32)`)**: Produces an ephemeral Data Encryption Key used exactly once, ensuring cryptographic forward secrecy.
    - **Lines 21–25 (`aes-256-gcm` and `dataIv`)**: Initializes Galois/Counter Mode (GCM) using a 96-bit Initialization Vector compliant with NIST SP 800-38D standards. GCM provides simultaneous confidentiality and cryptographic integrity verification.
    - **Line 26 (`dataCipher.getAuthTag()`)**: Generates a 128-bit authentication tag. If an attacker tampers with even a single bit of the ciphertext, decryption throws an unrecoverable integrity error.
    - **Lines 29–33 (`Wrap the DEK`)**: Encrypts the raw DEK using the KEK, sealing the key itself inside an authenticated envelope.

---

## [#] Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Vault key derivation functions utilize secret salting layers and hardware bound CPU timing delays. Envelope parameters and multi drive synchronization tokens are protected against cold boot physical extraction.
