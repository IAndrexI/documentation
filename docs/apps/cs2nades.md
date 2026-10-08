# CS2 Tactical Stratbook & Nade Lineups

A specialized tactical companion and whiteboard for competitive Counter-Strike 2, featuring interactive 2D maps, vector trajectory rendering, and real-time multiplayer drawing synchronization.

---

## 1. System Topology & Data Flow

```mermaid
graph TD
    subgraph ClientLayer["🖥️ Frontend (Vue 3 + Vite)"]
        UI["Tactical Board UI"]
        CanvasEngine["Canvas 2D Vector Engine"]
        PiniaStore["Lineup & Auth Store (Pinia)"]
        Guard["Security Guard & Password Gate"]
    end

    subgraph EdgeLayer["🛡️ Network & Ingress"]
        CF["Cloudflare Zero Trust"]
        Nginx["Nginx Reverse Proxy (:80)"]
    end

    subgraph BackendLayer["⚡ Server Daemon (Node 24 Express)"]
        API["Express REST API (:5000)"]
        SocketHub["Socket.IO Multiplayer Hub"]
        AuthService["JWT & bcrypt Engine"]
        DB[(JSON / SQLite Storage)]
    end

    UI --> Guard
    Guard --> PiniaStore
    PiniaStore --> CanvasEngine
    CanvasEngine -->|HTTP Requests| CF
    CanvasEngine -->|WebSocket Packets| CF
    CF --> Nginx
    Nginx -->|/api/*| API
    Nginx -->|/socket.io/*| SocketHub
    API --> AuthService
    AuthService --> DB
    SocketHub -->|Room Sync Broadcast| UI
```

---

## 2. Technical Component Architecture

| Component | Stack | Responsibilities |
| :--- | :--- | :--- |
| **Interactive Minimap** | Vue 3 + HTML5 Canvas | Renders 2D top-down map blueprints for all 7 active duty maps (Mirage, Inferno, Nuke, Dust II, Ancient, Anubis, Train). Calculates real-time Bezier trajectory curves. |
| **Tactics Board** | Vector Canvas API | Allows drawing execute arrows, smoke clouds, flash radiuses, player positions, and text callouts. |
| **Sync Daemon** | Socket.IO + Node.js | Multi-client room synchronization allowing teammates or dual-screen mobile devices to see tactic changes in $<15\text{ms}$. |
| **Security Hardening** | OXC Minification + Sourcemap Stripping | Disables source map emission in production, minifies code, and prevents DevTools inspection. |

---

## 3. Realtime Tactic Drawing Sync Implementation

=== "Client Composable (Socket Sync)"

    ```typescript
    import { io, Socket } from 'socket.io-client';
    import { ref } from 'vue';

    export function useTacticsRoom(roomId: string) {
      const socket: Socket = io(import.meta.env.VITE_API_URL || '', {
        transports: ['websocket'],
        withCredentials: true
      });

      const boardElements = ref<any[]>([]);

      function emitDrawElement(element: { type: string; coords: number[]; color: string }) {
        socket.emit('tactic:draw', { roomId, element }); // (1)!
      }

      socket.on('tactic:update', (incomingElement) => {
        boardElements.value.push(incomingElement); // (2)!
      });

      return { emitDrawElement, boardElements };
    }
    ```

    1. Emits the vector coordinate packet to the server room channel.
    2. Reactively pushes incoming updates to the canvas rendering loop without page reload.

=== "Server WebSocket Hub"

    ```javascript
    io.on('connection', (socket) => {
      socket.on('join-room', (roomId) => {
        socket.join(roomId);
      });

      socket.on('tactic:draw', ({ roomId, element }) => {
        // Broadcasts drawing packet to all other connected clients in room
        socket.to(roomId).emit('tactic:update', element);
      });
    });
    ```
