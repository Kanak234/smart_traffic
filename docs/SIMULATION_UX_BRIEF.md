# Simulation & Visual UX Brief — Smart Traffic

## 1. Overview & Visual Direction
Smart Traffic combines a mathematical traffic simulation engine with a procedural 2D visualization layer rendered via Pygame. The presentation layer gives operators intuitive visual feedback on signal phasing, vehicle queues, pedestrian interactions, and emergency preemption.

The visual direction follows a clean, modern aesthetic:
- **Canvas:** 1200 × 780 pixels at 60 FPS with fixed-timestep interpolation.
- **Color Coding:** Standardized signal colors (Red `#E74C3C`, Amber `#F39C12`, Green `#2ECC71`).
- **Telemetry HUD:** Glassmorphism overlay displaying real-time metrics with high-contrast typography.
- **Lighting & Ambiance:** Dynamic day/night transition, vehicular headlight cones, brake lights, and weather simulation (rain particles and fog depth).

---

## 2. Interactive Keybindings & Controls

| Key | Function | Operator Feedback |
|---|---|---|
| `SPACE` | Pause / Resume | Freezes vehicle motion and signal countdowns |
| `+` / `−` | Time Scale | Speeds up or slows down simulation (0.25× to 8.0×) |
| `Tab` | Toggle Metrics Dashboard | Shows/hides glassmorphism HUD panel |
| `N` | Toggle Night Mode | Toggles dark ambiance with vehicular headlight cones |
| `C` | Toggle Day/Night Cycle | Enables continuous day-to-night diurnal progression |
| `R` | Toggle Rain Effect | Activates procedural rain particle animation |
| `F` | Toggle Fog Layer | Activates translucent volumetric fog overlay |
| `P` | Toggle Pedestrians | Spawns pedestrian agents obeying zebra crossings |
| `E` | Emergency Preemption | Toggles automatic priority green for emergency vehicles |
| `T` | Signal Labels | Toggles node and signal ID labels on the canvas |
| `S` | Screenshot | Captures current viewport to PNG file |
| `H` | Help Overlay | Displays interactive shortcut guide on-screen |
| `Q` / `Esc` | Quit & Generate Report | Terminates simulation and exports `density_report.png` |

---

## 3. Telemetry HUD & Dashboard Elements
When the metrics panel (`Tab`) is enabled, the top-right overlay presents:
1. **Simulation Clock:** Elapsed simulated time in `HH:MM:SS`.
2. **Throughput:** Vehicles cleared per minute (`veh/min`).
3. **Queue Metric:** Total vehicles currently queued at red signals.
4. **Average Delay:** Average wait time experienced by vehicles across the network.
5. **Congestion Meter:** Dynamic rating (`LOW` in green, `MODERATE` in amber, `HIGH` in red).
6. **Active Greens:** Count of simultaneously open signal phases.
7. **FPS Counter:** Real-time render loop frame rate.

---

## 4. Headless & CLI Interaction Paradigm
For automated testing, CI pipelines, and batch experimentation, Smart Traffic provides a headless interface that operates without an X11 window display:

```bash
# Capture demo frames headlessly to directory and exit
smart-traffic --demo-shots out/ --ticks 420

# Run automated simulation with fixed seed and quit after 10 seconds
smart-traffic --autoquit 10 --seed 42

# Print help and usage options
smart-traffic --help
```
