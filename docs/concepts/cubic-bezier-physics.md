# Mathematical Concept: Cubic Bézier Trajectory Curves & Coordinate Mapping

In Counter-Strike 2, grenade utilities follow ballistic trajectories governed by the physics engine: constant gravitational acceleration ($g = 800\text{ hammer units/s}^2$), initial velocity vectors, air drag, and restitution bounce coefficients. To project these trajectories onto a flat 2D web tactical board in realtime without bogging down the browser with full numerical physics integration, we use **Cubic Bézier Parametric Splines** combined with **Source Engine Calibration Matrices**.

```mermaid
graph LR
    subgraph WorldSpace["CS2 Engine World Units (Hammer Units)"]
        ThrowOrigin["Throw Origin P0 (Xw, Yw, Zw)"]
        TargetImpact["Detonation P3 (Xw, Yw, Zw)"]
    end

    subgraph MatrixTransform["Valve Map Overview Transformation"]
        OverviewConfig["Overview Calibration (pos_x, pos_y, scale)"]
        ThrowOrigin --> OverviewConfig
        TargetImpact --> OverviewConfig
        OverviewConfig --> ScreenP0["Canvas Start P0 (x, y)"]
        OverviewConfig --> ScreenP3["Canvas End P3 (x, y)"]
    end

    subgraph BezierElevator["Normal Vector Elevation Engine"]
        Normal["Unit Normal: n = [-dy, dx] / ||d||"]
        Apex["Apex Height = distance * 0.35"]
        ScreenP0 + ScreenP3 --> Normal
        Normal + Apex --> ControlP1["Control Point P1"]
        Normal + Apex --> ControlP2["Control Point P2"]
    end

    subgraph Renderer["HTML5 Canvas 2D Pipeline"]
        ControlP1 --> BezierCall["ctx.bezierCurveTo(P1.x, P1.y, P2.x, P2.y, P3.x, P3.y)"]
        ControlP2 --> BezierCall
        BezierCall --> DashedFlight["High-Refresh-Rate Trajectory Dash + Blast Circle"]
    end
```

---

## Technical Derivations & Mathematical Foundations

### 1. Source Engine Coordinate Matrix
In Counter-Strike 2, map geometry is measured in Hammer units ($1 \text{ unit} = 0.75 \text{ inches} \approx 1.905 \text{ cm}$). Valve describes radar overviews using three parameters in `csgo/resource/overviews/<mapname>.txt`:
- `pos_x`: The X world coordinate aligned with the leftmost pixel of the 1024x1024 radar bitmap.
- `pos_y`: The Y world coordinate aligned with the topmost pixel of the radar bitmap.
- `scale`: World units represented by 1 pixel on the 1024x1024 canvas.

#### Forward Transform (World to Screen Percentage)
Given player world coordinates $(X_w, Y_w)$:

$$\text{pixel}_x = \frac{X_w - \text{pos\_x}}{\text{scale}}$$

$$\text{pixel}_y = \frac{\text{pos\_y} - Y_w}{\text{scale}}$$

$$\text{pct}_x = \operatorname{clamp}\left(0, 100, \frac{\text{pixel}_x}{1024} \times 100\right)$$

$$\text{pct}_y = \operatorname{clamp}\left(0, 100, \frac{\text{pixel}_y}{1024} \times 100\right)$$

Notice that in 3D world space, $+Y$ extends northward, while on 2D web screens pixel indices increase downward. Subtracting $Y_w$ from $\text{pos\_y}$ handles this vertical axis inversion.

---

### 2. Cubic Bézier Curve Geometry
A cubic Bézier curve is defined parametrically over $t \in [0, 1]$ using Bernstein basis polynomials of degree 3:

$$B(t) = (1-t)^3 P_0 + 3(1-t)^2 t P_1 + 3(1-t) t^2 P_2 + t^3 P_3$$

Where:
- $P_0$: Origin coordinates (thrower position).
- $P_3$: Terminus coordinates (grenade detonation point).
- $P_1, P_2$: Control vertices establishing flight curvature.

To produce a natural parabolic flight arc without requiring complex vertical perspective projection, we construct a 2D normal vector $\vec{n}$ perpendicular to the displacement vector $\vec{d} = P_3 - P_0$:

$$\vec{n} = \begin{bmatrix} -d_y \\ d_x \end{bmatrix} \cdot \frac{1}{\|\vec{d}\|}$$

We then scale the apex elevation proportionally to distance ($h = \|\vec{d}\| \times 0.35$):

$$P_1 = P_0 + \frac{1}{3} \vec{d} + h \vec{n}$$

$$P_2 = P_0 + \frac{2}{3} \vec{d} + h \vec{n}$$

This gives an authentic flight trajectory with clean curvature that renders at 144+ FPS on client browsers.

---

## Technical References & Authoritative Sources

1. **Valve Developer Community**: *Overview Maps Configuration and Calibration Standards*  
   Official Wiki: [https://developer.valvesoftware.com/wiki/Counter-Strike:_Global_Offensive_Overviews](https://developer.valvesoftware.com/wiki/Counter-Strike:_Global_Offensive_Overviews)
2. **Valve Developer Community**: *Dimensions and Hammer Units in Source 2*  
   Documentation: [https://developer.valvesoftware.com/wiki/Dimensions](https://developer.valvesoftware.com/wiki/Dimensions)
3. **W3C / WHATWG HTML Living Standard**: *The 2D Canvas Context: `CanvasRenderingContext2D.bezierCurveTo`*  
   Specification: [https://html.spec.whatwg.org/multipage/canvas.html#dom-context-2d-beziercurveto](https://html.spec.whatwg.org/multipage/canvas.html#dom-context-2d-beziercurveto)
4. **Farin, Gerald (2002)**: *Curves and Surfaces for CAGD: A Practical Guide* (5th Edition, Morgan Kaufmann).
