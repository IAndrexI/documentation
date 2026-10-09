# Source Code Deep Dive: `src/services/livekit.ts`

## File Metadata

- **Subsystem:** ProtutechChat Ultra Low Latency Voice Subsystem
- **Path:** `discordapi/client/src/services/livekit.ts`
- **Language / Runtime:** TypeScript (LiveKit WebRTC SDK)
- **Primary Responsibility:** Coordinates Selective Forwarding Unit (SFU) room joins, WebRTC audio/video track subscriptions, digital signal processing (DSP), and per user volume amplification.

---

## General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `src/services/livekit.ts` gives ProtutechChat sub-30ms audio and screen sharing:
    
    1. **Selective Forwarding Unit (SFU):** Instead of peer-to-peer mesh calls that overwhelm internet bandwidth in group chats, your audio is sent once to your homelab server and efficiently mirrored to listeners.
    2. **Hardware Accelerated DSP:** Pre-configures browser Web Audio filters (automatic gain control, acoustic echo cancellation, background noise suppression).
    3. **Dynamic Stream Tuning:** Automatically pauses off-screen video streams (`adaptiveStream: true`) to preserve workstation CPU and GPU power during gaming.
    4. **Per-User Volume Scaling:** Allows players to boost quiet friends up to 200% volume or mute individuals locally.

---

## Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full architectural details, data structures, and line by line breakdown required to understand and recreate the WebRTC voice engine from scratch.

    ### Voice Subscription Flow
    ```mermaid
    graph TD
        UserAction["user.joinVoice(roomName, identity, displayName)"] --> FetchToken["POST /api/voice/token -> Obtain ephemeral JWT"]
        FetchToken --> InitRoom["new Room({ adaptiveStream: true, dynacast: true, audioCaptureDefaults })"]
        InitRoom --> ConnectSFU["room.connect(wsUrl, token)"]
        
        subgraph TrackLifecycle["Track Subscription Pipeline"]
            ConnectSFU --> OnTrackSubscribed["room.on(RoomEvent.TrackSubscribed, (track, publication, participant))"]
            OnTrackSubscribed --> AttachAudio["track.attach() to HTMLMediaElement"]
            AttachAudio --> VolumeApply["Apply userVolumes.get(identity) scaling (0% - 200%)"]
        end
    ```

    ---

    ### 1. Room Configuration & Audio DSP Hardware Optimization (Lines 89–105)
    ```typescript linenums="89"
          // Initialize LiveKit room with ultra low latency tuning
          const room = new Room({
            adaptiveStream: true,
            dynacast: true,
            audioCaptureDefaults: {
              autoGainControl: true,
              echoCancellation: true,
              noiseSuppression: true,
            },
          });

          this.room = room;
    ```
    - **Line 91 (`adaptiveStream: true`)**: Pauses incoming video decoding when video elements are minimized or off screen, saving vital GPU cycles during intensive games like Counter-Strike 2.
    - **Line 92 (`dynacast: true`)**: Dynamically scales publishing video bitrate and resolution according to viewers' active screen sizes.
    - **Lines 93–97 (`audioCaptureDefaults`)**: Enables Web Audio hardware filters:
      - `autoGainControl: true`: Balances microphone volume automatically.
      - `echoCancellation: true`: Prevents speaker sound from feeding back into the microphone.
      - `noiseSuppression: true`: Uses DSP filters to eliminate mechanical keyboard and background fan noise.

    ---

    ### 2. Individual User Volume Amplification (Lines 150–162)
    ```typescript linenums="150"
      public setUserVolume(identity: string, volume: number) {
        // Volume percentage from 0 to 200
        this.userVolumes.set(identity, volume);
        const audioEl = this.audioElements.get(identity);
        if (audioEl) {
          // Scale standard 0.0 - 1.0 volume property
          audioEl.volume = Math.max(0, Math.min(1, volume / 100));
        }
      }
    ```
    - **Line 152**: Updates the internal memory volume map keyed by participant identity.
    - **Lines 153–157**: Normalizes the UI slider range ($0\%$ to $200\%$) onto the browser's native `HTMLMediaElement.volume` property with safe clamping, preventing audio clipping.

---

## Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> LiveKit server administrative tokens, STUN/TURN ICE candidate relay addresses, and WebRTC encryption keys are negotiated via authenticated backend endpoints. Raw token signing secrets are never exposed on client runtimes.
