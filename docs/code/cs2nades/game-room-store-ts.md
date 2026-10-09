# Source Code Deep Dive: `src/stores/gameRoomStore.ts`

## File Metadata

- **Subsystem:** Pinia Realtime Room & Collaboration Store
- **Path:** `CS2Nades/src/stores/gameRoomStore.ts`
- **Language / Runtime:** TypeScript (Vue 3 Pinia Store / Socket.IO Client)
- **Primary Responsibility:** Manages persistent WebSocket lifecycle, room joining tokens, live tactical drawing strokes, host administrative permissions, and team chat.

---

## General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `src/stores/gameRoomStore.ts` is the central nervous system for collaborative team playbooks:
    
    1. **Persistent WebSocket Bridge:** It connects your browser to the Socket.IO server and maintains the connection with automatic reconnection backoff if your Wi-Fi drops.
    2. **Squad Room State:** It tracks active squad members, their in-game roles (IGL, Entry, AWPer), and who currently holds captain/host permissions.
    3. **Live Whiteboard Synchronization:** Whenever a player draws an arrow or line, it normalizes coordinates and streams strokes to all teammates' screens in under 20ms.
    4. **Tactical Broadcasts:** When a player discovers a smoke lineup, they click "Broadcast to Squad", and the store displays an interactive popup across all teammates' screens.

---

## Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full architectural details, data structures, and line by line breakdown required to understand and recreate the Pinia collaboration store from scratch.

    ### Lifecycle & Event Dispatch
    ```mermaid
    graph TD
        Mount["Component Mounts: useGameRoomStore()"] --> GetSocket["getSocket(): Check or instantiate Socket.IO singleton"]
        GetSocket --> BindHandlers["Bind 'connect', 'disconnect', 'room:members', 'room:stroke'"]
        
        BindHandlers --> UserJoins["joinRoom(roomCode, user)"]
        UserJoins --> EmitJoin["socket.emit('room:join', { roomCode, user })"]
        
        subgraph RealtimeSubscribers["Realtime Event Dispatchers"]
            EmitJoin --> OnStroke["socket.on('room:stroke') -> liveDrawings.push(stroke)"]
            EmitJoin --> OnMapChange["socket.on('room:map_switched') -> mapStore.setMap(mapId)"]
            EmitJoin --> OnLineup["socket.on('room:lineup_broadcast') -> activeBroadcastLineups.push(lineup)"]
        end
    ```

    ---

    ### 1. Data Interfaces & Store Initialization (Lines 9–52)
    ```typescript linenums="9"
    export interface RoomMember {
      socketId: string;
      username: string;
      avatar?: string;
      inGameRole?: string;
      isAutoAllowed?: boolean;
      isHost?: boolean;
    }

    export interface DrawingStroke {
      id: string;
      tool: 'pen' | 'arrow' | 'line';
      color: string;
      width: number;
      points: Array<{ x: number; y: number }>;
    }

    export const useGameRoomStore = defineStore('gameRoom', () => {
      const socket = ref<any>(null);
      const isConnected = ref<boolean>(false);
      const currentRoomCode = ref<string | null>(null);
      const hostUsername = ref<string | null>(null);
      const currentMapId = ref<string>('mirage');
      const members = ref<RoomMember[]>([]);
      const liveDrawings = ref<DrawingStroke[]>([]);
      const activeBroadcastLineups = ref<Lineup[]>([]);
    ```
    - **Lines 9–23**: Strongly typed interfaces defining room member profiles and 2D vector drawing stroke paths.
    - **Lines 42–52**: Pinia setup store syntax defining reactive refs. Any modification to `liveDrawings` or `members` triggers instant Vue DOM updates without manual event binding.

    ---

    ### 2. Host Authority Computed Logic (Lines 60–83)
    ```typescript linenums="60"
      const isHost = computed(() => {
        if (!hostUsername.value) return false;
        const current = localStorage.getItem('cs2_stratbook_user');
        const username = current ? JSON.parse(current)?.username : '';
        return hostUsername.value.toLowerCase() === (username || '').toLowerCase();
      });

      function updateRoomPermissions(signedUsers: boolean, guests: boolean, onlyHostMap = true) {
        allowSignedUsersToDraw.value = signedUsers;
        allowGuestsToDraw.value = guests;
        onlyHostCanChangeMap.value = onlyHostMap;
        if (socket.value && socket.value.connected) {
          socket.value.emit('room:update_permissions', {
            allowSignedUsersToDraw: signedUsers,
            allowGuestsToDraw: guests,
            onlyHostCanChangeMap: onlyHostMap
          });
        }
      }
    ```
    - **Lines 60–65 (`isHost`)**: Reactive computed evaluation verifying if the active user matches the designated room host.
    - **Lines 71–83 (`updateRoomPermissions`)**: Synchronizes room access rules across the network, preventing guests or unauthenticated viewers from modifying the team whiteboard during tournament matches.

    ---

    ### 3. Resilient WebSocket Connection Pool (Lines 84–110)
    ```typescript linenums="84"
      function getSocket(): Socket {
        if (!socket.value) {
          socket.value = io({
            autoConnect: true,
            reconnection: true,
            reconnectionAttempts: 10,
            reconnectionDelay: 1000
          });

          socket.value.on('connect', () => {
            isConnected.value = true;
            if (currentRoomCode.value) {
              const u = localStorage.getItem('cs2_stratbook_user') ? JSON.parse(localStorage.getItem('cs2_stratbook_user') || '{}') : null;
              socket.value.emit('room:join', { roomCode: currentRoomCode.value, user: u });
            }
          });

          socket.value.on('disconnect', () => {
            isConnected.value = false;
          });
        }
        return socket.value;
      }
    ```
    - **Lines 84–91**: Initializes the singleton Socket.IO client with exponential backoff (`reconnectionAttempts: 10`, `reconnectionDelay: 1000ms`), preventing server flooding if network connections drop.
    - **Lines 93–99**: Automatically re-joins active room sessions upon network recovery, preserving whiteboard state.

---

## Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Room token authentication hashes and peer verification handshakes use transient server secrets. Room join identifiers are protected with cryptographic time signatures, preventing unauthorized bots from brute forcing private tactical squad rooms.
