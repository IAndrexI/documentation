# Source Code Deep Dive: `proxmox_rpc.py`

## ▪ File Metadata

- **Subsystem:** Proxmox Hypervisor Telemetry & Discord RPC
- **Path:** `apps/proxdiscord/proxmox_rpc.py`
- **Language / Runtime:** Python 3 (AsyncIO / `aiohttp` / `pypresence`)
- **Primary Responsibility:** Queries Proxmox VE REST API metrics asynchronously, normalizes cluster resource utilization, and broadcasts live status to Discord Rich Presence IPC.

---

## ⬡ General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `proxmox_rpc.py` streams live homelab telemetry into your Discord profile:
    
    1. **Asynchronous Polling:** Runs a non-blocking 15-second loop querying the Proxmox VE hypervisor REST API (`/api2/json/nodes/{node}/status`).
    2. **Metric Normalization:** Calculates cluster-wide CPU percentage, RAM allocation, and continuous node uptime.
    3. **Local IPC Bridge:** Connects to the local Discord desktop application via named pipe (`\\.\pipe\discord-ipc-0` on Windows or Unix domain socket on Linux).
    4. **Rich Presence Display:** Updates your Discord presence card with dynamic status details, elapsed uptime counters, and custom homelab cluster badges.

---

## ⬡ Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "🔎 Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full Python AsyncIO architecture, REST endpoints, and line by line breakdown required to understand and recreate the Proxmox Discord RPC daemon from scratch.

    ### Telemetry Polling Loop
    ```mermaid
    graph TD
        DaemonStart["Boot: asyncio.run(main())"] --> ConnectPVE["Authenticate with Proxmox VE REST API (/api2/json)"]
        ConnectPVE --> ConnectIPC["Connect pypresence RPC to local Discord IPC socket"]

        subgraph PollingLoop["Async Telemetry Polling Loop (15s Heartbeat)"]
            ConnectIPC --> FetchNode["GET /nodes/{node}/status"]
            FetchNode --> ParseMetrics["Extract cpu (0.0-1.0), memory.used, memory.total, uptime"]
            ParseMetrics --> FormatPresence["Construct Rich Presence Activity Payload"]
            FormatPresence --> UpdateRPC["rpc.update(state, details, large_image, timestamps)"]
            UpdateRPC --> SleepInterval["await asyncio.sleep(15)"]
            SleepInterval --> FetchNode
        end
    ```

    ---

    ### 1. Asynchronous Cluster Metric Poller (Lines 15–35)
    ```python linenums="15"
    async def fetch_cluster_metrics(session, base_url, node_name, headers):
        url = f"{base_url}/api2/json/nodes/{node_name}/status"
        async with session.get(url, headers=headers, ssl=False) as resp:
            if resp.status != 200:
                return None
            payload = await resp.json()
            data = payload.get("data", {})
            
            cpu_pct = round(data.get("cpu", 0) * 100, 1)
            mem_used = data.get("memory", {}).get("used", 0)
            mem_total = data.get("memory", {}).get("total", 1)
            mem_pct = round((mem_used / mem_total) * 100, 1)
            uptime_sec = data.get("uptime", 0)

            return {
                "cpu": cpu_pct,
                "mem": mem_pct,
                "uptime": uptime_sec
            }
    ```
    - **Lines 15–17 (`session.get(..., ssl=False)`)**: Asynchronously queries the Proxmox REST API node status endpoint without blocking other concurrent tasks. `ssl=False` allows self signed homelab TLS certificates without failing connections.
    - **Lines 22–26 (`cpu_pct` and `mem_pct`)**: Normalizes raw Proxmox decimal representations (where `0.184` represents $18.4\%$ CPU load) and converts raw memory bytes into human readable percentage ratios.

    ---

    ### 2. Discord IPC Rich Presence Broadcast (Lines 40–55)
    ```python linenums="40"
    async def update_discord_status(rpc, metrics):
        details_str = f"CPU: {metrics['cpu']}% | RAM: {metrics['mem']}%"
        state_str = f"Uptime: {metrics['uptime'] // 3600}h {((metrics['uptime'] % 3600) // 60)}m"

        rpc.update(
            state=state_str,
            details=details_str,
            large_image="pve_logo",
            large_text="Proxmox VE 9.2 Cluster",
            small_image="online_status",
            small_text="Node Online & Healthy"
        )
    ```
    - **Lines 41–42 (`details_str` & `state_str`)**: Formats high density performance telemetry into concise text strings compliant with Discord Rich Presence length limits.
    - **Lines 44–51 (`rpc.update(...)`)**: Transmits a formatted JSON IPC payload over the local Windows named pipe (`\\.\pipe\discord-ipc-0`), instantly updating the user's active Discord presence.

---

## [#] Anti Reverse Engineering Boundary

> [!NOTE] Implementation Abstraction
> Proxmox API tokens, cluster node names, and private network addresses are injected through encrypted environment configurations. Error handling logic applies jittered exponential backoff to prevent API rate limiting.
