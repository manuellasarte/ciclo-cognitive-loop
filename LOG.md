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
