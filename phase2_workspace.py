#!/usr/bin/env python3
"""
CICLO Phase 2 v2 - Metacognitive workspace with asymmetric information.
Planner: proposes action from state+goal.
Critic: sees planner's proposal, can VETO or ACCEPT (outputs "VETO" or "ACCEPT").
Executor: sees state+history only, proposes independently.
Hub: if critic vetoes, executor's action wins; if accepts, planner wins if agrees with executor, else majority.
"""
import json, time, urllib.request, os
from datetime import datetime, timezone

URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:7b"
LOG = "logs/phase2_run_v2.jsonl"
N = 30
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
                    "options": {"temperature": 0.4, "num_predict": 15}}).encode()
    r = urllib.request.Request(URL, data=p, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(r, timeout=120) as resp:
        return json.loads(resp.read().decode()).get("response", "").strip()

def parse_action(raw):
    for a in ACTIONS:
        if a in raw.upper():
            return a
    return None

def main():
    os.makedirs("logs", exist_ok=True)
    state, history, valid_count, goal_at = "door_closed", [], 0, None
    start = time.time()
    with open(LOG, "a") as f:
        for i in range(N):
            t0 = time.time()
            # 1. Planner: state + goal + last 3 actions
            planner_raw = call(
                f"Role: PLANNER. Goal: reach 'room'. State: {state}. Last actions: {history[-3:]}. "
                f"Pick the single best action from {ACTIONS}. Output only the action word."
            )
            planner_act = parse_action(planner_raw)

            # 2. Critic: sees planner's proposal, can VETO if it repeats a non-progressing action
            critic_raw = call(
                f"Role: CRITIC. State: {state}. Last actions: {history[-3:]}. "
                f"Planner proposes: {planner_act}. "
                f"If this action repeats the last action and the state has not changed, output VETO. "
                f"Otherwise output ACCEPT. Output only VETO or ACCEPT."
            )
            critic_veto = "VETO" in critic_raw.upper()

            # 3. Executor: state + full history, independent proposal
            executor_raw = call(
                f"Role: EXECUTOR. Goal: reach 'room'. State: {state}. Last actions: {history[-5:]}. "
                f"Pick the action most likely to change the state. Options: {ACTIONS}. Output only the action word."
            )
            executor_act = parse_action(executor_raw)

            # 4. Hub: resolve
            if critic_veto and executor_act:
                chosen = executor_act
                resolution = "critic_veto_executor"
            elif planner_act and executor_act and planner_act == executor_act:
                chosen = planner_act
                resolution = "consensus"
            elif planner_act and executor_act:
                chosen = planner_act  # planner wins ties if no veto
                resolution = "planner_priority"
            elif planner_act:
                chosen = planner_act
                resolution = "planner_only"
            elif executor_act:
                chosen = executor_act
                resolution = "executor_only"
            else:
                chosen = None
                resolution = "none"

            # Epistemic tension: disagreement between planner and executor, plus veto
            tension = 0.0
            if planner_act and executor_act and planner_act != executor_act:
                tension += 0.5
            if critic_veto:
                tension += 0.5

            latency = round(time.time() - t0, 2)
            valid = chosen is not None
            if valid:
                valid_count += 1
                nxt = ENV[state][chosen]
            else:
                nxt = state
                chosen = "INVALID"

            if nxt == GOAL and goal_at is None:
                goal_at = i

            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(), "cycle": i,
                "state": state, "planner": planner_act, "critic_veto": critic_veto,
                "executor": executor_act, "chosen": chosen, "resolution": resolution,
                "tension": tension, "next_state": nxt, "valid": valid, "latency_s": latency,
            }
            f.write(json.dumps(entry) + "\n"); f.flush()
            print(f"[{i+1}/{N}] {state} -> {chosen} -> {nxt} | P={planner_act} E={executor_act} V={critic_veto} T={tension:.2f} ({latency}s)")
            history.append(chosen)
            state = nxt
            if state == GOAL:
                print(f"  >>> GOAL at cycle {i} (continuing for diagnostics)")

    total = round(time.time() - start, 1)
    n = i + 1
    print(f"\nValid: {valid_count}/{n} ({100*valid_count/n:.1f}%)")
    print(f"Goal: {'yes at cycle ' + str(goal_at) if goal_at is not None else 'no'}")
    print(f"Time: {total}s. Log: {LOG}")

if __name__ == "__main__":
    main()
