# ProtutechDash Subfolder & Module Anatomy

## ▸ Exhaustive Directory Hierarchy

The repository is structured into distinct functional domains, isolating browser presentation, native host bindings, build tooling, and static mock environments:

```
protutechdash/
├── 📁 .github/
│   └── 📁 workflows/
│       └── deploy.yml              # Automated GitHub Pages CI/CD pipeline
├── 📁 assets/
│   └── protutech-logo.svg          # Core SVG vector branding asset
├── 📁 data/
│   └── default-apps.json           # Default service registry (ports, URLs, icons, categories)
├── 📁 desktop/
│   ├── launch-helper.bat           # Silent background runner for bridge Node process
│   ├── protutech-bridge.js         # HTTP/WebSocket daemon executing local native binaries
│   └── protutech-protocol.bat      # Windows Registry helper to register protutech:// URI scheme
├── 📁 dist/
│   ├── app.min.js                  # Production obfuscated AST build of src/app.js
│   └── security-guard.min.js       # Production obfuscated AST build of src/security-guard.js
├── 📁 embed/
│   ├── demo-app.html               # Isolated iframe test fixture for cross-origin security
│   └── protutech-launcher.js       # Embeddable script tag allowing third-party sites to open apps
├── 📁 scripts/
│   └── obfuscate.js                # Build script using javascript-obfuscator for production
├── 📁 src/
│   ├── app.js                      # Core frontend application state & DOM rendering logic
│   ├── security-guard.js           # Anti-devtools, keyboard lockout & tamper detection
│   └── styles.css                  # Apple Obsidian glassmorphic design system tokens
├── index.html                      # Single Page Application entrypoint
├── manifest.json                   # PWA web app manifest (icons, theme color, display mode)
├── package.json                    # Node dependencies (javascript-obfuscator, terser)
└── sw.js                           # Service worker cache strategy for offline resilience
```

---

## ▪ Module Responsibilities by Subfolder

### 1. `src/` – Application Core & User Experience
The primary client runtime executing in the browser:
- **`app.js`**: Initializes application state, reads `data/default-apps.json`, merges user overrides from `localStorage`, mounts search listeners, and constructs the interactive card grid. Handles clicking events, routing web links vs native `protutech://` protocol dispatches.
- **`security-guard.js`**: A standalone zero dependency security watchdog. Injected at the `<head>` of `index.html` before any other script executes. Binds low-level window listeners to inhibit DevTools opening (`F12`, `Ctrl+Shift+I`, `Ctrl+U`), monitors window inner vs outer dimensions to detect docked developer panes, and neutralizes context menus.
- **`styles.css`**: CSS variables defining the Obsidian dark palette (`--bg-primary: #060913`, `--accent-cyan: #00f2fe`), glassmorphic backdrop filters, responsive CSS grid layouts, and micro-interaction animations.

### 2. `desktop/` – Native Operating System Bridge
Bridging the gap between containerized web browsers and host desktop software:
- **`protutech-bridge.js`**: A lightweight Node.js daemon running locally on the workstation (listening on `127.0.0.1:48123` or invoked via CLI argument). When a user clicks a native desktop target (e.g. Counter-Strike 2, VS Code, Steam), the browser triggers a `protutech://run/<app_id>` custom URI.
- **`protutech-protocol.bat`**: Windows Batch script that writes registry keys into `HKEY_CURRENT_USER\Software\Classes\protutech` to bind the URL protocol handler to `launch-helper.bat`.
- **`launch-helper.bat`**: Invokes `node.exe protutech-bridge.js %1` with hidden console window windowing flags.

### 3. `scripts/` – Build Automation & Code Hardening
- **`obfuscate.js`**: Node.js build script utilizing `javascript-obfuscator`. Ingests `src/app.js` and `src/security-guard.js`, performs AST control-flow flattening (threshold `0.75`), injects dead code (threshold `0.3`), transforms string arrays with Base64 encoding and rotation, and outputs production bundles to `dist/`.

### 4. `embed/` – Micro-Frontend & Iframe Isolation
- **`demo-app.html`**: A mock micro frontend embedded inside ProtutechDash's modal viewport to test CSP (Content Security Policy) headers, postMessage serialization, and iframe sandbox permissions (`allow-scripts`, `allow-same-origin`).
- **`protutech-launcher.js`**: A drop-in widget script that can be embedded in internal documentation or wikis to render a floating quick-access launcher pill.

### 5. `data/` – Service Directory Configuration
- **`default-apps.json`**: Declarative JSON registry specifying all 15+ homelab applications, categorized by functional group, containing internal URLs (`https://dash.protutech.vip`), port allocations, SVG icons, and description metadata.
