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

### 2026-11-20 | Phase 2 (complete, with diagnostic note)
- phase2_workspace.py v1: tension=0.00 always (degenerate). Sub-agents had identical prompts.
- phase2_workspace.py v2: asymmetric information (planner proposes, critic vetoes, executor independent).
- 30-cycle run: 30/30 valid actions, goal reached at cycle 1, tension varies 0.50-1.00 (non-degenerate).
- CRITICAL FINDING: critic vetoes 30/30 times, even when planner and executor agree and action is correct.
- Hub resolves via critic_veto_executor in all cycles, but system remains stable (executor compensates).
- ETR criterion (non-trivial resolution) is MET: tension does not collapse to a fixed value.
- Decision: Phase 2 closed with diagnostic note. Critic miscalibration to be addressed in Phase 3 (memory) or via prompt adjustment if it persists.

### 2026-11-20 | Phase 3 (complete)
- phase3_memory.py: episodic memory (every cycle), procedural memory (consolidated every 5 cycles), planner uses memory hints.
- 30-cycle run: 30/30 valid, goal at cycle 1, MNR=0.50 (3 novelty events / 6 consolidations), procedural_size stabilized at 3.
- MNR criterion (intermediate regime, not 0 or 1) is MET.
- Memory is used: planner prompt includes "Memory suggests: ..." from cycle 5 onward.
- DIAGNOSTIC: environment is degenerate after goal (all actions from 'room' return to 'room'). Not a system failure, but future phases should add a post-goal state.
- Decision: Phase 3 closed. All three metrics (PED pending formalization, MNR non-degenerate, ETR non-degenerate) now have evidence. Proceed to Phase 4: formalize PED and run a longer stability test (72h) if hardware allows.

### 2026-11-20 | Phase 4A (complete)
- phase4_ped.py: formalizes Plan-Execution Divergence. Hub can override planner if planner's last action was ineffective and executor disagrees.
- First run: PED=0.000 always (override condition too narrow: required exact repetition).
- Patched: override triggers when last action was ineffective (state unchanged), not when repeated.
- Second run: 5/5 valid, goal at cycle 4, PED avg=0.200 (range 0.0-1.0), resolutions: planner_only=4, override_executor=1.
- PED criterion (non-degenerate, intermediate regime) is MET.
- Decision: Phase 4A closed. All three metrics (PED, MNR, ETR) now have non-degenerate evidence. Proceed to Phase 4B: 72h stability test in background.
