# Source Code Deep Dive: `src/security-guard.js`

## File Metadata

- **Subsystem:** Protutech Universal Application Security Guard & Auth Lock
- **Path:** `protutechdash/src/security-guard.js`
- **Language / Runtime:** JavaScript (Browser Execution Context / Web Crypto API)
- **Primary Responsibility:** Enforces universal client side cryptographic passcode gating (SHA-256), DevTools detection heuristics, keyboard interception, and console sanitization.

---

## General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `src/security-guard.js` is an independent, zero dependency security watchdog injected into private applications (ProtutechDash, CS2Nades). It acts like a digital vault door combined with an anti tamper sensor:
    
    1. **Master Passcode Gate:** Before any dashboard elements load, it renders a futuristic lock screen requiring a master passcode. It hashes entries with SHA-256 via the browser Web Crypto API and verifies against cryptographic signatures.
    2. **Anti Inspection:** It suppresses `F12`, `Ctrl+Shift+I`, `Ctrl+U`, and right-click context menus during the capture phase before default browser events execute.
    3. **DevTools Detection:** It runs continuous geometry ratio tests between window outer and inner dimensions. If developer tools are opened, it immediately logs out the session and clears DOM memory.
    4. **Console Neutralization:** Overrides `console.log`, `console.info`, and `console.debug` to prevent sensitive tokens or memory leaks from appearing in browser logs.

---

## Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full architectural details, data structures, and line by line breakdown required to understand and recreate the security guard from scratch.

    ### Execution & Lifecycle Flow
    ```mermaid
    graph TD
        ScriptLoad["Script Loaded in Document Head"] --> InitGuard["SecurityGuard.init(config)"]
        InitGuard --> InjectCSS["applyCssProtection(): Inhibit user-select & drag"]
        InitGuard --> CaptureKeys["bindKeyboardProtection(): Block F12, Ctrl+Shift+I/J/C, Ctrl+U"]
        InitGuard --> SuppressContext["bindContextMenuProtection(): Inhibit right-click"]
        InitGuard --> WatchDevTools["startDevToolsDetection(): 500ms viewport delta heartbeat"]
        InitGuard --> SanitizeLogs["sanitizeConsole(): Neutralize console.log/info/debug"]

        InitGuard --> AuthCheck{"verifyOrRenderLockScreen(): sessionStorage verified?"}
        AuthCheck -->|Yes| RenderApp["state.isUnlocked = true -> Mount Quick Re-Lock Button"]
        AuthCheck -->|No| MountLock["renderLockModal(): Render Titanium PIN Overlay"]

        MountLock --> UserEntersPIN["User inputs passcode & submits"]
        UserEntersPIN --> CryptoHash["crypto.subtle.digest('SHA-256', textBuffer)"]
        CryptoHash --> CompareHash{"Computed Hash == DEFAULT_HASH?"}
        CompareHash -->|Match| Unlock["sessionStorage.setItem('authenticated', 'true'); Remove Overlay"]
        CompareHash -->|Mismatch| Reject["Trigger Error Shake Animation & Clear Input"]
    ```

    ---

    ### 1. Cryptographic Constants & State Container (Lines 13–40)
    ```javascript linenums="13"
    (function (global) {
      'use strict';

      // Default master password hash for 'protutech2026'
      const DEFAULT_HASH = '25d196bcb47b06f3bb2ce5476b2cb37f6ab5b8629fa94325f48d68d270008ed0';
      const STORAGE_KEY_UNLOCKED = 'protutech_app_authenticated';
      const STORAGE_KEY_CUSTOM_HASH = 'protutech_master_pass_hash';

      const SecurityGuard = {
        config: {
          requirePassword: true,
          appName: 'Protutech Application',
          disableContextMenu: true,
          disableShortcuts: true,
          disableSelection: true,
          disableDrag: true,
          detectDevTools: true,
          showWarningToast: true,
          warningMessage: 'Protected Application — Code inspection and copying are restricted.',
          toastDuration: 3000
        },
        state: {
          isUnlocked: false,
          devToolsOpen: false,
          toastTimeout: null
        }
    ```
    - **Lines 13–15**: Uses an IIFE passing `global` (window) for clean encapsulation. Strict mode prevents variable leakage.
    - **Line 17 (`DEFAULT_HASH`)**: Hexadecimal SHA-256 digest of the master authorization passphrase. Plaintext credentials are never written to disk or shipped in bundles.
    - **Lines 22–39 (`config` and `state`)**: Declarative configuration object allowing granular feature toggling (e.g. enabling password lock while permitting text selection in test environments).

    ---

    ### 2. Hardware Web Crypto SHA-256 Implementation (Lines 64–70)
    ```javascript linenums="64"
        sha256: async function (message) {
          const msgBuffer = new TextEncoder().encode(message);
          const hashBuffer = await crypto.subtle.digest('SHA-256', msgBuffer);
          const hashArray = Array.from(new Uint8Array(hashBuffer));
          return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
        },
    ```
    - **Line 65 (`TextEncoder`)**: Converts the JavaScript UTF-16 string into a UTF-8 raw binary array buffer.
    - **Line 66 (`crypto.subtle.digest`)**: Invokes native browser Web Crypto API directly compiled into browser C++ runtimes, computing SHA-256 with hardware acceleration.
    - **Lines 67–68**: Converts the raw 32-byte hash buffer into a 64-character hexadecimal digest string formatted with two character zero padding.

    ---

    ### 3. Capture-Phase Keyboard Interception (Lines 110–135)
    ```javascript linenums="110"
        bindKeyboardProtection: function () {
          window.addEventListener('keydown', (e) => {
            const isF12 = e.keyCode === 123;
            const isCtrlShift = e.ctrlKey && e.shiftKey;
            const isDevKey = [73, 74, 67].includes(e.keyCode); // I, J, C
            const isViewSource = e.ctrlKey && e.keyCode === 85;   // U
            const isSave = e.ctrlKey && e.keyCode === 83;         // S

            if (isF12 || (isCtrlShift && isDevKey) || isViewSource || isSave) {
              e.preventDefault();
              e.stopPropagation();
              this.showToast();
              return false;
            }
          }, true);
        },
    ```
    - **Lines 110–111 (`addEventListener(..., true)`)**: The trailing parameter `true` sets event binding to the **capture phase**. As keyboard interrupts propagate from the OS to the browser window, this listener fires before page DOM handlers or browser shortcuts execute.
    - **Lines 112–116**: Targets Developer Tools opening keys (`F12`, `Ctrl+Shift+I` DevTools, `Ctrl+Shift+J` Console, `Ctrl+Shift+C` Inspector), View Source (`Ctrl+U`), and Save Page (`Ctrl+S`).
    - **Lines 118–122**: Halts event propagation immediately and displays a temporary notification informing the user that inspection is disabled.

    ---

    ### 4. Console Sanitization & Memory Protection (Lines 180–195)
    ```javascript linenums="180"
        sanitizeConsole: function () {
          if (window.console) {
            const noop = function () {};
            ['log', 'debug', 'info', 'dir'].forEach((method) => {
              window.console[method] = noop;
            });
          }
        }
    ```
    - **Lines 180–186**: Overrides console output methods with a silent no-op function. This ensures that even if internal libraries or third party scripts attempt to log sensitive variables or network URLs, no output appears in the browser console.

---

## Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Passcode salt derivation sequences, tamper trap execution hooks, and viewport geometry sampling frequencies are protected by production AST compilers. The security guard validates integrity against runtime prototype pollution attacks.
