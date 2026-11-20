#!/usr/bin/env python3
"""
CICLO Phase 1 - Minimal cognitive loop (v2: with goal and progress signal).
No metacognition, no memory consolidation. Stability + valid action rate + goal progress.
"""
import json
import time
import urllib.request
import os
from datetime import datetime, timezone

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
MODEL = "qwen2.5:7b"
LOG_FILE = "logs/phase1_run_v2.jsonl"
N_CYCLES = 30

ENV = {
    "door_closed": {"OPEN_DOOR": "door_open", "WAIT": "door_closed", "MOVE_FORWARD": "wall"},
    "door_open": {"OPEN_DOOR": "door_open", "WAIT": "door_open", "MOVE_FORWARD": "room"},
    "room": {"OPEN_DOOR": "room", "WAIT": "room", "MOVE_FORWARD": "room"},
    "wall": {"OPEN_DOOR": "wall", "WAIT": "wall", "MOVE_FORWARD": "wall"},
}
VALID_ACTIONS = ["OPEN_DOOR", "WAIT", "MOVE_FORWARD"]
GOAL_STATE = "room"


def call_model(state: str, history: list, steps_since_goal: int) -> str:
    prompt = (
        f"You are a cognitive agent. Your goal is to reach the state 'room'. "
        f"Current state: {state}. "
        f"Last 5 actions: {history[-5:] if history else 'none'}. "
        f"Steps taken since start: {steps_since_goal}. "
        f"If you are stuck, try a different action. "
        f"Choose exactly one action from: {VALID_ACTIONS}. "
        f"Output only the action word, nothing else."
    )
    payload = json.dumps({
        "model": MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 10},
    }).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data.get("response", "").strip()


def parse_action(raw: str):
    for action in VALID_ACTIONS:
        if action in raw.upper():
            return action
    return None


def main():
    os.makedirs("logs", exist_ok=True)
    state = "door_closed"
    history = []
    valid_count = 0
    goal_reached_at = None
    start = time.time()

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for i in range(N_CYCLES):
            t0 = time.time()
            raw = call_model(state, history, i)
            latency = round(time.time() - t0, 2)
            action = parse_action(raw)
            valid = action is not None
            if valid:
                valid_count += 1
                next_state = ENV[state][action]
            else:
                next_state = state
                action = "INVALID"

            if next_state == GOAL_STATE and goal_reached_at is None:
                goal_reached_at = i

            entry = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "cycle": i,
                "state": state,
                "raw_response": raw,
                "action": action,
                "valid": valid,
                "next_state": next_state,
                "goal_reached": next_state == GOAL_STATE,
                "latency_s": latency,
            }
            f.write(json.dumps(entry) + "\n")
            f.flush()
            print(f"[{i+1}/{N_CYCLES}] {state} -> {action} -> {next_state} ({latency}s)")
            history.append(action)
            state = next_state

            if state == GOAL_STATE:
                print(f"  >>> GOAL REACHED at cycle {i}")
                break

    total = round(time.time() - start, 1)
    print(f"\nDone. Valid actions: {valid_count}/{i+1} ({100*valid_count/(i+1):.1f}%)")
    print(f"Goal reached: {'yes at cycle ' + str(goal_reached_at) if goal_reached_at is not None else 'no'}")
    print(f"Total time: {total}s. Log: {LOG_FILE}")


if __name__ == "__main__":
    main()
