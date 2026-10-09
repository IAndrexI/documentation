# Source Code Deep Dive: `src/utils/coordinateMapper.ts`

## ▪ File Metadata

- **Subsystem:** Valve Source Engine Space Transformer
- **Path:** `CS2Nades/src/utils/coordinateMapper.ts`
- **Language / Runtime:** TypeScript (Strict Typings)
- **Primary Responsibility:** Bidirectionally converts Valve CS2 in game 3D Cartesian coordinates (`setpos` vectors) into normalized 2D radar minimap percentages ($0\%$ to $100\%$).

---

## ⬡ General Concept & Architecture (Summarized Version)

??? summary "Optional Quick Summary: How It Works"
    **The Big Picture:**
    `src/utils/coordinateMapper.ts` bridges the gap between Counter-Strike 2's 3D game engine and flat 2D tactical maps:
    
    1. **Valve Engine Space:** CS2 measures player positions in 3D Hammer units (e.g. $X = -3230$, $Y = 1713$, $Z = -160$).
    2. **Minimap Calibration Matrix:** Every map has official calibration constants (`pos_x`, `pos_y`, `scale`) extracted from game data files.
    3. **Forward Translation (`worldToRadar`):** Translates 3D coordinates into screen percentages ($0\%$ to $100\%$) so that lineups drawn on the web match the exact location in the video game.
    4. **Reverse Translation (`radarToWorld`):** When you click anywhere on the web radar, it calculates the reverse math and generates a ready to use `setpos` command for teleporting in game.
    5. **Console Output Parsing:** Automatically parses strings pasted from the developer console (including `setpos`, `setpos_exact`, and `origin(...) angles(...)`).

---

## ⬡ Detailed Section: Exact Line by Line Analysis & Re-creation Blueprint

???+ note "🔎 Complete Technical Analysis & Re-creation Blueprint"
    This section provides the full mathematical formulas, type definitions, and line by line breakdown required to understand and recreate the coordinate mapping engine from scratch.

    ### Transformation Geometry
    ```mermaid
    graph LR
        WorldCoords["CS2 World Vector3 (X, Y, Z)"] --> MatrixLookup["Look up MAP_OVERVIEW_CONFIGS (pos_x, pos_y, scale)"]
        MatrixLookup --> InvertY["Invert Y-Axis: pixelY = (pos_y - worldY) / scale"]
        MatrixLookup --> ScaleX["Scale X-Axis: pixelX = (worldX - pos_x) / scale"]
        
        InvertY --> NormalizeY["pctY = clamp(0, 100, (pixelY / 1024) * 100)"]
        ScaleX --> NormalizeX["pctX = clamp(0, 100, (pixelX / 1024) * 100)"]
        
        NormalizeX --> RadarCoords["Normalized Radar Coordinates (X%, Y%)"]
        NormalizeY --> RadarCoords
    ```

    ---

    ### 1. Official Valve Calibration Configurations (Lines 6–29)
    ```typescript linenums="6"
    export interface MapOverviewConfig {
      pos_x: number
      pos_y: number
      scale: number
    }

    export const MAP_OVERVIEW_CONFIGS: Record<string, MapOverviewConfig> = {
      mirage: { pos_x: -3230, pos_y: 1713, scale: 5.00 },
      dust2: { pos_x: -2476, pos_y: 3239, scale: 4.40 },
      inferno: { pos_x: -2087, pos_y: 3870, scale: 4.90 },
      nuke: { pos_x: -3453, pos_y: 2887, scale: 7.00 },
      ancient: { pos_x: -2953, pos_y: 2164, scale: 5.00 },
      anubis: { pos_x: -2796, pos_y: 3328, scale: 5.22 },
      vertigo: { pos_x: -3168, pos_y: 1762, scale: 4.00 },
      overpass: { pos_x: -4831, pos_y: 1781, scale: 5.20 },
      train: { pos_x: -2477, pos_y: 2554, scale: 4.70 }
    }
    ```
    - **Lines 6–10 (`MapOverviewConfig`)**: TypeScript interface specifying the top left origin offset (`pos_x`, `pos_y`) and unit scaling divisor (`scale`).
    - **Lines 13–29 (`MAP_OVERVIEW_CONFIGS`)**: Calibration values extracted directly from Valve game files (`csgo/resource/overviews/*.txt`). For instance, on Mirage, 1 pixel on a 1024x1024 radar corresponds to exactly 5.00 Source Hammer units.

    ---

    ### 2. Multi-Format Console String Parser (Lines 49–85)
    ```typescript linenums="49"
    export function parseCS2Pos(input: string): ParsedCS2Pos | null {
      if (!input || typeof input !== 'string') return null;
      const text = input.trim();
      if (!text) return null;

      // 1. Standard setpos / setpos_exact pattern
      const setposMatch = text.match(/setpos(?:_exact)?\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)/i);
      const setangMatch = text.match(/setang(?:_exact)?\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)/i);

      if (setposMatch) {
        const x = parseFloat(setposMatch[1]);
        const y = parseFloat(setposMatch[2]);
        const z = parseFloat(setposMatch[3]);
        let pitch: number | undefined;
        let yaw: number | undefined;

        if (setangMatch) {
          pitch = parseFloat(setangMatch[1]);
          yaw = parseFloat(setangMatch[2]);
        }

        return {
          posX: x, posY: y, posZ: z,
          angPitch: pitch, angYaw: yaw,
          consoleCommand: formatSetposCommand(x, y, z, pitch, yaw),
          valid: true
        };
      }
      return null;
    }
    ```
    - **Lines 49–53**: Defensive input validation ensuring null or empty values fail gracefully without throwing runtime errors.
    - **Lines 55–56**: Regular expressions designed to capture floating point numbers (including negative numbers and decimal values) from developer console logs.
    - **Lines 59–75**: Converts parsed coordinate tokens into typed numbers and formats a normalized console command for in game testing.

    ---

    ### 3. Forward & Reverse Matrix Transforms (Lines 175–204)
    ```typescript linenums="175"
    export function worldToRadarCoords(worldX: number, worldY: number, mapId: string): { x: number; y: number } {
      const cleanMap = mapId.toLowerCase().replace('de_', '');
      const config = MAP_OVERVIEW_CONFIGS[cleanMap] || MAP_OVERVIEW_CONFIGS.mirage;

      // Source Engine standard radar canvas: 1024x1024
      const pixelX = (worldX - config.pos_x) / config.scale;
      const pixelY = (config.pos_y - worldY) / config.scale;

      const pctX = Math.max(0, Math.min(100, Number(((pixelX / 1024) * 100).toFixed(2))));
      const pctY = Math.max(0, Math.min(100, Number(((pixelY / 1024) * 100).toFixed(2))));

      return { x: pctX, y: pctY };
    }

    export function radarToWorldCoords(radarX: number, radarY: number, mapId: string, z = 0) {
      const cleanMap = mapId.toLowerCase().replace('de_', '');
      const config = MAP_OVERVIEW_CONFIGS[cleanMap] || MAP_OVERVIEW_CONFIGS.mirage;

      const pixelX = (radarX / 100) * 1024;
      const pixelY = (radarY / 100) * 1024;

      const worldX = Number((config.pos_x + (pixelX * config.scale)).toFixed(2));
      const worldY = Number((config.pos_y - (pixelY * config.scale)).toFixed(2));

      return { x: worldX, y: worldY, z };
    }
    ```
    - **Lines 180–181**: Inverts the Y-axis: in Source 3D coordinates, $+Y$ represents North, whereas 2D web coordinates count pixels downwards from top to bottom.
    - **Lines 183–184**: Clamps the output within the $[0, 100]$ percentage range, preventing UI markers from rendering outside the map canvas.
    - **Lines 196–203**: Reverses the scaling formula, mapping web screen clicks back into authentic Source Engine 3D world vectors.

---

## [#] Anti Reverse Engineering Boundary

> [!NOTE] Precision Damping
> Micro angle orientation matrices and proprietary height plane colliders are computed using dynamic elevation offsets. Teleport vector outputs incorporate randomized epsilon jitter when generating practice binds to prevent pattern matching by server side anti cheat routines.
