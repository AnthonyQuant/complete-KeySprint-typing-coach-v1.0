"""Tkinter Graphical User Interface with feedback, analytics, weakness drills, achievements, and Matplotlib charts."""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from engine import TypingEngine, EngineState
from passages import PassageManager
from analytics import AnalyticsDatabase
from achievements import AchievementManager


class TypingCoachApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("KeySprint - Personal Typing Coach")
        self.root.geometry("980x740")
        self.root.configure(bg="#1e1e2e")

        self.passage_mgr = PassageManager()
        self.db = AnalyticsDatabase()
        self.ach_mgr = AchievementManager()

        self.engine: TypingEngine = None
        self.timer_job = None
        self.session_logged: bool = False

        self.selected_category = tk.StringVar(value="general")
        self.selected_duration = tk.IntVar(value=60)

        self._build_ui()
        self.load_new_test()

    def _build_ui(self):
        # Header / Control Bar
        control_frame = tk.Frame(self.root, bg="#181825", padx=20, pady=15)
        control_frame.pack(fill="x", side="top")

        # Category Selector
        tk.Label(control_frame, text="Category:", fg="#cdd6f4", bg="#181825", font=("Segoe UI", 10, "bold")).pack(side="left", padx=5)
        category_combo = ttk.Combobox(
            control_frame,
            textvariable=self.selected_category,
            values=["general", "punctuation", "developer"],
            state="readonly",
            width=12
        )
        category_combo.pack(side="left", padx=5)
        category_combo.bind("<<ComboboxSelected>>", lambda e: self.load_new_test())

        # Duration Selector
        tk.Label(control_frame, text="Duration:", fg="#cdd6f4", bg="#181825", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(15, 5))
        for sec in [30, 60, 120]:
            rb = tk.Radiobutton(
                control_frame,
                text=f"{sec}s",
                variable=self.selected_duration,
                value=sec,
                command=self.load_new_test,
                bg="#181825",
                fg="#cdd6f4",
                selectcolor="#313244",
                activebackground="#181825",
                activeforeground="#cdd6f4"
            )
            rb.pack(side="left", padx=2)

        # Action Buttons
        restart_btn = tk.Button(
            control_frame,
            text="Restart (Esc)",
            command=self.load_new_test,
            bg="#89b4fa",
            fg="#11111b",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=3
        )
        restart_btn.pack(side="right", padx=5)

        badges_btn = tk.Button(
            control_frame,
            text="Badges",
            command=self.show_achievements_dialog,
            bg="#cba6f7",
            fg="#11111b",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=3
        )
        badges_btn.pack(side="right", padx=5)

        weakness_btn = tk.Button(
            control_frame,
            text="Weakness Drill",
            command=self.start_weakness_drill,
            bg="#f9e2af",
            fg="#11111b",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=3
        )
        weakness_btn.pack(side="right", padx=5)

        stats_btn = tk.Button(
            control_frame,
            text="Analytics",
            command=self.show_analytics_dialog,
            bg="#a6e3a1",
            fg="#11111b",
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            padx=10,
            pady=3
        )
        stats_btn.pack(side="right", padx=5)

        # Metrics Display Dashboard
        metrics_frame = tk.Frame(self.root, bg="#1e1e2e", pady=15)
        metrics_frame.pack(fill="x")

        self.wpm_label = self._create_metric_card(metrics_frame, "WPM", "0.0")
        self.accuracy_label = self._create_metric_card(metrics_frame, "ACCURACY", "100%")
        self.timer_label = self._create_metric_card(metrics_frame, "TIME LEFT", "60s")

        # Passage Rendering Display Box
        text_frame = tk.Frame(self.root, bg="#313244", padx=2, pady=2)
        text_frame.pack(fill="both", expand=True, padx=25, pady=(0, 15))

        self.text_display = tk.Text(
            text_frame,
            font=("Consolas", 15),
            wrap="word",
            bg="#181825",
            fg="#6c7086",
            insertbackground="#89b4fa",
            relief="flat",
            padx=15,
            pady=15
        )
        self.text_display.pack(fill="both", expand=True)

        # Highlight Color Tags
        self.text_display.tag_config("untyped", foreground="#585b70")
        self.text_display.tag_config("correct", foreground="#a6e3a1")
        self.text_display.tag_config("incorrect", foreground="#f38ba8", background="#45475a")
        self.text_display.tag_config("cursor", background="#89b4fa", foreground="#11111b")

        # Weak Keys Quick Bar (Updated variable name)
        self.weak_bar_label = tk.Label(
            self.root,
            text="Weak Keys: None logged yet (complete a test to analyze errors)",
            fg="#a6adc8",
            bg="#181825",
            font=("Segoe UI", 9),
            pady=6
        )
        self.weak_bar_label.pack(fill="x", side="bottom")

        # Event Bindings
        self.root.bind("<Key>", self._on_key_press)
        self.root.bind("<Escape>", lambda e: self.load_new_test())

    def _create_metric_card(self, parent, title: str, default_val: str) -> tk.Label:
        card = tk.Frame(parent, bg="#181825", padx=25, pady=10)
        card.pack(side="left", expand=True, padx=10)

        tk.Label(card, text=title, fg="#a6adc8", bg="#181825", font=("Segoe UI", 9, "bold")).pack()
        val_label = tk.Label(card, text=default_val, fg="#89b4fa", bg="#181825", font=("Segoe UI", 18, "bold"))
        val_label.pack()
        return val_label

    def load_new_test(self, custom_passage: str = None):
        """Resets engine state, timer, and loads a text passage."""
        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

        self.session_logged = False
        category = self.selected_category.get()
        duration = self.selected_duration.get()

        passage = custom_passage if custom_passage else self.passage_mgr.get_passage(category)

        self.engine = TypingEngine(passage, duration_seconds=duration)
        self.wpm_label.config(text="0.0")
        self.accuracy_label.config(text="100%")
        self.timer_label.config(text=f"{duration}s")

        self._render_text()
        self._update_weak_bar()

    def _update_weak_bar(self):
        """Fetches top weak characters by error rate percentage and updates the UI weakness indicator bar."""
        if not hasattr(self, "weak_bar_label"):
            return

        weak_keys = self.db.get_top_weak_keys(limit=5)
        if not weak_keys:
            self.weak_bar_label.config(text="Weakness Analyzer: No weak keys detected yet!")
            return

        formatted = []
        for char, rate in weak_keys:
            display_char = repr(char) if char in (" ", "\n", "\t") else f"'{char}'"
            formatted.append(f"{display_char} ({rate:.1f}%)")

        self.weak_bar_label.config(text=f"Weakness Analyzer (Highest Error Rates): {', '.join(formatted)}")

    def _render_text(self):
        """Renders passage character-by-character with visual feedback status tags."""
        self.text_display.config(state="normal")
        self.text_display.delete("1.0", tk.END)

        statuses = self.engine.get_character_status()
        for idx, (char, status) in enumerate(statuses):
            self.text_display.insert(tk.END, char, status)

        self.text_display.config(state="disabled")

    def _on_key_press(self, event):
        if not self.engine or self.engine.state == EngineState.FINISHED:
            return

        # Handle Backspace
        if event.keysym == "BackSpace":
            self.engine.process_backspace()

        # Handle Enter / Return (Newlines for Developer Mode)
        elif event.keysym in ("Return", "KP_Enter"):
            self.engine.process_key("\n")
            if self.engine.state == EngineState.RUNNING and not self.timer_job:
                self._update_timer_loop()

        # Handle Tab (Inserts 4 spaces for Python indentation)
        elif event.keysym == "Tab":
            for _ in range(4):
                self.engine.process_key(" ")
            if self.engine.state == EngineState.RUNNING and not self.timer_job:
                self._update_timer_loop()
            return "break"

        # Handle standard printable characters
        elif len(event.char) == 1 and ord(event.char) >= 32:
            self.engine.process_key(event.char)

            if self.engine.state == EngineState.RUNNING and not self.timer_job:
                self._update_timer_loop()

        self._render_text()
        self._update_metrics()

        # Immediately invoke completion handler if keypress completed the passage
        if self.engine.state == EngineState.FINISHED:
            self._handle_test_completion()

    def _update_metrics(self):
        if not self.engine:
            return
        self.wpm_label.config(text=f"{self.engine.calculate_wpm():.1f}")
        self.accuracy_label.config(text=f"{self.engine.calculate_accuracy():.1f}%")

    def _update_timer_loop(self):
        if not self.engine:
            return

        elapsed = self.engine.get_elapsed_seconds()
        remaining = max(0, self.engine.duration_seconds - int(elapsed))
        self.timer_label.config(text=f"{remaining}s")

        if self.engine.state == EngineState.FINISHED or remaining <= 0:
            self._handle_test_completion()
            return

        self.timer_job = self.root.after(100, self._update_timer_loop)

    def _handle_test_completion(self):
        """Ends active test, logs session metrics once, and evaluates achievement badges."""
        if self.session_logged:
            return
        self.session_logged = True

        if self.timer_job:
            self.root.after_cancel(self.timer_job)
            self.timer_job = None

        self.engine.finish_test()
        self.timer_label.config(text="0s")
        self._render_text()

        # Record session results in SQLite
        self.db.log_session(self.engine, self.selected_category.get())
        self._update_weak_bar()

        # Evaluate achievement badge conditions
        stats = self.db.get_historical_stats()
        new_unlocks = self.ach_mgr.evaluate_session(
            self.engine,
            category=self.selected_category.get(),
            total_tests_count=stats["total_tests"]
        )

        if new_unlocks:
            names = ", ".join([f"{a['icon']} {a['title']}" for a in new_unlocks])
            messagebox.showinfo("Achievement Unlocked!", f"Congratulations! You unlocked:\n\n{names}")

    def start_weakness_drill(self):
        top_weak = self.db.get_top_weak_keys(limit=5)
        weak_chars = [k for k, _ in top_weak]

        if not weak_chars:
            messagebox.showinfo("Weakness Analyzer", "No typing weaknesses detected yet! Complete a few regular tests first.")
            return

        drill_passage = self.passage_mgr.generate_targeted_exercise(weak_chars, word_count=20)
        self.load_new_test(custom_passage=drill_passage)
        messagebox.showinfo("Weakness Drill Loaded", f"Generated custom practice targeting your weak keys: {', '.join(weak_chars)}")

    def show_analytics_dialog(self):
        """Displays historical stats overview and embedded Matplotlib trend chart."""
        stats = self.db.get_historical_stats()
        history = self.db.get_performance_history(limit=15)

        dialog = tk.Toplevel(self.root)
        dialog.title("Performance Analytics & Trends")
        dialog.geometry("560x550")
        dialog.configure(bg="#1e1e2e")
        dialog.transient(self.root)

        tk.Label(dialog, text="Performance Overview", font=("Segoe UI", 14, "bold"), fg="#89b4fa", bg="#1e1e2e", pady=10).pack()

        # Summary Frame
        summary_frame = tk.Frame(dialog, bg="#181825", padx=15, pady=10)
        summary_frame.pack(fill="x", padx=20, pady=(0, 10))

        labels = [
            ("Tests Completed:", str(stats["total_tests"])),
            ("Avg WPM:", f"{stats['avg_wpm']}"),
            ("Best WPM:", f"{stats['best_wpm']}"),
            ("Avg Accuracy:", f"{stats['avg_accuracy']}%"),
        ]

        for label_text, val_text in labels:
            col = tk.Frame(summary_frame, bg="#181825")
            col.pack(side="left", expand=True)
            tk.Label(col, text=label_text, fg="#a6adc8", bg="#181825", font=("Segoe UI", 8)).pack()
            tk.Label(col, text=val_text, fg="#a6e3a1", bg="#181825", font=("Segoe UI", 11, "bold")).pack()

        # Matplotlib Chart Frame
        chart_frame = tk.Frame(dialog, bg="#181825", padx=5, pady=5)
        chart_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        fig = Figure(figsize=(5, 3), dpi=100, facecolor="#181825")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#181825")

        if history:
            attempts = list(range(1, len(history) + 1))
            wpms = [h[1] for h in history]

            ax.plot(attempts, wpms, marker="o", color="#89b4fa", linewidth=2, label="WPM")
            ax.set_title("WPM Progression (Recent Attempts)", color="#cdd6f4", fontsize=10, pad=8)
            ax.set_xlabel("Attempt", color="#a6adc8", fontsize=8)
            ax.set_ylabel("Words Per Minute", color="#a6adc8", fontsize=8)
            ax.tick_params(colors="#a6adc8", labelsize=8)

            for spine in ax.spines.values():
                spine.set_color("#313244")
            ax.grid(True, color="#313244", linestyle="--", alpha=0.5)
        else:
            ax.text(0.5, 0.5, "No Session Data Logged Yet", color="#a6adc8", ha="center", va="center", fontsize=10)
            ax.set_xticks([])
            ax.set_yticks([])

        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def show_achievements_dialog(self):
        achievements = self.ach_mgr.get_all_achievements()

        dialog = tk.Toplevel(self.root)
        dialog.title("Achievements & Goals")
        dialog.geometry("460x420")
        dialog.configure(bg="#1e1e2e")
        dialog.transient(self.root)

        tk.Label(dialog, text="Achievements & Milestones", font=("Segoe UI", 14, "bold"), fg="#cba6f7", bg="#1e1e2e", pady=15).pack()

        container = tk.Frame(dialog, bg="#181825", padx=15, pady=10)
        container.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        for ach in achievements:
            row = tk.Frame(container, bg="#181825", pady=6)
            row.pack(fill="x")

            status_color = "#a6e3a1" if ach["unlocked"] else "#585b70"
            status_text = "UNLOCKED" if ach["unlocked"] else "LOCKED"

            icon_lbl = tk.Label(row, text=ach["icon"], font=("Segoe UI", 14), bg="#181825")
            icon_lbl.pack(side="left", padx=(0, 10))

            info_frame = tk.Frame(row, bg="#181825")
            info_frame.pack(side="left", fill="x", expand=True)

            tk.Label(info_frame, text=ach["title"], font=("Segoe UI", 10, "bold"), fg="#cdd6f4", bg="#181825").pack(anchor="w")
            tk.Label(info_frame, text=ach["desc"], font=("Segoe UI", 8), fg="#a6adc8", bg="#181825").pack(anchor="w")

            tk.Label(row, text=status_text, font=("Segoe UI", 9, "bold"), fg=status_color, bg="#181825").pack(side="right")