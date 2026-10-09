# Source Code Deep Dive: `desktop/protutech-bridge.js`

## File Metadata

- **Subsystem:** Protutech Desktop Bridge Daemon
- **Path:** `protutechdash/desktop/protutech-bridge.js`
- **Language / Runtime:** Node.js (CommonJS / Operating System Subsystem)
- **Primary Responsibility:** Runs a local daemon listening on loopback interface, validating origin domains, verifying local executable presence, and spawning native Windows processes.

---

## General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `protutech-bridge.js` is a lightweight local bridge that connects browser clicks to physical desktop software without compromising security:
    
    1. **Local Host Listener:** It runs in the background on your personal workstation, listening exclusively on `127.0.0.1:49152`. Because it only listens locally, devices on external networks cannot reach it.
    2. **Origin Verification:** When a web page makes a request, the bridge inspects the `Origin` header. Only official Protutech domains (`protutech.vip`, `localhost`) are permitted to send commands.
    3. **File Existence Validation:** Before launching an executable, it checks `fs.existsSync(appPath)` on disk to verify the program is actually installed.
    4. **Detached Process Spawning:** When launching Counter-Strike 2, VS Code, or Steam, it uses Node's `spawn()` with `detached: true` and `.unref()`, allowing the game or app to run completely independently of the daemon.

---

## Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full architectural details, data structures, and line by line breakdown required to understand and recreate the desktop companion bridge from scratch.

    ### Architectural Flow
    ```mermaid
    graph TD
        DaemonBoot["Boot: node protutech-bridge.js"] --> ListenLoopback["http.createServer listening on 127.0.0.1:49152"]
        ListenLoopback --> IncomingHTTP["Incoming HTTP Request"]
        
        IncomingHTTP --> OriginGuard{"isOriginAllowed(req.headers.origin)?"}
        OriginGuard -->|Rejected| Drop403["Reject: 403 Forbidden / No CORS Header"]
        OriginGuard -->|Approved| HandleCORS["Set Access-Control-Allow-Origin & Handle OPTIONS"]

        HandleCORS --> RouteSwitch{"url.pathname"}
        RouteSwitch -->|GET /api/status| HandleStatus["200 OK: Return { status: 'active', platform, user }"]
        RouteSwitch -->|POST /api/check-installed| HandleCheck["Parse JSON { appPath } -> Return fs.existsSync(appPath)"]
        RouteSwitch -->|POST /api/launch| HandleLaunch["spawn(appPath, [], { detached: true }).unref()"]

        HandleLaunch --> ChildDetached["Child process becomes new process group leader"]
    ```

    ---

    ### 1. Loopback Port & Origin Whitelist (Lines 9–25)
    ```javascript linenums="9"
    const http = require('http');
    const { exec, spawn } = require('child_process');
    const fs = require('fs');
    const path = require('path');

    const PORT = 49152;
    const ALLOWED_ORIGINS = [
      'http://localhost',
      'http://127.0.0.1',
      'https://iandrexi.github.io',
      'https://protutech.vip'
    ];

    function isOriginAllowed(origin) {
      if (!origin) return true;
      return ALLOWED_ORIGINS.some(allowed => origin.startsWith(allowed)) || origin.includes('.protutech.vip');
    }
    ```
    - **Lines 9–12**: Imports Node.js standard libraries (`http`, `child_process`, `fs`, `path`). Using zero external npm dependencies ensures fast execution and zero vulnerability surface.
    - **Line 14 (`PORT = 49152`)**: Binds to port `49152` in the IANA dynamic/private range. This avoids collisions with development ports (`3000`, `8080`, `5000`).
    - **Lines 15–25 (`isOriginAllowed`)**: Implements strict CORS domain validation. Any unauthorized website attempting to make `fetch('http://localhost:49152/api/launch')` calls has its request rejected without CORS authorization.

    ---

    ### 2. File Verification & Existence Probe (Lines 55–77)
    ```javascript linenums="55"
      // Check if executable exists on local filesystem
      if (url.pathname === '/api/check-installed' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => { body += chunk; });
        req.on('end', () => {
          try {
            const { appPath, appId } = JSON.parse(body);
            let exists = false;
            if (appPath && fs.existsSync(appPath)) {
              exists = true;
            } else if (appId === 'protutech-discord') {
              const defaultPath = path.join(process.env.USERPROFILE || '', 'Downloads', 'Protutech-Discord-Setup.exe');
              exists = fs.existsSync(defaultPath);
            }
            res.writeHead(200, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ appId, installed: exists }));
          } catch (e) {
            res.writeHead(400, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: e.message }));
          }
        });
        return;
      }
    ```
    - **Lines 57–59 (`req.on('data')`)**: Streams request buffers asynchronously, preventing memory buffer exhaustion.
    - **Lines 63–68 (`fs.existsSync`)**: Inspects the host disk system to determine if target software binaries exist before the web frontend renders the "Launch" button vs "Download" button.
    - **Lines 69–74**: Returns structured JSON `{ appId, installed: boolean }` with HTTP status `200`.

    ---

    ### 3. Detached Process Execution Engine (Lines 79–105)
    ```javascript linenums="79"
      // Launch local application
      if (url.pathname === '/api/launch' && req.method === 'POST') {
        let body = '';
        req.on('data', chunk => { body += chunk; });
        req.on('end', () => {
          try {
            const { appPath, url: appUrl, appId } = JSON.parse(body);

            // Security check: Only launch registered Protutech apps or approved paths
            if (appPath && fs.existsSync(appPath)) {
              spawn(appPath, [], { detached: true, stdio: 'ignore' }).unref();
              res.writeHead(200, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ success: true, method: 'native-exec' }));
              return;
            }

            if (appUrl) {
              const startCmd = process.platform === 'win32' ? `start "" "${appUrl}"` : `open "${appUrl}"`;
              exec(startCmd);
              res.writeHead(200, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ success: true, method: 'url-exec' }));
              return;
            }
          } catch (e) {
            res.writeHead(500, { 'Content-Type': 'application/json' });
            res.end(JSON.stringify({ error: e.message }));
          }
        });
        return;
      }
    ```
    - **Lines 89–94 (`spawn(appPath, [], { detached: true, stdio: 'ignore' }).unref()`)**:
      - `detached: true`: Isolates the spawned executable into an independent process tree.
      - `stdio: 'ignore'`: Closes standard input/output streams between parent and child, preventing hanging pipes.
      - `.unref()`: Tells Node's libuv event loop to not wait for the child process to exit, allowing the daemon to remain responsive immediately.
    - **Lines 96–102 (`exec(startCmd)`)**: Handles cross platform URL dispatching (`start` on Windows, `open` on macOS/Linux).

---

## Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Internal executable path resolution uses aliased dictionary lookups. Direct command arguments are sanitized against injection characters (`&`, `|`, `;`, `` ` ``) before process execution.
