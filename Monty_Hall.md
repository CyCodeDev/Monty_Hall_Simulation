# 🐐 GOATED — Monty Hall Simulator

## Overview

GOATED is an interactive desktop GUI application built with Python and Tkinter that
demonstrates the Monty Hall problem. It supports two modes:

- **Simulate Mode** — runs N automated trials and visualizes the cumulative win rate
  in real time via a live line graph and progress bars
- **Play Mode** — lets the user play the Monty Hall game interactively, door by door,
  with a running console log of results

---

## App Capabilities

### Simulate Mode
- Select whether the simulated player always switches or never switches
- Enter any number of trials (N)
- Watch three progress bars update in real time: Progress, Wins, Losses
- Watch a live cumulative win rate line graph grow left-to-right as trials complete
- X-axis of the graph is scaled exactly to N (the user's input), with labeled tick marks
- Final stats summary displayed on completion: win rate, loss rate, switch preference

### Play Mode
- Pick one of three doors in Stage 1
- Monty reveals a goat behind one of the remaining doors
- Pick a final door in Stage 2 (switch or stay)
- All three doors are revealed with their outcomes (car or goat)
- A dark-themed console at the bottom logs every round result in color:
  - Green for wins
  - Red for losses
- Results panel updates after every round showing cumulative wins/losses
- Play Again button resets the board for a new round

---

## Code Structure & Flow

### Module-Level

#### `PlayMonteHall(door, switch) -> (won, shown_index, winning_door)`

The core game logic function. Given the player's initial door choice and a switch
preference, it:

1. Randomly selects a `winning_door`
2. Picks a `shown_index` — a door that is neither the player's pick nor the winning door
   (this is the goat Monty reveals)
3. Computes `final_door` — the door the player ends up on after switching or staying
4. Returns a 3-tuple:
   - `won` (bool) — whether `final_door == winning_door`
   - `shown_index` (int) — the goat door Monty revealed
   - `winning_door` (int) — where the car actually is

This is the single source of truth for all game logic. Both Simulate and Play modes
use it, but consume different parts of its return value.

---

### Class: `SimApp(tk.Tk)`

The entire GUI lives inside this class, which extends `tk.Tk` directly.

#### `__init__()`

Initializes instance state variables:

- `_play_door` — the door the user picked in Stage 1 (Play mode)
- `_revealed_door` — the goat door Monty opened (Play mode)
- `_winning_door` — where the car is (Play mode)
- `_graph_points` — list of `(trial, win_rate)` tuples accumulated during simulation
- `_graph_n` — the total N for the current simulation run, used to scale the x-axis

Calls `_build_ui()` to construct the interface.

---

### UI Construction

#### `_build_ui()`

Constructs the entire widget tree. The layout is divided into three regions:

```
+---------------------------------------------+
|           GOATED  (title)                   |
+--------------------+----+--------------------+
|   left_frame       | |  |   right_frame      |
|   (mode + inputs)  | |  |   (RESULTS panel)  |
+--------------------+----+--------------------+
|   graph_outer  <-- Simulate mode only        |
|   console_outer <-- Play mode only           |
+---------------------------------------------+
```

**Title** — packed at the top of the root window.

**`body` frame** — uses `grid` internally with `columnconfigure(0, minsize=340)` to
lock the left column to a fixed minimum width, preventing `right_frame` from shifting
horizontally when instruction text changes length during Play mode.

**`left_frame`** — contains the mode radio buttons, a horizontal separator, and two
swappable sub-frames: `sim_frame` and `play_frame`. Only one is visible at a time,
swapped by `_on_mode_change()`.

**`right_frame`** — always visible; contains the RESULTS label, three labeled progress
bars (Progress, Wins, Losses), and a `stats_label` for the final summary text.

**`graph_outer`** — a direct child of the root window (`self`), packed with
`fill="x", side="bottom"`. Contains the `graph_canvas` (a `tk.Canvas`) which renders
the live line graph. Shown only in Simulate mode.

**`console_outer`** — also a direct child of `self`, packed with
`fill="x", side="bottom"`. Contains a dark-themed `tk.Text` widget with a scrollbar.
Shown only in Play mode.

---

### Mode Management

#### `_on_mode_change()`

Called whenever the user clicks a mode radio button. It:

1. Calls `_reset_stats()` to clear all progress bars, labels, and the graph
2. In **Simulate mode**: hides `play_frame` and `console_outer`, shows `sim_frame`
   and `graph_outer`
3. In **Play mode**: hides `sim_frame` and `graph_outer`, shows `play_frame` and
   `console_outer`, then calls `_reset_play_stage()`

Uses `pack_forget()` / `pack()` to show and hide frames without destroying them.

---

### Simulate Mode Flow

```
User clicks "Run Simulation"
        |
        v
_on_run()
  |-- validates input via _validate()
  |-- stores N in self._graph_n
  |-- resets progress bars and graph
  |-- redraws axes with new N tick labels
  +-- spawns background thread -> SimMonteHall()
                |
                v
        SimMonteHall(will_switch, n)       [background thread]
          |-- loops i = 1..n
          |     |-- calls PlayMonteHall(random door, will_switch)
          |     |-- accumulates wins
          |     +-- every batch: self.after(0, _update_ui, ...)
                              |
                              v
                      _update_ui(...)        [main thread]
                        |-- updates progress bar values
                        |-- updates win/loss label text
                        |-- appends (trial, win_rate) to _graph_points
                        |-- calls _redraw_graph()
                        +-- on final batch: writes stats_label,
                                            re-enables run_btn
```

#### `_validate()`

Checks that the switch dropdown has a real selection (not `"-- Select --"`) and that
the N entry is a positive integer. Sets `error_var` text if invalid, clears it if valid.

#### `SimMonteHall(will_switch, n)`

Runs on a background daemon thread. Iterates N trials, calling `PlayMonteHall()` each
time. Batches UI updates using `self.after(0, ...)` to safely schedule them on the
main thread. Batch size is `max(1, n // 200)` so the graph updates approximately 200
times regardless of N.

#### `_update_ui(runs_done, n, wins, losses, option_y, will_switch)`

Always called on the main thread via `after()`. Updates all three progress bars, their
text labels, appends a new data point to `_graph_points`, and triggers `_redraw_graph()`.
On the final batch (`runs_done == n`), fills in the stats summary and re-enables the
Run button.

---

### Graph Rendering

#### `_draw_graph_axes()`

Draws the static parts of the chart onto the canvas:

- Horizontal dashed gridlines at 0%, 33%, 50%, 67%, and 100% — the theoretically
  significant win rates for the Monty Hall problem
- Y-axis percentage labels on the left
- X-axis tick marks and trial number labels derived from `self._graph_n`
- The two axis lines (x and y)

All items are tagged `"axes"` so they persist across graph redraws.

#### `_redraw_graph()`

Deletes only `"plot"`-tagged canvas items (leaving axes intact), then redraws the full
polyline from all points in `_graph_points`. X positions are scaled using
`trial / self._graph_n` so the line always grows across the full axis width regardless
of how many batches have completed. Draws a small filled circle at the latest data point.

#### `_on_canvas_resize(event)`

Bound to the canvas `<Configure>` event, which fires on first render and on any window
resize. Deletes everything and redraws both axes and the current graph line so the
chart always fills the available width correctly.

#### `_reset_graph()`

Clears `_graph_points` and deletes all `"plot"` items from the canvas. Called at the
start of each new run and when switching modes.

---

### Play Mode Flow

```
User clicks a door (Stage 1)
        |
        v
_on_door_click(idx)
  |-- stores idx as _play_door
  |-- highlights the chosen door button
  |-- calls PlayMonteHall(idx, switch=True)
  |     +-- returns (_, shown_index, winning_door)
  |           won is intentionally ignored —
  |           user has not made their final pick yet
  |-- stores shown_index as _revealed_door
  |-- stores winning_door as _winning_door
  +-- disables revealed door button, shows goat label,
      updates instruction text

User clicks a second door (Stage 2)
        |
        v
_on_door_click(idx)  [same handler, different branch]
  |-- ignores click if idx == _revealed_door
  |-- computes switched = (idx != _play_door)
  |-- computes won = (idx == _winning_door)
  |-- reveals all three doors in the UI
  |-- updates instruction label with win/loss result
  |-- calls _log() to append result to the console
  |-- shows the Play Again button
  +-- schedules _update_ui(1, 1, won, not won, ...) via after()
```

**Why `switch=True` in Stage 1's `PlayMonteHall()` call?**

In Play mode, `PlayMonteHall()` is called solely to obtain `shown_index` and
`winning_door` from its internal randomisation logic. The `won` return value is
discarded with `_` because the actual outcome depends on the user's Stage 2 click,
not a predetermined switch flag. Passing `switch=True` satisfies the function's
internal computation of `final_door` without affecting the values we actually use.

#### `_reset_play_stage()`

Resets all three door buttons to their default door state, clears the instruction
label, hides the Play Again button, and nulls out `_play_door`, `_revealed_door`,
and `_winning_door`. Called at startup, on mode switch, and when Play Again is clicked.

#### `_log(message, tag)`

Temporarily enables the read-only `tk.Text` console widget, appends a line with the
given colour tag (`"win"` for green, `"loss"` for red), scrolls to the bottom with
`.see("end")`, then disables the widget again to prevent user editing.

---

### Shared Helpers

#### `_reset_stats()`

Resets all three progress bar values to 0, restores their label text to plain
"Progress / Wins / Losses", clears `stats_label`, and calls `_reset_graph()`.
Called by `_on_mode_change()` every time the mode switches.

---

## Threading Model

The simulation loop (`SimMonteHall`) runs on a background **daemon thread** so the
UI remains responsive during long runs. All UI mutations happen exclusively on the
main thread, scheduled via `self.after(0, callback, ...)`. This is the correct and
safe Tkinter threading pattern — Tkinter widgets must never be written to from a
background thread directly.
