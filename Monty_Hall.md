# 🐐 GOATED — Monty Hall Simulator

A Python desktop application built with Tkinter that lets you both **play** and **simulate** the classic Monty Hall probability problem.

---

## User Features

- **Play Mode** — Play the Monty Hall game interactively by clicking door buttons. A goat is revealed after your first pick, and you decide to stay or switch. Results are logged to an on-screen console.
- **Simulate Mode** — Run thousands of trials automatically with a chosen switch preference. A live progress bar and real-time cumulative win-rate line graph update as the simulation runs.
- **Live Results Panel** — Progress, Wins, and Losses bars update in real time alongside a final summary (win rate, loss rate, switch preference).
- **Play Again** — After each interactive round, a reset button re-arms all doors instantly.
- **Console Log** — A dark-themed scrollable console in Play mode logs every result with colour-coded win/loss messages.

---

## Core Functions

### `PlayMonteHall(door, switch) -> (won, shown_index, winning_door)`
The single source of truth for all game logic. Given the player's initial `door` choice and a `switch` boolean:
1. Randomly selects a `winning_door`.
2. Picks `shown_index` — a door Monty can safely reveal (neither the player's pick nor the winning door).
3. Computes `final_door` — the switched-to door, or the original if `switch=False`.
4. Returns `won` (bool), `shown_index` (int), and `winning_door` (int).

In **Play mode**, only `shown_index` and `winning_door` are consumed at Stage 1; `won` is intentionally discarded because the outcome is deferred to the player's actual Stage 2 click. In **Simulate mode**, only `won` is used.

### `SimMonteHall(N, switch) -> list[bool]`
Convenience wrapper that runs `N` calls to `PlayMonteHall()` with a random door each time, returning a list of boolean outcomes. Used as a clean standalone API; the GUI's `_simulate()` calls `PlayMonteHall()` directly to support live batched updates.

---

## Application Class — `SimApp(tk.Tk)`

### `__init__()`
Initialises the root window, sets instance state variables (`_play_door`, `_revealed_door`, `_winning_door`, `_graph_points`, `_graph_n`), and calls `_build_ui()`.

### `_build_ui()`
Constructs the entire widget tree once at startup:
- **Title label** — full-width at the top.
- **`body` frame** — uses `grid` with `columnconfigure(0, minsize=340)` to lock the left panel width and prevent the right panel from shifting when instruction text changes length.
- **`left_frame`** — contains the mode radio buttons, a horizontal separator, and two swappable sub-frames: `sim_frame` (Simulate inputs) and `play_frame` (door buttons + instruction label + Play Again button).
- **`right_frame`** — permanently visible results panel containing the RESULTS header, three `ttk.Progressbar` widgets with labels, and the `stats_label` summary.
- **`graph_outer`** — full-width bottom section (Simulate mode only) containing the `tk.Canvas` line graph, bound to `<Configure>` for responsive resizing.
- **`console_outer`** — full-width bottom section (Play mode only) containing a dark-themed read-only `tk.Text` widget with a scrollbar and colour tags for win/loss lines.

### `_on_mode_change()`
Called when the user switches between Simulate and Play via the radio buttons. Uses `pack_forget()` and `pack()` to swap the relevant left-panel sub-frame, show/hide `graph_outer` or `console_outer`, and calls `_reset_stats()` and `_reset_play_stage()` to clear stale state.

---

## Graph Methods

### `_on_canvas_resize(event)`
Bound to the canvas `<Configure>` event. Fires whenever the canvas is first rendered or resized. Deletes all canvas items and redraws axes and the current line from scratch at the correct dimensions.

### `_draw_graph_axes()`
Draws the static scaffold of the line graph onto the canvas:
- Five horizontal dashed gridlines at 0%, 33%, 50%, 67%, and 100% — the theoretically significant thresholds for the Monty Hall problem.
- Y-axis percentage labels.
- X-axis tick marks and labels at `0`, `N/4`, `N/2`, `3N/4`, and `N`, derived from `self._graph_n` so they always reflect the current simulation size.
- X and Y axis lines.

All items are tagged `"axes"` so they survive `delete("plot")` calls.

### `_redraw_graph()`
Redraws only the data line on every batch update. Deletes items tagged `"plot"`, then:
- Scales all `(trial, win_rate)` points in `_graph_points` to canvas coordinates using `self._graph_n` as the x-axis maximum — so the line always grows left-to-right across the full axis width as trials complete.
- Draws the polyline in green (`#69ff47`) with `smooth=True`.
- Places a small filled dot at the most recent data point.

### `_reset_graph()`
Clears `_graph_points` and deletes all `"plot"` tagged canvas items, leaving axes intact.

---

## Play Mode Methods

### `_reset_play_stage()`
Resets all Stage 1/2 state (`_play_door`, `_revealed_door`, `_winning_door` → `None`), restores all three door buttons to their default `🚪` appearance, hides the Play Again button, and sets the instruction label back to the initial prompt.

### `_on_door_click(idx)`
Handles both stages of an interactive round:

**Stage 1** (no door selected yet):
- Records `_play_door = idx` and highlights the chosen button.
- Calls `PlayMonteHall(idx, switch=True)` to obtain `shown_index` and `winning_door`; `won` is discarded.
- Disables and labels the revealed goat door.
- Updates the instruction label to prompt the final pick.

**Stage 2** (initial door already chosen):
- Ignores clicks on the revealed door.
- Computes `switched = (idx != _play_door)` and `won = (idx == _winning_door)`.
- Reveals all doors with car/goat icons and colours.
- Logs the result to the console via `_log()`.
- Shows the Play Again button.
- Dispatches `_update_ui()` on the main thread to update the results panel.

---

## Simulate Mode Methods

### `_validate()`
Checks inputs before running a simulation:
- Switch dropdown must not be `"-- Select --"`.
- N entry must be a positive integer.
Sets `error_var` with a descriptive message on failure, clears it on success.

### `_on_run()`
Entry point for a simulation run:
- Calls `_validate()`; aborts if invalid.
- Stores `self._graph_n = n` so the graph x-axis is scaled correctly before the first point arrives.
- Resets all progress bars, stats label, and graph.
- Redraws graph axes immediately with updated tick labels.
- Disables the Run button to prevent concurrent runs.
- Spawns `_simulate()` on a daemon background thread.

### `_simulate(will_switch, n)`
Runs on a background thread. Iterates `n` trials, calling `PlayMonteHall()` each time and accumulating `wins`. Every `max(1, n // 200)` iterations — or on the final trial — dispatches `_update_ui()` to the main thread via `self.after(0, ...)`. This batching prevents flooding the Tkinter event queue while keeping the UI visually smooth.

---

## Shared Methods

### `_update_ui(runs_done, n, wins, losses, option_y, will_switch)`
Always called on the main thread via `self.after()`. Updates:
- Progress, Win, and Loss bar values and labels.
- Appends `(runs_done, wins / runs_done)` to `_graph_points` and calls `_redraw_graph()`.
- On completion (`runs_done == n`), populates `stats_label` with the final summary and re-enables the Run button.

### `_reset_stats()`
Zeros all three progress bars, resets their text labels, clears `stats_label`, and calls `_reset_graph()`. Called at the start of every mode switch and every new simulation run.

### `_log(message, tag)`
Appends a line to the console `Text` widget. Temporarily sets the widget to `"normal"` state, inserts the message with the given colour tag (`"win"` or `"loss"`), scrolls to the bottom, then re-locks the widget to `"disabled"`.

---

## Application Flow
startup
└─ _build_ui()
└─ _on_mode_change() → default: Simulate mode shown

── SIMULATE MODE ──────────────────────────────────────────
User sets switch dropdown + N entry → clicks "Run Simulation"
└─ _on_run()
├─ _validate()
├─ stores _graph_n, resets bars + graph, redraws axes
└─ Thread: _simulate()
└─ every batch: self.after(0, _update_ui)
├─ updates bars + labels
├─ appends point → _redraw_graph()
└─ on final batch: shows summary, re-enables button

── PLAY MODE ──────────────────────────────────────────────
User clicks a door → _on_door_click() [Stage 1]
├─ PlayMonteHall() → captures shown_index, winning_door
└─ reveals goat door, prompts final pick

User clicks final door → _on_door_click() [Stage 2]
├─ resolves won, switched
├─ reveals all doors
├─ _log() → console
├─ shows Play Again button
└─ self.after(0, _update_ui) → updates results panel

User clicks "🔄 Play Again" → _reset_play_stage()