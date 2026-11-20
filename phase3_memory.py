#!/usr/bin/env python3
"""
CICLO Phase 3 - Episodic + procedural memory with consolidation.
- Episodic memory: every cycle stored (state, action, next_state, success).
- Procedural memory: generalized patterns derived from episodes every N cycles.
- Planner uses procedural memory before proposing.
- MNR metric: fraction of consolidated memories that are structurally new.
"""
import json, time, urllib.request, os
from datetime import datetime, timezone
from collections import defaultdict

URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:7b"
LOG = "logs/phase3_run.jsonl"
N = 30
CONSOLIDATE_EVERY = 5
ENV = {
    "door_closed": {"OPEN_DOOR": "door_open", "WAIT": "door_closed", "MOVE_FORWARD": "wall"},
    "door_open": {"OPEN_DOOR": "door_open", "WAIT": "door_open", "MOVE_FORWARD": "room"},
    "room": {"OPEN_DOOR": "room", "WAIT": "room", "MOVE_FORWARD": "room"},
    "wall": {"OPEN_DOOR": "wall", "WAIT": "wall", "MOVE_FORWARD": "wall"},
}
ACTIONS = ["OPEN_DOOR", "WAIT", "MOVE_FORWARD"]
GOAL = "room"

def call(prompt):
    p = json.dumps({"model": MODEL, "prompt": prompt, "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 15}}).encode()
    r = urllib.request.Request(URL, data=p, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read().decode()).get("response", "").strip()

def parse_action(raw):
    for a in ACTIONS:
        if a in raw.upper():
            return a
    return None

def consolidate(episodes):
    """Distill episodes into procedural rules: state -> action -> most common next_state."""
    rules = {}
    grouped = defaultdict(lambda: defaultdict(list))
    for e in episodes:
        if e["success"]:
            grouped[e["state"]][e["action"]].append(e["next_state"])
    for state, actions in grouped.items():
        best_action, best_next = None, None
        best_count = 0
        for act, nexts in actions.items():
            most_common = max(set(nexts), key=nexts.count)
            if len(nexts) > best_count:
                best_count = len(nexts)
                best_action, best_next = act, most_common
        if best_action:
            rules[state] = {"action": best_action, "next_state": best_next, "count": best_count}
    return rules

def main():
    os.makedirs("logs", exist_ok=True)
    state, history = "door_closed", []
    episodes = []
    procedural = {}
    seen_rules = set()
    novelty_events, total_consolidations = 0, 0
    valid_count, goal_at = 0, None
    start = time.time()

    with open(LOG, "a") as f:
        for i in range(N):
            t0 = time.time()

            # Planner consults procedural memory if available
            mem_hint = ""
            if state in procedural:
                mem_hint = f" Memory suggests: {procedural[state]['action']} leads to {procedural[state]['next_state']}."
            planner_raw = call(
                f"Role: PLANNER. Goal: reach 'room'. State: {state}. Last actions: {history[-3:]}.{mem_hint} "
                f"Pick the single best action from {ACTIONS}. Output only the action word."
            )
            planner_act = parse_action(planner_raw)

            # Executor independent
            executor_raw = call(
                f"Role: EXECUTOR. Goal: reach 'room'. State: {state}. Last actions: {history[-5:]}. "
                f"Pick the action most likely to change the state. Options: {ACTIONS}. Output only the action word."
            )
            executor_act = parse_action(executor_raw)

            # Simple resolution: planner wins, fallback executor
            chosen = planner_act or executor_act
            valid = chosen is not None
            if valid:
                valid_count += 1
                nxt = ENV[state][chosen]
            else:
                nxt = state; chosen = "INVALID"
            success = (nxt != state) or (nxt == GOAL)
            if nxt == GOAL and goal_at is None:
                goal_at = i

            # Episodic memory
            episode = {"cycle": i, "state": state, "action": chosen, "next_state": nxt,
                       "success": success, "planner": planner_act, "executor": executor_act}
            episodes.append(episode)

            # Consolidation every N cycles
            consolidated_now = False
            if (i + 1) % CONSOLIDATE_EVERY == 0:
                new_rules = consolidate(episodes)
                for s, r in new_rules.items():
                    key = (s, r["action"], r["next_state"])
                    if key not in seen_rules:
                        seen_rules.add(key)
                        novelty_events += 1
                procedural.update(new_rules)
                total_consolidations += 1
                consolidated_now = True

            entry = {"timestamp": datetime.now(timezone.utc).isoformat(), **episode,
                     "consolidated_now": consolidated_now, "procedural_size": len(procedural),
                     "latency_s": round(time.time() - t0, 2)}
            f.write(json.dumps(entry) + "\n"); f.flush()
            print(f"[{i+1}/{N}] {state} -> {chosen} -> {nxt} | P={planner_act} E={executor_act} mem={len(procedural)} {'CONS' if consolidated_now else ''}")
            history.append(chosen); state = nxt

    total = round(time.time() - start, 1)
    mnr = novelty_events / total_consolidations if total_consolidations > 0 else 0
    print(f"\nValid: {valid_count}/{N} ({100*valid_count/N:.1f}%)")
    print(f"Goal: {'yes at cycle ' + str(goal_at) if goal_at is not None else 'no'}")
    print(f"Consolidations: {total_consolidations}, novelty events: {novelty_events}, MNR={mnr:.2f}")
    print(f"Procedural rules: {len(procedural)}")
    print(f"Time: {total}s. Log: {LOG}")

if __name__ == "__main__":
    main()
