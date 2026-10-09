# Cryptographic Concept: Double Envelope Encryption & Authenticated Ciphers

In Protutech's security infrastructure, protecting database secrets, Discord bot tokens, and user credentials requires more than basic symmetric encryption. If you encrypt every credential using a single master password directly, an attacker who recovers one decrypted memory buffer or derives the key compromises every asset on the server. We solved this by implementing **Double Layer Envelope Encryption** using **AES-256-GCM** and **PBKDF2**.

```mermaid
graph TD
    subgraph Layer1["Layer 1: Ephemeral Payload Encryption"]
        Plaintext["Sensitive Secret Payload (Plaintext String)"]
        DEK["256-bit Random DEK (crypto.randomBytes(32))"]
        IV1["96-bit Random IV (crypto.randomBytes(12))"]
        Plaintext + DEK + IV1 --> AES1["AES-256-GCM Cipher"]
        AES1 --> Ciphertext["Ciphertext Payload (hex)"]
        AES1 --> AuthTag1["128-bit Authentication Tag (dataTag)"]
    end

    subgraph Layer2["Layer 2: Key Encryption Wrapping"]
        Passphrase["Master Passphrase (User Secret)"]
        Salt["256-bit Random Salt (crypto.randomBytes(32))"]
        Passphrase + Salt --> PBKDF2["PBKDF2-HMAC-SHA512 (100,000 iterations)"]
        PBKDF2 --> KEK["Derived 256-bit KEK"]
        IV2["96-bit Random IV (crypto.randomBytes(12))"]
        DEK + KEK + IV2 --> AES2["AES-256-GCM Cipher"]
        AES2 --> WrappedDEK["Encrypted DEK (hex)"]
        AES2 --> AuthTag2["128-bit Authentication Tag (keyTag)"]
    end

    subgraph OutputEnvelope["Sealed Digital Envelope"]
        Ciphertext --> Envelope["JSON Envelope Record"]
        WrappedDEK --> Envelope
        Salt --> Envelope
        IV1 --> Envelope
        IV2 --> Envelope
        AuthTag1 --> Envelope
        AuthTag2 --> Envelope
    end
```

---

## Technical Mechanics & Byte Specifications

### 1. Data Encryption Key (DEK) Lifecycle
- **Entropy Source**: Generated using `crypto.randomBytes(32)` pulled directly from the OS entropy pool (`/dev/urandom` on Linux or `BCryptGenRandom` on Windows).
- **Scope**: Used exactly once for one specific secret, then discarded from heap memory.
- **Key Length**: 256 bits (32 bytes).

### 2. Galois/Counter Mode (GCM)
We use GCM instead of CBC (Cipher Block Chaining) because CBC only provides confidentiality, requiring a separate HMAC pass to prevent bit flipping attacks (such as padding oracle exploits). 
- **NIST SP 800-38D Compliance**: GCM combines counter mode privacy with a Galois field multiplier ($GF(2^{128})$) to calculate an authentication tag simultaneously.
- **Initialization Vector (IV)**: Exactly 96 bits (12 bytes). Using a 96 bit IV is critical; any other length forces the cipher to execute an additional GHASH step over the IV, degrading performance and increasing collision risk.
- **Auth Tag**: 128 bits (16 bytes). If an attacker changes even one bit of the ciphertext or IV, `cipher.final()` or `decipher.setAuthTag()` throws an immediate `Error: Unsupported state or unable to authenticate data`.

### 3. Key Derivation via PBKDF2 (RFC 2898)
The Key Encryption Key (KEK) is derived from the master passphrase:
- **Hash Primitive**: HMAC-SHA512.
- **Iterations**: 100,000 rounds. This computational work factor forces an attacker to burn millions of GPU clock cycles per guess during an offline brute force attack.
- **Salt**: 32 bytes of cryptographically secure random data per envelope, preventing precomputed rainbow table attacks.

---

## Wire Format & JSON Envelope Schema

Every encrypted record in the homelab is stored using this strict JSON schema:

```json
{
  "version": 1,
  "salt": "a4f89b...32_bytes_hex",
  "dataIv": "c1d2e3...12_bytes_hex",
  "dataTag": "7f8a9b...16_bytes_hex",
  "ciphertext": "993a4b...variable_length_hex",
  "keyIv": "1a2b3c...12_bytes_hex",
  "keyTag": "5e6f7a...16_bytes_hex",
  "encryptedKey": "8b9c0d...64_hex_chars"
}
```

---

## Technical References & Authoritative Sources

1. **NIST Special Publication 800-38D**: *Recommendation for Block Cipher Modes of Operation: Galois/Counter Mode (GCM) and GMAC*  
   Official Specification: [https://csrc.nist.gov/publications/detail/sp/800-38d/final](https://csrc.nist.gov/publications/detail/sp/800-38d/final)
2. **IETF RFC 2898 (PKCS #5 v2.0)**: *Password-Based Cryptography Specification Version 2.0*  
   RFC Index: [https://datatracker.ietf.org/doc/html/rfc2898](https://datatracker.ietf.org/doc/html/rfc2898)
3. **Node.js Crypto API Documentation**: *Ciphers, Deciphers, and Web Crypto Compatibility*  
   Documentation: [https://nodejs.org/api/crypto.html#cryptocreatecipherivalgorithm-key-iv-options](https://nodejs.org/api/crypto.html#cryptocreatecipherivalgorithm-key-iv-options)
4. **Ferguson, Schneier & Kohno (2010)**: *Cryptography Engineering: Design Principles and Practical Applications* (Wiley).
