import random
import tkinter as tk
from tkinter import ttk
import threading


DOOR = ["Door 1", "Door 2", "Door 3"]
# ----------------------------------------------------------------------
# Single interactive play
# ----------------------------------------------------------------------
def PlayMonteHall(door, switch):
    winning_door = random.randint(0, 2)
    all_indices = {0, 1, 2}

    remaining = list(all_indices - {door, winning_door})
    shown_index = random.choice(remaining)

    switch_candidates = list(all_indices - {shown_index})
    final_door = next(i for i in switch_candidates if i != door)
    if not switch:
        final_door = door

    won = final_door == winning_door
    return won, shown_index, winning_door


# ----------------------------------------------------------------------
# Batch simulation
# ----------------------------------------------------------------------
def SimMonteHall(N, switch):
    return [PlayMonteHall(random.randint(0, 2), switch)[0] for _ in range(N)]


# ======================================================================
# GUI
# ======================================================================
class SimApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Monty Hall Simulator")
        self.resizable(False, False)
        self._play_door     = None
        self._revealed_door = None
        self._winning_door  = None
        self._graph_points  = []
        self._graph_n       = 1     # total trials for current run — set in _on_run
        self._build_ui()


    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------
    def _build_ui(self):

        # ── Title ──────────────────────────────────────────────────────
        tk.Label(self, text="🐐 GOATED - A Monty Hall Simulator 🐐", font=("Courier", 20, "bold")).pack(
            pady=(16, 4)
        )

        # ── Body: left_frame | separator | right_frame ─────────────────
        body = tk.Frame(self)
        body.pack(fill="x", padx=0, pady=0)
        body.columnconfigure(0, minsize=340)

        left_frame = tk.Frame(body)
        left_frame.grid(row=0, column=0, sticky="nw", padx=(12, 0), pady=4)

        ttk.Separator(body, orient="vertical").grid(
            row=0, column=1, sticky="ns", padx=10, pady=4
        )

        right_frame = tk.Frame(body)
        right_frame.grid(row=0, column=2, sticky="nw", padx=(0, 16), pady=4)

        # ══════════════════════════════════════════════════════════════
        # LEFT FRAME
        # ══════════════════════════════════════════════════════════════

        tk.Label(left_frame, text="Mode:", font=("Helvetica", 11, "bold")).pack(
            anchor="w", pady=(4, 2)
        )
        self.mode_var = tk.StringVar(value="simulate")
        mode_frame = tk.Frame(left_frame)
        mode_frame.pack(anchor="w")
        tk.Radiobutton(
            mode_frame, text="Simulate", variable=self.mode_var, value="simulate",
            font=("Helvetica", 10), command=self._on_mode_change
        ).pack(side="left", padx=(0, 6))
        tk.Radiobutton(
            mode_frame, text="Play", variable=self.mode_var, value="play",
            font=("Helvetica", 10), command=self._on_mode_change
        ).pack(side="left")

        ttk.Separator(left_frame, orient="horizontal").pack(fill="x", pady=8)

        # ── [SIMULATE] widgets ─────────────────────────────────────────
        self.sim_frame = tk.Frame(left_frame)
        self.sim_frame.pack(anchor="w")

        tk.Label(self.sim_frame, text="Switch if given the chance?",
                 font=("Helvetica", 11, "bold")).grid(row=0, column=0, sticky="w", pady=6)
        self.switch_var = tk.StringVar(value="-- Select --")
        self.switch_dropdown = ttk.Combobox(
            self.sim_frame, textvariable=self.switch_var,
            values=["Yes", "No"], state="readonly", width=12, font=("Helvetica", 10)
        )
        self.switch_dropdown.grid(row=0, column=1, sticky="w", padx=(10, 0), pady=6)

        tk.Label(self.sim_frame, text="Number of simulations:",
                 font=("Helvetica", 11, "bold")).grid(row=1, column=0, sticky="w", pady=6)
        self.n_var = tk.StringVar(value="1000")
        self.n_entry = tk.Entry(self.sim_frame, textvariable=self.n_var, width=10,
                                font=("Helvetica", 10))
        self.n_entry.grid(row=1, column=1, sticky="w", padx=(10, 0), pady=6)

        self.run_btn = tk.Button(
            self.sim_frame, text="Run Simulation", font=("Helvetica", 11, "bold"),
            command=self._on_run, bg="#4CAF50", fg="white", padx=10
        )
        self.run_btn.grid(row=2, column=0, columnspan=2, pady=(10, 4))

        # ── [PLAY] widgets ─────────────────────────────────────────────
        self.play_frame = tk.Frame(left_frame)

        tk.Label(self.play_frame, text="Pick your door:",
                 font=("Helvetica", 11, "bold")).pack(anchor="w", pady=(4, 6))

        door_btn_frame = tk.Frame(self.play_frame)
        door_btn_frame.pack(anchor="w")
        self.play_door_btns = []
        for i, label in enumerate(DOOR):
            btn = tk.Button(
                door_btn_frame, text=f"🚪\n{label}",
                font=("Helvetica", 11), width=8, height=3,
                command=lambda idx=i: self._on_door_click(idx)
            )
            btn.pack(side="left", padx=(0, 8))
            self.play_door_btns.append(btn)

        self.instruction_var = tk.StringVar(value="")
        tk.Label(
            self.play_frame, textvariable=self.instruction_var,
            font=("Helvetica", 10, "italic"), fg="#1565c0",
            wraplength=320, justify="left"
        ).pack(anchor="w", pady=(6, 2))

        self.play_again_btn = tk.Button(
            self.play_frame, text="🔄  Play Again", font=("Helvetica", 10, "bold"),
            command=self._reset_play_stage, bg="#1565c0", fg="white", padx=10
        )

        # ── Error label ────────────────────────────────────────────────
        self.error_var = tk.StringVar()
        tk.Label(left_frame, textvariable=self.error_var,
                 fg="red", font=("Helvetica", 9)).pack(anchor="w")

        # ══════════════════════════════════════════════════════════════
        # RIGHT FRAME
        # ══════════════════════════════════════════════════════════════

        tk.Label(right_frame, text="RESULTS",
                 font=("Helvetica", 12, "bold")).pack(anchor="w", pady=(4, 6))

        self.progress_label = tk.Label(right_frame, text="Progress",
                                       font=("Helvetica", 10))
        self.progress_label.pack(anchor="w")
        self.progress_bar = ttk.Progressbar(right_frame, length=260, mode="determinate")
        self.progress_bar.pack(anchor="w", pady=(2, 6))

        self.win_label = tk.Label(right_frame, text="Wins",
                                  font=("Helvetica", 10), fg="#2e7d32")
        self.win_label.pack(anchor="w")
        self.win_bar = ttk.Progressbar(right_frame, length=260, mode="determinate")
        self.win_bar.pack(anchor="w", pady=(2, 6))

        self.loss_label = tk.Label(right_frame, text="Losses",
                                   font=("Helvetica", 10), fg="#c62828")
        self.loss_label.pack(anchor="w")
        self.loss_bar = ttk.Progressbar(right_frame, length=260, mode="determinate")
        self.loss_bar.pack(anchor="w", pady=(2, 6))

        self.stats_label = tk.Label(right_frame, text="",
                                    font=("Courier", 10), justify="left")
        self.stats_label.pack(anchor="w", pady=(6, 4))

        # ══════════════════════════════════════════════════════════════
        # GRAPH — full-width bottom section, Simulate mode only
        # ══════════════════════════════════════════════════════════════

        self.graph_outer = tk.Frame(self)

        ttk.Separator(self.graph_outer, orient="horizontal").pack(
            fill="x", padx=12, pady=(0, 4)
        )
        tk.Label(self.graph_outer, text="Cumulative Win Rate",
                 font=("Helvetica", 9, "bold"), fg="#555555").pack(anchor="w", padx=12)

        graph_inner = tk.Frame(self.graph_outer)
        graph_inner.pack(fill="both", expand=True, padx=12, pady=(2, 12))

        self.PAD_L = 36
        self.PAD_B = 20
        self.PAD_T = 10
        self.PAD_R = 12

        self.graph_canvas = tk.Canvas(
            graph_inner, height=160,
            bg="#1e1e1e", highlightthickness=1, highlightbackground="#444"
        )
        self.graph_canvas.pack(fill="x", expand=True)
        self.graph_canvas.bind("<Configure>", self._on_canvas_resize)

        # ══════════════════════════════════════════════════════════════
        # CONSOLE — full-width bottom row, Play mode only
        # ══════════════════════════════════════════════════════════════

        self.console_outer = tk.Frame(self)

        ttk.Separator(self.console_outer, orient="horizontal").pack(
            fill="x", padx=12, pady=(0, 6)
        )
        tk.Label(self.console_outer, text="Console",
                 font=("Helvetica", 9, "bold"), fg="#555555").pack(anchor="w", padx=12)

        console_inner = tk.Frame(self.console_outer)
        console_inner.pack(fill="both", expand=True, padx=12, pady=(2, 12))

        self.console = tk.Text(
            console_inner, height=6,
            font=("Courier", 9), state="disabled",
            bg="#1e1e1e", fg="#d4d4d4",
            relief="flat", padx=6, pady=4, wrap="word"
        )
        self.console.pack(side="left", fill="both", expand=True)

        console_scroll = ttk.Scrollbar(console_inner, orient="vertical",
                                       command=self.console.yview)
        console_scroll.pack(side="right", fill="y")
        self.console.config(yscrollcommand=console_scroll.set)
        self.console.tag_config("win",  foreground="#69ff47")
        self.console.tag_config("loss", foreground="#ff6b6b")

        self._on_mode_change()


    # ------------------------------------------------------------------
    # Graph Helpers
    # ------------------------------------------------------------------
    def _on_canvas_resize(self, event=None):
        self.graph_canvas.delete("all")
        self._draw_graph_axes()
        self._redraw_graph()


    def _draw_graph_axes(self):
        c  = self.graph_canvas
        w  = c.winfo_width()  or 400
        h  = c.winfo_height() or 160
        pl, pb, pt, pr = self.PAD_L, self.PAD_B, self.PAD_T, self.PAD_R

        x0, y0 = pl,     pt
        x1, y1 = w - pr, h - pb

        # Horizontal gridlines + y-axis labels
        for pct in [0.0, 0.33, 0.50, 0.67, 1.0]:
            y = y1 - pct * (y1 - y0)
            c.create_line(x0, y, x1, y, fill="#333333", dash=(2, 4), tags="axes")
            c.create_text(x0 - 4, y, text=f"{int(pct*100)}%", anchor="e",
                          fill="#888888", font=("Courier", 7), tags="axes")

        # X-axis tick labels: 0, n/4, n/2, 3n/4, n
        n = self._graph_n
        for frac, label in [(0, "0"), (0.25, f"{n//4}"), (0.5, f"{n//2}"),
                            (0.75, f"{3*n//4}"), (1.0, f"{n}")]:
            x = x0 + frac * (x1 - x0)
            c.create_line(x, y1, x, y1 + 3, fill="#666666", tags="axes")
            c.create_text(x, h - 5, text=label, anchor="n",
                          fill="#888888", font=("Courier", 7), tags="axes")

        # Axes
        c.create_line(x0, y0, x0, y1, fill="#666666", width=1, tags="axes")
        c.create_line(x0, y1, x1, y1, fill="#666666", width=1, tags="axes")


    def _redraw_graph(self):
        c = self.graph_canvas
        c.delete("plot")

        pts = self._graph_points
        if len(pts) < 2:
            return

        w  = c.winfo_width()  or 400
        h  = c.winfo_height() or 160
        pl, pb, pt, pr = self.PAD_L, self.PAD_B, self.PAD_T, self.PAD_R

        x0, y0 = pl,     pt
        x1, y1 = w - pr, h - pb

        # Scale x to the user's chosen N, not just the last data point
        n = self._graph_n

        def to_canvas(trial, rate):
            cx = x0 + (trial / n) * (x1 - x0)
            cy = y1 - rate * (y1 - y0)
            return cx, cy

        coords = []
        for trial, rate in pts:
            coords.extend(to_canvas(trial, rate))

        c.create_line(*coords, fill="#69ff47", width=1.5,
                      smooth=True, tag="plot")

        lx, ly = to_canvas(*pts[-1])
        r = 3
        c.create_oval(lx - r, ly - r, lx + r, ly + r,
                      fill="#69ff47", outline="", tag="plot")


    def _reset_graph(self):
        self._graph_points = []
        self.graph_canvas.delete("plot")


    # ------------------------------------------------------------------
    # Mode Toggle
    # ------------------------------------------------------------------
    def _on_mode_change(self):
        self._reset_stats()
        if self.mode_var.get() == "simulate":
            self.play_frame.pack_forget()
            self.console_outer.pack_forget()
            self.sim_frame.pack(anchor="w")
            self.graph_outer.pack(fill="x", side="bottom", padx=0, pady=0)
        else:
            self.sim_frame.pack_forget()
            self.graph_outer.pack_forget()
            self.play_frame.pack(anchor="w")
            self.console_outer.pack(fill="x", side="bottom")
            self._reset_play_stage()


    # ------------------------------------------------------------------
    # Stats Reset Helper
    # ------------------------------------------------------------------
    def _reset_stats(self):
        self.progress_bar["value"] = 0
        self.win_bar["value"]      = 0
        self.loss_bar["value"]     = 0
        self.progress_label.config(text="Progress")
        self.win_label.config(text="Wins")
        self.loss_label.config(text="Losses")
        self.stats_label.config(text="")
        self._reset_graph()


    # ------------------------------------------------------------------
    # Console Helper
    # ------------------------------------------------------------------
    def _log(self, message, tag):
        self.console.config(state="normal")
        self.console.insert("end", message + "\n", tag)
        self.console.see("end")
        self.console.config(state="disabled")


    # ------------------------------------------------------------------
    # Play Mode — Stage Management
    # ------------------------------------------------------------------
    def _reset_play_stage(self):
        self._play_door     = None
        self._revealed_door = None
        self._winning_door  = None
        self.instruction_var.set("👆 Pick a door to begin!")
        self.error_var.set("")
        self.play_again_btn.pack_forget()
        for i, btn in enumerate(self.play_door_btns):
            btn.config(
                text=f"🚪\n{DOOR[i]}",
                state="normal",
                relief="raised",
                bg="SystemButtonFace"
            )


    def _on_door_click(self, idx):
        if self._play_door is None:
            # ── Stage 1 ────────────────────────────────────────────────
            self._play_door = idx
            self.play_door_btns[idx].config(relief="sunken", bg="#bbdefb")

            _, shown_index, winning_door = PlayMonteHall(idx, switch=True)
            self._revealed_door = shown_index
            self._winning_door  = winning_door

            self.play_door_btns[self._revealed_door].config(
                text=f"🐐\n{DOOR[self._revealed_door]}\n(Goat!)",
                state="disabled",
                bg="#eeeeee"
            )
            self.instruction_var.set(
                f"🐐 {DOOR[self._revealed_door]} has a goat!  Now pick your final door."
            )

        else:
            # ── Stage 2 ────────────────────────────────────────────────
            if idx == self._revealed_door:
                return
            switched = (idx != self._play_door)
            won = (idx == self._winning_door)

            for i, btn in enumerate(self.play_door_btns):
                if i == self._winning_door:
                    btn.config(text=f"🚗\n{DOOR[i]}\n(Car!)", bg="#c8e6c9", state="disabled")
                elif i == self._revealed_door:
                    pass
                else:
                    btn.config(text=f"🐐\n{DOOR[i]}\n(Goat!)", bg="#eeeeee", state="disabled")

            result = "🎉 You WON!" if won else "😢 You lost."
            switch_text = "switched" if switched else "stayed"
            self.instruction_var.set(f"{result}  You {switch_text}.")

            GOAT_ART = """
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣤⣀⠀⠀⠀⢰⡶⣦⠀⠀⠀⣰⣾⣿⡄⠀⠀⣠⣴⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠀⠀⠀⢀⣿⠉⢻⣷⡄⢀⣿⠷⠻⣿⠁⠸⠋⠉⢹⡇⠀⡾⠛⢻⡿⠀⣤⡾⣻⠇⠀⠀⢠⡶⠀⠀⡀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣤⣤⣤⣤⡀⠀⠀⠀⣿⡿⣦⣄⡀⣴⡿⠟⠋⠙⠿⠙⠉⠀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠁⠛⠉⢻⡟⠀⠠⣴⣿⡀⣠⡞⠁⢀⣴⠆⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⠋⠁⠀⣠⡟⠁⠀⠀⠀⣽⣿⠟⠻⡶⠈⠗⠀⠀⠀⠀⠀⣀⣠⣴⣪⣡⣾⣷⡿⣷⣾⣿⣿⣟⣃⠀⠀⠀⠈⠀⠀⣾⠏⣨⣿⠋⢀⣴⠟⠁⣀⣴⠞
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠻⣷⣴⠿⠛⠛⠛⠛⣷⡄⠸⣷⠀⠀⠀⠀⠀⠀⠀⠀⠘⢧⣿⣿⠛⣟⣿⣏⣤⠾⠿⠾⠷⣶⣌⠁⠀⠀⠀⠀⠀⠀⠀⢴⠟⠁⠀⠛⠁⣠⡾⠋⠁⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⡄⠀⠀⠀⠀⣼⡟⠀⠁⠀⠀⠀⠀⢀⣤⡴⠶⠛⠛⠋⠉⠉⠀⠀⠀⠀⠑⠄⢀⠀⠀⠉⢳⣄⡀⠀⠀⠀⠀⠀⠀⠀⠐⠟⣀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣀⣀⣠⣼⠟⠀⠀⠀⠀⠀⠀⢀⣿⠃⢀⡀⣀⣤⠤⠤⢤⣀⠀⠀⠀⣀⡿⢧⠤⣄⠛⠛⠛⠛⠻⣄⠀⠀⠀⠀⠀⠀⠘⠛⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⠾⠿⠛⠛⠋⠁⠀⠀⠀⠀⠀⠀⢰⣿⣃⣴⠛⠋⠁⠀⠀⠀⠀⠈⠘⢦⡈⠁⠀⠀⠐⠒⠀⠠⣴⠓⠛⠛⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢶⣿⡇⠁⠁⡤⢐⣴⣦⣤⡀⠀⠀⠀⠈⠻⣄⠀⠀⠀⠀⠁⠀⠈⢻⡟⢻⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣤
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⡴⠞⢻⡇⠀⠀⣴⣡⣤⣤⣮⢻⡄⠀⠀⠀⠀⠀⢹⡄⠀⠀⠀⠀⠀⠀⠙⢾⡷⡦⣤⣄⣀⣀⣀⣀⣀⣀⡤⠞⠉⣻
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣠⣤⠤⠶⠚⠛⠉⠀⠀⠀⢸⡇⠀⠠⣿⠛⠛⠛⢉⣸⠇⠀⠀⠀⠀⠀⠀⠸⠄⠀⠀⠀⠀⠀⠀⠈⠛⢮⠊⠀⠉⠉⠉⠉⠉⠁⠀⠀⣰⡇
⣀⣀⣀⣀⣀⣀⣤⣤⡤⠴⠶⠚⠛⠋⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢷⠀⠀⠈⢻⣒⣒⣫⠏⡀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡶⠛⠛⠛⠛⢿⠛⠉⣷⡀⠀⠀⠀⠀⠀⠀⠀⣸⠋⠀
⣭⣿⠍⠉⠉⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡀⠄⠐⠫⠀⢸⡇⠀⠻⠽⠁⠈⠁⠀⠀⠀⠀⢀⡶⠦⠀⠸⣤⠞⣻⠆⠀⠈⡀⣴⠟⢳⣀⣀⠀⠀⢀⣠⠜⠃⠀⠀
⡼⠻⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⢾⡥⠤⣤⣀⠀⠀⠘⣧⡀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣞⠁⠀⠀⠀⠀⠈⠙⢦⣀⣀⣡⠏⠀⢨⠇⠉⠉⠉⠉⠁⠀⠀⠀⠀
⠀⠀⠈⠛⢦⣀⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣠⠴⠋⠁⠀⠀⠀⣿⠈⠀⠀⠀⠀⠉⠛⣦⣀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⠀⠀⠀⠀⠉⢽⠁⠀⣠⠞⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠈⠉⠛⠛⠛⠛⠛⠛⠛⠋⠉⠉⠁⠀⠀⠀⠀⠀⢸⣿⠀⠀⠀⢰⡀⠀⠀⠏⠫⠀⠀⠀⠀⢀⠀⣴⣋⣽⣿⣉⣹⡟⠒⠶⠤⢤⠶⣺⠟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⢾⡿⠀⠀⠀⠀⣷⠀⠀⠀⠀⠀⠀⠀⠀⡞⣸⣿⣿⣿⣿⣿⣿⣿⣷⣶⣶⠛⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢴⣿⠇⠀⠀⠀⠀⠹⣷⡀⠀⠀⠀⠀⢠⣎⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣻⡟⠀⠀⠀⠀⠀⠀⠹⣿⡀⠀⠀⠀⠀⠙⡆⢿⡿⢿⣻⢍⠉⠉⠙⠲⣄⠉⠻⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⢾⡟⠀⠀⠀⠀⠀⠀⠀⠀⠹⣿⣄⠀⠀⠀⠀⠀⢸⣧⡟⢹⣦⡠⠀⠀⠀⠈⢣⠀⠙⢦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣽⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣄⠀⠀⠀⠀⠀⢣⣳⣞⢀⡟⢧⡄⠀⠀⠀⠛⡂⠀⠻⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢿⣦⡀⠀⠀⠀⠀⠙⢿⣿⡧⣯⣙⡾⣗⡤⠤⣀⣀⣀⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣦⠀⠀⠀⠀⠀⠈⠛⢳⣮⣥⣥⣭⣿⣿⣿⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣷⣦⡀⢀⣀⢀⢀⣴⢾⣷⡶⠞⠛⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣻⢆⠞⠰⣽⢿⣍⢢⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⡿⢿⣿⣿⠙⣿⡾⡆⠃⠈⢧⡟⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢧⡄⠀⠀⠀⠀⠀⠀⠀⣠⠞⠁⠀⢸⡿⠃⠀⡏⢇⡟⡄⢠⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠳⢤⣀⠀⠀⠰⠊⠀⠀⠀⢠⡿⠃⠀⠘⠀⡿⣸⡃⠻⢷⣶⣒⠲⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠑⠢⣄⠀⠀⠀⢠⡟⠁⠀⠀⠀⠀⠷⣿⣷⣶⣖⡒⣿⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠐⣰⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠋⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""
            CAR_ART = """
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⠴⠖⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠛⠻⠿⢿⣿⠽⠽⠿⢷⣒⠦⢄⣀⣀⣀⣀⣀⣀⡀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⠞⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠏⡟⠀⠀⠀⠀⠈⢹⡛⢮⡻⣏⠙⢿⡿⠿⠇⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡴⠋⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠏⣸⠀⠀⠀⠀⠀⠀⠈⢧⣀⡙⡎⠳⣿⣀⣀⣀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣀⣀⣤⣴⠾⠯⠤⠤⠤⠤⠤⠤⢤⣤⣤⠤⠀⠀⠀⠀⠀⠀⣀⣀⣀⣀⣀⣞⣀⣏⣧⣄⣀⡈⠹⠖⠒⠛⠳⣍⣀⣀⡤⠤⠝⠛⢷⡀⠀
⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⠤⠶⠛⠋⠉⠘⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⠉⠁⠀⠀⣀⡠⢤⠤⠖⠚⠛⢉⣉⠀⠀⠈⡇⠙⠋⠀⣀⣀⠤⠴⠒⠋⠉⡇⠀⠀⠀⣀⢀⡈⢧⠀
⠀⠀⠀⠀⣠⣶⣾⡿⠋⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⡤⠴⠒⠉⣉⠤⣶⣾⣠⠴⠚⠉⠉⠈⠳⣄⣠⡷⠖⠉⠉⠁⠀⠀⠀⠀⠀⢀⠇⠀⠀⣤⡿⢿⣿⣾⣿
⠀⠀⣴⢿⡽⠋⠙⠒⠒⠒⠒⠒⠲⠤⠤⠤⠤⠀⠀⠤⠤⠤⠔⠒⠋⠉⣠⡤⠖⠋⣣⣤⡾⠛⠉⣀⣴⣶⣯⣖⣦⡀⠹⡀⢰⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⠀⠀⢰⣿⣿⡿⣿⣿⠸
⢠⡾⣩⡿⣡⣴⣶⣖⣒⣂⣤⣤⣤⣄⣄⣀⡠⢤⣀⠀⠀⠀⠀⣤⠖⡫⠑⠓⣦⣴⠟⣁⣀⣀⣴⣿⢿⣛⡉⠻⣷⣵⡀⢹⣸⠀⠀⠀⠀⠀⠀⠀⠀⢀⡇⠀⠀⢸⣿⣿⣧⣿⡽⠀
⢸⣷⣿⣼⡟⠙⠻⠿⠿⡁⠀⢠⠾⠿⠿⠿⠿⠟⢛⡆⠀⠀⡼⠷⠶⠖⠛⠛⣿⠟⠉⠁⠀⣸⣿⣧⣾⣞⣯⠱⣾⣿⣇⠀⢿⠀⠀⠀⠀⠀⠀⠀⠀⣼⣀⡀⠀⣿⣿⣿⣯⣿⡇⢰
⣸⣦⣿⣿⠉⠉⠓⠒⠒⠚⠛⠓⠲⠶⠦⠤⠤⠤⢼⣷⠀⠀⡇⠀⠀⠀⠀⢸⡟⠀⠀⠀⢀⣿⡇⣦⢹⣷⢿⣀⢚⣻⡇⠀⠸⡄⠀⣀⣠⠤⠴⣞⣫⣯⠤⠖⠒⡿⣿⣻⣿⡏⠀⠘
⣸⣻⣿⣿⣿⣽⠳⣶⣶⣦⣦⣤⣤⣤⣤⣤⠤⠄⣸⣿⠀⠀⢹⣤⣄⣤⣤⣾⡇⠀⠀⠀⢸⡟⣷⣿⣿⣿⠚⠛⢭⣿⡇⠀⢀⣏⠭⠽⠚⣛⣉⡥⠶⠒⠚⠛⠉⠁⠸⠿⠿⠀⠀⠀
⢻⠠⢽⣿⡻⠿⣼⡿⣿⡿⣿⣿⣿⣿⣿⣿⡿⡀⣸⣿⠀⠀⠸⠿⡿⠿⠿⠋⡇⠀⠀⣠⣾⡇⡿⣋⣀⣏⢻⡦⢼⣾⠓⠋⣁⣴⠴⠛⠛⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠸⠿⣿⣿⣾⣮⣯⣭⣿⣛⣻⣻⣿⠿⠿⠥⠼⢿⠛⣿⣧⣶⣶⣿⣥⣭⣉⡹⠽⠟⠋⠁⣸⡇⢧⢿⡏⢸⡆⢁⣼⠛⠚⠉⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠉⠉⠙⠛⠓⠛⠿⠿⠿⠿⢿⣿⣾⣿⣿⣟⣿⣷⣖⣀⣀⣐⣀⣐⣒⣊⣉⣉⣁⣳⠘⢦⡣⠬⣵⣾⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠁⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠉⠛⠓⠒⠛⠒⠛⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
"""
            if won:
                self._log(f"🚗 Congrats, you won the car! {CAR_ART}", "win")
            else:
                self._log(f"🐐 Congrats, you won a goat! \n {GOAT_ART}", "loss")

            self.play_again_btn.pack(anchor="w", pady=(6, 2))

            self.after(0, self._update_ui, 1, 1,
                       1 if won else 0, 0 if won else 1,
                       self._play_door, switched)


    # ------------------------------------------------------------------
    # Input Validation (Simulate mode only)
    # ------------------------------------------------------------------
    def _validate(self):
        if self.switch_var.get() == "-- Select --":
            self.error_var.set("Please select a switch preference (Yes or No).")
            return False
        if not self.n_var.get().isdigit() or int(self.n_var.get()) < 1:
            self.error_var.set("Please enter a positive number.")
            return False
        self.error_var.set("")
        return True


    # ------------------------------------------------------------------
    # Run Handler (Simulate mode only)
    # ------------------------------------------------------------------
    def _on_run(self):
        if not self._validate():
            return

        will_switch = self.switch_var.get() == "Yes"
        n = int(self.n_var.get())

        # Store N so the graph x-axis always spans exactly 0..N
        self._graph_n = n

        self.progress_bar["maximum"] = n
        self.win_bar["maximum"] = n
        self.loss_bar["maximum"] = n
        self.progress_bar["value"] = 0
        self.win_bar["value"] = 0
        self.loss_bar["value"] = 0
        self.stats_label.config(text="")
        self._reset_graph()

        # Redraw axes immediately with the new N tick labels
        self.graph_canvas.delete("all")
        self._draw_graph_axes()

        self.run_btn.config(state="disabled")

        thread = threading.Thread(
            target=self._simulate, args=(will_switch, n), daemon=True
        )
        thread.start()


    # ------------------------------------------------------------------
    # Simulation loop (background thread)
    # ------------------------------------------------------------------
    def _simulate(self, will_switch, n):
        wins  = 0
        batch = max(1, n // 200)

        for i in range(1, n + 1):
            won, _, _ = PlayMonteHall(random.randint(0, 2), will_switch)
            wins += won

            if i % batch == 0 or i == n:
                losses = i - wins
                self.after(0, self._update_ui, i, n, wins, losses, None, will_switch)


    # ------------------------------------------------------------------
    # UI Update (called on main thread via after())
    # ------------------------------------------------------------------
    def _update_ui(self, runs_done, n, wins, losses, option_y, will_switch):
        win_rate  = wins   / runs_done * 100
        loss_rate = losses / runs_done * 100
        option_label = "Random" if option_y is None else DOOR[option_y]

        self.progress_bar["maximum"] = n
        self.win_bar["maximum"]      = n
        self.loss_bar["maximum"]     = n

        self.progress_bar["value"] = runs_done
        self.win_bar["value"]      = wins
        self.loss_bar["value"]     = losses

        self.progress_label.config(text=f"Progress  : {runs_done}/{n} ({runs_done/n*100:.1f}%)")
        self.win_label.config(      text=f"Wins      : {wins}  ({win_rate:.1f}%)")
        self.loss_label.config(     text=f"Losses    : {losses}  ({loss_rate:.1f}%)")

        self._graph_points.append((runs_done, wins / runs_done))
        self._redraw_graph()

        if runs_done == n:
            self.stats_label.config(
                text=(
                    f"  Option   : {option_label}\n"
                    f"  Switch   : {'Yes' if will_switch else 'No'}\n"
                    f"  Win rate : {win_rate:.1f}%\n"
                    f"  Loss rate: {loss_rate:.1f}%\n"
                    f"  ✓ Simulation complete!"
                )
            )
            self.run_btn.config(state="normal")


if __name__ == "__main__":
    app = SimApp()
    app.mainloop()
