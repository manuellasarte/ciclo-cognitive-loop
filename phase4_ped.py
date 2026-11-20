#!/usr/bin/env python3
"""
CICLO Phase 4A - Formalize Plan-Execution Divergence (PED).
PED = |planner_action - hub_chosen_action| normalized.
Need a hub that can override planner to measure non-zero PED.
"""
import json, time, urllib.request, os
from datetime import datetime, timezone

URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:7b"
LOG = "logs/phase4_ped.jsonl"
N = 30
ENV = {
    "door_closed": {"OPEN_DOOR": "door_open", "WAIT": "door_closed", "MOVE_FORWARD": "wall"},
    "door_open": {"OPEN_DOOR": "door_open", "WAIT": "door_open", "MOVE_FORWARD": "room"},
    "room": {"OPEN_DOOR": "room", "WAIT": "room", "MOVE_FORWARD": "exit"},
    "wall": {"OPEN_DOOR": "wall", "WAIT": "wall", "MOVE_FORWARD": "wall"},
    "exit": {"OPEN_DOOR": "exit", "WAIT": "exit", "MOVE_FORWARD": "exit"},
}
ACTIONS = ["OPEN_DOOR", "WAIT", "MOVE_FORWARD"]
GOAL = "exit"

def call(prompt):
    p = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 15}}).encode()
    r = urllib.request.Request(URL, data=p, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read().decode()).get("response", "").strip()

def parse(raw):
    for a in ACTIONS:
        if a in raw.upper():
            return a
    return None

def hub_override(planner_act, executor_act, state, history, last_effective):
    """Hub overrides planner if executor disagrees AND planner's action was ineffective last time."""
    if planner_act and executor_act and planner_act != executor_act:
        if not last_effective:
            return executor_act, "override_executor"
        return planner_act, "planner_priority"
    if planner_act:
        return planner_act, "planner_only"
    if executor_act:
        return executor_act, "executor_only"
    return None, "none"

def main():
    os.makedirs("logs", exist_ok=True)
    state, history = "door_closed", []
    last_effective = True
    valid_count, goal_at = 0, None
    ped_values, resolutions = [], []
    start = time.time()
    with open(LOG, "a") as f:
        for i in range(N):
            t0 = time.time()
            planner_raw = call(f"Role: PLANNER. Goal: reach 'exit'. State: {state}. Last actions: {history[-3:]}. Pick one: {ACTIONS}. Output only the action.")
            planner_act = parse(planner_raw)
            executor_raw = call(f"Role: EXECUTOR. Goal: reach 'exit'. State: {state}. Last actions: {history[-5:]}. Pick one: {ACTIONS}. Output only the action.")
            executor_act = parse(executor_raw)
            chosen, resolution = hub_override(planner_act, executor_act, state, history, last_effective)
            # PED: 1 if planner != chosen, 0 if same
            ped = 1.0 if (planner_act and chosen and planner_act != chosen) else 0.0
            ped_values.append(ped); resolutions.append(resolution)
            latency = round(time.time() - t0, 2)
            valid = chosen is not None
            if valid:
                valid_count += 1
                nxt = ENV[state][chosen]
            else:
                nxt = state; chosen = "INVALID"
            if nxt == GOAL and goal_at is None: goal_at = i
            entry = {"timestamp": datetime.now(timezone.utc).isoformat(), "cycle": i,
                     "state": state, "planner": planner_act, "executor": executor_act,
                     "chosen": chosen, "resolution": resolution, "ped": ped,
                     "next_state": nxt, "valid": valid, "latency_s": latency}
            f.write(json.dumps(entry) + "\n"); f.flush()
            print(f"[{i+1}/{N}] {state} -> {chosen} -> {nxt} | P={planner_act} E={executor_act} res={resolution} PED={ped:.1f}")
            last_effective = (nxt != state)
            history.append(chosen); state = nxt
            if state == GOAL:
                print(f"  >>> GOAL at cycle {i}"); break
    total = round(time.time() - start, 1)
    n = len(ped_values)
    avg_ped = sum(ped_values) / n if n else 0
    from collections import Counter
    print(f"\nValid: {valid_count}/{n} ({100*valid_count/n:.1f}%)")
    print(f"Avg PED: {avg_ped:.3f} | Min: {min(ped_values):.1f} Max: {max(ped_values):.1f}")
    print(f"Resolutions: {dict(Counter(resolutions))}")
    print(f"Goal: {'yes at cycle ' + str(goal_at) if goal_at is not None else 'no'}")
    print(f"Time: {total}s. Log: {LOG}")

if __name__ == "__main__":
    main()
