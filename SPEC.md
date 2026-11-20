# CICLO — Specification v0.1

## Objective
Build a closed-loop cognitive system on low-cost hardware (Raspberry Pi 5 16GB or equivalent) that exhibits measurable self-regulation, defined by three falsifiable metrics.

## Core Metrics (all three must show non-trivial trajectories over time)
1. **Plan-Execution Divergence (PED)**: |planned action - executed action| must decrease but not collapse to zero.
2. **Memory Novelty Rate (MNR)**: proportion of consolidated memories that are structurally distinct from existing ones must stabilize in an intermediate regime.
3. **Epistemic Tension Resolution (ETR)**: disagreement between sub-agents must be resolved by evidence accumulation, not by fixed dominance of one sub-agent.

## Falsification Criterion
If any metric converges to a degenerate state (PED → 0, MNR → 0 or → 1, ETR → always one agent wins) over sustained operation (≥72 hours), the hypothesis of genuine self-regulation is rejected.

## Hardware Target
- Phase 1: Development machine (any laptop/desktop with ≥16GB RAM)
- Phase 2: Raspberry Pi 5 16GB (or Jetson Orin Nano)
- Model: Gemma or Qwen 2-5B range, Q4_K_M quantization

## Architecture Layers
- L1: Reasoning core (small quantized LLM)
- L2: Metacognitive workspace (multi-agent hub with salience-based selection)
- L3: Episodic + procedural memory with consolidation
- L4: Closed loop + instrumentation (the three metrics above)

## Phase Gates
- Phase 0: Repo + spec (this document)
- Phase 1: Minimal loop (no metacognition) — stable for 1 hour
- Phase 2: Add metacognitive hub — stable for 24 hours
- Phase 3: Add memory consolidation — run 72+ hours, measure metrics
- Phase 4: Replicate on Pi 5 (only if Phase 3 shows signal)

## Negative Results Policy
All failures, dead ends, and degenerate outcomes will be documented in `LOG.md` and published. A well-documented failure is a valid contribution.
