# Source Code Deep Dive: `src/services/matrix.ts`

## File Metadata

- **Subsystem:** ProtutechChat Federated Messaging & State Engine
- **Path:** `discordapi/client/src/services/matrix.ts`
- **Language / Runtime:** TypeScript (Browser ESNext & Electron Renderer)
- **Primary Responsibility:** Manages Matrix homeserver authentication, realtime long polling synchronization, media conversions (`mxc://` to HTTP), message redactions, and in memory event caches.

---

## General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `src/services/matrix.ts` is the communication engine that gives ProtutechChat sovereign, decentralized messaging:
    
    1. **Authentication:** It logs users into the self-hosted Matrix homeserver, obtaining a secure session token and caching it in local storage.
    2. **Long Polling Sync:** Rather than continuously spamming the server with requests, it opens a persistent 30-second HTTP channel. The server answers the split second a new message arrives.
    3. **In-Memory Cache:** Maintains high-speed maps (`roomsCache`, `guildsCache`) so conversations and channel lists switch with zero lag.
    4. **Media Translation:** Translates internal Matrix media URIs (`mxc://`) into authenticated HTTPS download links for avatars and attachments.
    5. **Event Dispatching:** Implements reactive pub/sub listeners notifying React components when messages are created, edited, or redacted.

---

## Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full architectural details, data structures, and line by line breakdown required to understand and recreate the Matrix communications engine from scratch.

    ### Client State Flow & Long Polling Loop
    ```mermaid
    graph TD
        UserLogin["user.login(username, password)"] --> AuthPost["POST /_matrix/client/v3/login"]
        AuthPost --> SaveToken["Persist accessToken & userId in localStorage"]
        SaveToken --> StartSync["startSync(): Continuous Polling Loop"]

        subgraph SyncLoop["Realtime Long-Polling Loop"]
            StartSync --> SyncFetch["GET /_matrix/client/v3/sync?since=TOKEN&timeout=30000"]
            SyncFetch --> ProcessEvents["Process room messages, state changes & presence"]
            ProcessEvents --> NotifySubscribers["messageListeners.forEach(cb => cb(roomId, msg))"]
            NotifySubscribers --> SyncFetch
        end
    ```

    ---

    ### 1. Matrix Client Service State & Constructor (Lines 6–25)
    ```typescript linenums="6"
    export class MatrixClientService {
      private accessToken: string | null = null;
      private userId: string | null = null;
      private syncToken: string | null = null;
      private syncRunning: boolean = false;
      private messageListeners: Set<(roomId: string, message: MatrixMessage) => void> = new Set();
      private redactionListeners: Set<(roomId: string, eventId: string) => void> = new Set();
      private presenceListeners: Set<(userId: string, presence: 'online' | 'idle' | 'dnd' | 'offline') => void> = new Set();
      private roomsCache: Map<string, MatrixRoom> = new Map();
      private guildsCache: Map<string, DiscordGuild> = new Map();

      constructor() {
        this.accessToken = localStorage.getItem('matrix_access_token');
        this.userId = localStorage.getItem('matrix_user_id');
      }
    ```
    - **Lines 7–10**: Private instance variables storing authentication tokens and batch synchronization cursors (`syncToken`). Keeping them private ensures external components cannot mutate sync state directly.
    - **Lines 11–13**: Reactive pub/sub listener sets using JavaScript `Set` data structures. This provides $O(1)$ addition and removal of component callbacks without duplicate listeners.
    - **Lines 14–15**: In-memory `Map` caches providing sub-millisecond retrieval of room metadata and Discord-style server groupings.
    - **Lines 21–24**: The constructor hydrates existing session tokens from local storage, restoring authentication state on app boot.

    ---

    ### 2. Authentication & Session Initialization (Lines 34–59)
    ```typescript linenums="34"
      public async login(username: string, password: string): Promise<boolean> {
        try {
          const res = await fetch(`${BASE_URL}/_matrix/client/v3/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              type: 'm.login.password',
              identifier: { type: 'm.id.user', user: username },
              password,
            }),
          });

          if (!res.ok) return false;

          const data = await res.json();
          this.accessToken = data.access_token;
          this.userId = data.user_id;
          localStorage.setItem('matrix_access_token', data.access_token);
          localStorage.setItem('matrix_user_id', data.user_id);

          this.startSync();
          return true;
        } catch {
          return false;
        }
      }
    ```
    - **Lines 36–44**: Dispatches standard Matrix Client-Server specification v3 password login requests over encrypted HTTPS.
    - **Lines 49–52**: Stores the granted `access_token` and canonical user matrix identifier (`@user:protutech.vip`).
    - **Line 54 (`this.startSync()`)**: Immediately triggers the continuous sliding sync process upon successful verification.

    ---

    ### 3. MXC Media URI Transformation (Lines 69–73)
    ```typescript linenums="69"
      public mxcToHttp(mxcUrl?: string): string | undefined {
        if (!mxcUrl || !mxcUrl.startsWith('mxc://')) return mxcUrl;
        const path = mxcUrl.replace('mxc://', '');
        return `${BASE_URL}/_matrix/media/v3/download/${path}`;
      }
    ```
    - **Line 70**: Asserts whether the input string conforms to the content addressed Matrix media format (`mxc://`).
    - **Lines 71–72**: Strips the protocol prefix and constructs an authenticated HTTP endpoint that standard browser `<img>` elements and video players can render without custom decoding.

---

## Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Internal state synchronization batch tokens, presence rate limiters, and end to end encrypted room key exchange parameters are negotiated inside protected service modules. Homeserver network boundaries utilize abstracted edge routing.
