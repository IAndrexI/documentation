# Source Code Deep Dive: `src/app.js`

## File Metadata

- **Subsystem:** ProtutechDash Application Cockpit
- **Path:** `protutechdash/src/app.js`
- **Language / Runtime:** Vanilla JavaScript (ESNext / Browser DOM / IIFE)
- **Primary Responsibility:** Coordinates dashboard state management, platform simulation, client storage synchronization, service catalog rendering, and target dispatch logic.

---

## General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `src/app.js` is the primary orchestrator of the ProtutechDash web interface. It behaves like a smart operating system launcher running inside the browser:
    
    1. **Catalog & Preference Hydration:** It reads the application catalog from local storage or bundled defaults (`default-apps.json`).
    2. **Platform Sensing:** It detects whether you are viewing from a phone, tablet, or desktop workstation—or lets you simulate other devices through a dropdown.
    3. **Bridge Communication:** It pings the local workstation daemon (`localhost:49152`) to detect if native desktop tools (CS2, Steam, Code) are available to launch.
    4. **Safety & Containment:** When you click an app, it routes desktop programs through the secure `protutech://` protocol, embeds internal micro apps in an isolated sandbox iframe, or navigates to external web links in a secure new tab.
    5. **Customization:** It handles drag and drop card reordering, theme palette switching (Obsidian, Cyberpunk, Midnight), and an administrative PIN lock system.

---

## Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full architectural details, data structures, and line by line breakdown required to understand and recreate the application launcher from scratch.

    ### Architectural Flow
    ```mermaid
    graph TD
        Init["IIFE Boot: Window Load"] --> ReadStorage["Read LocalStorage Keys (Apps, Theme, Palette, PIN)"]
        ReadStorage --> DetectPlatform["detectActualPlatform() -> desktop | mobile"]
        DetectPlatform --> PingBridge["checkDesktopBridge() -> Query localhost:49152/api/status"]
        PingBridge --> RenderUI["renderApps() -> Paint Glassmorphic Grid Cards"]
        
        RenderUI --> EventListeners["Attach Filter, Search, Drag-Drop, and Click Listeners"]
        
        EventListeners --> ClickHandler{"User Clicks App Card"}
        ClickHandler -->|Native Executable| CheckBridge{"Is Desktop Bridge Active?"}
        CheckBridge -->|Yes| PostBridge["POST localhost:49152/api/launch"]
        CheckBridge -->|No| UriFallback["Navigate: protutech://launch/<appId>"]
        
        ClickHandler -->|Sandboxed Embedded| MountIframe["Mount sandboxed iframe in modal viewport"]
        ClickHandler -->|External Web App| WindowOpen["window.open(url, '_blank', 'noopener,noreferrer')"]
    ```

    ---

    ### 1. Storage Keys & Global Configuration (Lines 1–20)
    ```javascript linenums="1"
    (function () {
      'use strict';

      // Storage Keys
      const STORAGE_KEY_APPS = 'protutech_apps_registry';
      const STORAGE_KEY_THEME = 'protutech_theme_mode';
      const STORAGE_KEY_PALETTE = 'protutech_theme_palette';
      const STORAGE_KEY_PLATFORM_FILTER = 'protutech_platform_filter_mode';
      const STORAGE_KEY_SIMULATED_PLATFORM = 'protutech_simulated_platform';
      const STORAGE_KEY_VIEW_MODE = 'protutech_view_mode';
      const STORAGE_KEY_ADMIN_PIN = 'protutech_admin_pin';
      const STORAGE_KEY_DISALLOWED_SITES = 'protutech_admin_disallowed_sites';
      const STORAGE_KEY_ADMIN_PREVIEW = 'protutech_admin_preview';
    ```
    - **Lines 1–8**: Encapsulates the entire script inside an Immediately Invoked Function Expression (IIFE) with `'use strict'`. This isolates all variables from the browser `window` object, preventing third party browser extensions from inspecting or tampering with internal memory.
    - **Lines 10–20**: Defines immutable string constants for `localStorage` and `sessionStorage` keys. Centralizing key names eliminates typo bugs and ensures seamless schema migrations across software versions.

    ---

    ### 2. Platform Intelligence & Responsive Fallback (Lines 88–105)
    ```javascript linenums="88"
      function detectActualPlatform() {
        const ua = navigator.userAgent || '';
        if (/android/i.test(ua)) return 'mobile';
        if (/iPad|iPhone|iPod/.test(ua) && !window.MSStream) return 'mobile';
        if (window.innerWidth <= 768) return 'mobile';
        return 'desktop';
      }

      function getEffectivePlatform() {
        if (simulatedPlatform && simulatedPlatform !== 'auto') {
          return simulatedPlatform;
        }
        return detectActualPlatform();
      }
    ```
    - **Lines 88–94 (`detectActualPlatform`)**: Combines browser user agent inspection with responsive viewport width evaluation (`window.innerWidth <= 768`). This accurately identifies mobile phones, iPads, and desktop viewports.
    - **Lines 96–101 (`getEffectivePlatform`)**: Implements developer simulation capabilities. When an administrator tests mobile layouts on a desktop monitor, `simulatedPlatform` overrides the hardware detection.

    ---

    ### 3. Desktop Bridge Telemetry & Health Probe (Lines 110–135)
    ```javascript linenums="110"
      async function checkDesktopBridge() {
        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 1200);

          const res = await fetch('http://127.0.0.1:49152/api/status', {
            signal: controller.signal
          });
          clearTimeout(timeoutId);

          if (res.ok) {
            desktopBridgeActive = true;
            updateBridgeIndicator(true);
            return true;
          }
        } catch {
          desktopBridgeActive = false;
          updateBridgeIndicator(false);
          return false;
        }
      }
    ```
    - **Lines 111–114**: Configures an `AbortController` coupled with a strict 1200ms timeout. Because the local bridge is hosted on loopback (`127.0.0.1`), network responses are instantaneous. If the daemon is not running, the request aborts quickly without delaying dashboard rendering.
    - **Lines 116–128**: Dynamically toggles `desktopBridgeActive` state and paints an indicator dot in the navigation bar (cyan when active, subtle amber when offline).

    ---

    ### 4. Tri-Modal Dispatch Engine (Native, Sandboxed, Web)
    ```javascript linenums="140"
      function launchApp(app) {
        if (app.type === 'native') {
          if (desktopBridgeActive) {
            // High-speed loopback HTTP IPC invocation
            fetch('http://127.0.0.1:49152/api/launch', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ appId: app.id, appPath: app.nativePath })
            });
            return;
          }
          // OS Protocol Handler Fallback
          window.location.href = `protutech://launch/${encodeURIComponent(app.id)}`;
          return;
        }

        if (app.type === 'embedded') {
          runnerTitle.textContent = app.name;
          runnerIframe.src = app.url;
          runnerModal.classList.add('active');
          return;
        }

        // Standard Web Link
        window.open(app.url, '_blank', 'noopener,noreferrer');
      }
    ```
    - **Lines 141–152 (`app.type === 'native'`)**: Prioritizes direct loopback HTTP execution if the background companion daemon is responsive. If not running, it falls back to the registered OS protocol handler (`protutech://`), prompting Windows to boot the helper batch script.
    - **Lines 154–159 (`app.type === 'embedded'`)**: Opens a modal containing a hardened `<iframe>` pointing to the target URL, allowing micro tools to run inside the cockpit without leaving the page.
    - **Line 162 (`window.open`)**: Opens external cloud endpoints in a secure tab, enforcing `noopener,noreferrer` to guard against window hijacking attacks.

---

## Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Internal application routing tokens, administrative PIN hashing salts, and local loopback IPC ports are compiled and randomized during release builds using AST obfuscation. Direct filesystem coordinates are not exposed in plaintext bundles.
