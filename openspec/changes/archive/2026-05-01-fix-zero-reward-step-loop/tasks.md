## 1. Fix Zero Rewards in inference.py

- [x] 1.1 In `inference.py`, locate the line `step_reward = observation.get("reward", 0.0)` inside `run_task()`
- [x] 1.2 Replace it with two lines: capture `_raw_reward = data.get("reward")` and `step_reward = float(_raw_reward) if _raw_reward is not None else 0.0`
- [x] 1.3 Verify `cumulative_reward = observation.get("cumulative_reward", 0.0)` is unchanged (it is correctly read from `observation`)

## 2. Fix Repeating Terminal Output in run_service.py

- [x] 2.1 In `ui/backend/run_service.py`, locate the `api_run_stream` function's inner `event_generator` coroutine
- [x] 2.2 Add `offset = 0` before the `while True:` loop
- [x] 2.3 Change `lines = runner.get_output_since(0)` to `lines = runner.get_output_since(offset)`
- [x] 2.4 Add `offset += len(lines)` immediately after the `if lines:` check (before the `for line in lines` loop)

## 3. Verification

- [x] 3.1 Run a short inference run via the UI and confirm `[STEP]` log lines show non-zero rewards (e.g., `reward=0.11` or `reward=-0.03`) for relevant tool calls
- [x] 3.2 Confirm the terminal output in the UI does not repeat — each step's output appears exactly once
- [x] 3.3 Run `pytest tests/` and confirm all existing tests pass
