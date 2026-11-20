# Experiment Log

## Format
Each entry: Date | Phase | What was done | Result | Decision

## Entries

### 2026-11-20 | Phase 0 (complete)
- Repository created, README and SPEC.md added.
- Kaggle notebook created (public, empty at this point).
- ThinkPad X220 (8GB) failed: OOM killer when loading gemma3:4b.
- Decision: move to IONOS server.

### 2026-11-20 | Phase 0→1 transition (complete)
- IONOS server verified: 47GB RAM available, AMD EPYC 12 cores, no GPU.
- Ollama 0.40.16 installed.
- qwen2.5:7b downloaded (4.7GB).
- Simple instruction test: output "CICLO READY" exactly.
- Structured instruction test: output "OPEN_DOOR" (valid action).
- Initial load time: 16.5s.
- Result: L1 (reasoning core) validated. Hardware sufficient for Phase 1.
- Decision: proceed to Phase 1 (minimal loop implementation).

### 2026-11-20 | Phase 1 (complete)
- phase1_loop.py v1 executed: 20/20 valid actions, but agent stuck in door_open (no goal signal).
- phase1_loop.py v2 executed: added goal ("reach room") + progress signal (last 5 actions, step count).
- Result: 4/4 valid actions (100%), goal reached at cycle 3, latency 1.7-2.7s.
- Log: logs/phase1_run_v2.jsonl
- Decision: Phase 1 closed. Proceed to Phase 2 (metacognitive workspace).
