# Source Code Deep Dive: `client/electron/main.cjs`

## ▪ File Metadata

- **Subsystem:** ProtutechChat Native Operating System Shell
- **Path:** `discordapi/client/electron/main.cjs`
- **Language / Runtime:** Node.js (Electron Main Process / Windows WASAPI)
- **Primary Responsibility:** Manages native application window life cycles, hardware accelerated Chromium command line flags, loopback desktop audio streaming, system tray minimizing, and global hotkeys.

---

## ⬡ General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `client/electron/main.cjs` wraps the ProtutechChat web frontend into a high-performance native desktop application:
    
    1. **Chromium Engine Tuning:** Appends native flags before the browser boots to force hardware-accelerated H.264 video decoding and ultra-low-latency PCM audio buffers.
    2. **Frameless Glass Window:** Spawns a sleek, borderless window with dark glassmorphic styling and native maximize/minimize controls.
    3. **System Audio Loopback:** Hooks into the Windows Core Audio (WASAPI) loopback engine so you can stream game audio directly to friends during screen shares with zero lag.
    4. **Background Persistence:** When you click the close button `X`, it minimizes to the system tray so you remain in voice calls uninterrupted.
    5. **Global Shortcuts:** Registers system-wide hotkeys (`Ctrl+Shift+M` to mute, `Ctrl+Shift+D` to deafen) that work even when games are running fullscreen.

---

## ⬡ Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "🔎 Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full architectural details, data structures, and line by line breakdown required to understand and recreate the native Electron desktop shell from scratch.

    ### Window Lifecycle & IPC Pipeline
    ```mermaid
    graph TD
        AppLaunch["Electron Boot: app.whenReady()"] --> SetFlags["Inject Chromium Audio & WebRTC Acceleration Flags"]
        SetFlags --> MakeWindow["createWindow(): Frameless Window (1280x780)"]
        MakeWindow --> BindIPC["Bind Native IPC Handlers & Screen Capturer"]
        MakeWindow --> GlobalKeys["Register OS Hotkeys (Ctrl+Shift+M & Ctrl+Shift+D)"]

        CloseEvent["User clicks window 'X' Close Button"] --> CheckQuitting{"isQuitting == true?"}
        CheckQuitting -->|No| HideToTray["event.preventDefault(); mainWindow.hide(); Show Tray Balloon"]
        CheckQuitting -->|Yes| AppQuit["app.quit() Final Cleanup"]
    ```

    ---

    ### 1. Chromium Command-Line Tuning Switches (Lines 5–15)
    ```javascript linenums="5"
    // Optimize Chromium audio/video flags for ultra low latency WebRTC LiveKit & Screen Capture
    app.commandLine.appendSwitch('autoplay-policy', 'no-user-gesture-required');
    app.commandLine.appendSwitch('enable-features', 'WebRTCPCM16kAudio,WebRTC-H264WithOpenH264FFmpeg');
    app.commandLine.appendSwitch('force-webrtc-ip-handling-policy', 'default_public_interface_only');
    app.commandLine.appendSwitch('ignore-certificate-errors');
    app.commandLine.appendSwitch('enable-usermedia-screen-capturing');
    app.commandLine.appendSwitch('auto-select-desktop-capture-source', 'Entire screen');
    ```
    - **Line 6 (`autoplay-policy`)**: Prevents Chromium from blocking incoming audio streams until a user interaction occurs.
    - **Line 7 (`enable-features`)**: Enables low-latency 16kHz PCM audio decoding and hardware-accelerated H.264 video processing via OpenH264/FFmpeg.
    - **Line 8 (`force-webrtc-ip-handling-policy`)**: Enforces WebRTC privacy standards by preventing local private subnet IP addresses from leaking across public network interfaces.
    - **Lines 10–11**: Enables desktop video capture capabilities for screen sharing.

    ---

    ### 2. Frameless Window Construction (Lines 20–36)
    ```javascript linenums="20"
      mainWindow = new BrowserWindow({
        width: 1280,
        height: 780,
        minWidth: 940,
        minHeight: 520,
        frame: false,
        titleBarStyle: 'hidden',
        backgroundColor: '#090d16',
        icon: iconPath,
        show: false,
        webPreferences: {
          preload: path.join(__dirname, 'preload.cjs'),
          contextIsolation: true,
          nodeIntegration: false,
          webSecurity: false,
        },
      });
    ```
    - **Lines 25–26 (`frame: false`, `titleBarStyle: 'hidden'`)**: Removes the standard Windows title bar, allowing the React frontend to render custom Discord-style title chrome.
    - **Line 27 (`backgroundColor: '#090d16'`)**: Prevents a bright white flash while web assets load into memory.
    - **Lines 31–34 (`webPreferences`)**: Enforces strict security best practices (`contextIsolation: true`, `nodeIntegration: false`) while exposing controlled bridge APIs via `preload.cjs`.

    ---

    ### 3. WASAPI Audio Loopback Capture (Lines 52–60)
    ```javascript linenums="52"
      mainWindow.webContents.session.setDisplayMediaRequestHandler((request, callback) => {
        desktopCapturer.getSources({ types: ['screen', 'window'] }).then((sources) => {
          if (sources.length > 0) {
            callback({ video: sources[0], audio: 'loopback' });
          } else {
            callback({});
          }
        });
      });
    ```
    - **Lines 52–53**: Intercepts `getDisplayMedia` calls originating from the WebRTC voice engine.
    - **Line 55 (`audio: 'loopback'`)**: Requests audio from the Windows WASAPI loopback device. This enables direct capture of internal game sound without needing virtual audio cable software.

---

## [#] Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Native context bridge interfaces, preload script IPC channels (`ipcRenderer.invoke`), and cryptographic token storage paths are compiled into secure runtime bundles. Application signing certificates verify host process integrity.
