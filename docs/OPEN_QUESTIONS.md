# Open Questions — Smart Traffic

## Tracking Status
All core architectural, security, and packaging requirements for Tier-2 production hardening (C1–C9) have been resolved. The items below document future engineering considerations for advanced deployments.

---

### Q1: Multi-Agent Deep Reinforcement Learning (RL) Signal Policies
- **Question:** Should the rule-based `DensityManager` heuristics be extensible with pre-trained PyTorch or ONNX reinforcement learning policies (e.g. DQN, PPO)?
- **Status:** RESOLVED for v1.0.0 (Preserved verbatim classic density rules to maintain deterministic benchmark parity).
- **Recommendation for v2.0.0:** Implement an abstract `SignalPolicy` interface allowing pluggable neural signal policies alongside classic density rules.

---

### Q2: Dynamic Road Network Topology Graph (JSON/SUMO Import)
- **Question:** Should the 19-road network definition support external graph imports from SUMO (Simulation of Urban MObility) or GeoJSON?
- **Status:** RESOLVED for v1.0.0 (Preserved canonical 19-road 9-node grid in `core/network.py`).
- **Recommendation for v2.0.0:** Provide a network graph deserializer for custom user-defined road layouts.
