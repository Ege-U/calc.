#!/usr/bin/env python3
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import random
import math
import json
import os
import multiprocessing as mp
import matplotlib.pyplot as plt
import numpy as np

# Audio libraries (Pure Python Standard Library)
import wave
import io
import sys
import subprocess
import tempfile
import threading

# ==========================================
# 1. PURE PYTHON MULTI-SOUND AUDIO SYNTHESIZER
# ==========================================

# Active sound preset ("Mute" is default)
current_sound_preset = "Mute"

def play_wav_bytes(wav_bytes):
    """Plays PCM WAV bytes in a non-blocking background process across OS platforms."""
    if sys.platform.startswith("win"):
        try:
            import winsound
            winsound.PlaySound(wav_bytes, winsound.SND_MEMORY | winsound.SND_ASYNC)
        except Exception:
            pass
    elif sys.platform == "darwin":  # macOS
        def _play_mac():
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(wav_bytes)
                    fname = f.name
                subprocess.run(["afplay", fname], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                os.remove(fname)
            except Exception:
                pass
        threading.Thread(target=_play_mac, daemon=True).start()
    else:  # Linux
        def _play_linux():
            try:
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                    f.write(wav_bytes)
                    fname = f.name
                subprocess.run(["aplay", "-q", fname], stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                os.remove(fname)
            except Exception:
                pass
        threading.Thread(target=_play_linux, daemon=True).start()

def generate_preset_sound(sound_type="number", preset="Mute"):
    """Synthesizes custom waveforms dynamically based on the selected sound preset."""
    if preset == "Mute":
        return None

    sample_rate = 22050
    
    # Set durations per profile
    if preset == "Mechanical Click":
        duration = 0.05 if sound_type == "equals" else 0.035
    elif preset == "Laser":
        duration = 0.22 if sound_type == "equals" else 0.06
    elif preset == "Arcade":
        duration = 0.15 if sound_type == "equals" else 0.05
    else:
        duration = 0.18 if sound_type == "equals" else 0.08

    num_samples = int(sample_rate * duration)
    
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(1)  # 8-bit audio
        wav_file.setframerate(sample_rate)
        
        data = bytearray()
        for i in range(num_samples):
            t = i / sample_rate
            
            if preset == "Mechanical Click":
                # Real Mechanical Switch Profile (Crisp Tactile Clack)
                if sound_type == "operator": start_f, end_f = 950, 420
                elif sound_type == "equals": start_f, end_f = 1200, 500
                elif sound_type == "clear": start_f, end_f = 750, 300
                else: start_f, end_f = 1100, 450  # Numbers

                # Layer 1: Soft High-Frequency Plastic Snap
                snap_noise = random.randint(-40, 40) * math.exp(-400 * t)
                
                # Layer 2: Light Keycap Body Click
                current_freq = start_f * math.exp(-120 * t) + end_f
                click_phase = (t * current_freq) % 1.0
                click_wave = math.sin(2 * math.pi * click_phase) * 60 * math.exp(-140 * t)
                
                # Layer 3: Subtle Switch Leaf Ping / Resonance
                ring_phase = (t * 4200) % 1.0
                ring_wave = math.sin(2 * math.pi * ring_phase) * 12 * math.exp(-180 * t)
                
                # Composite Signal Output
                val = int(128 + snap_noise + click_wave + ring_wave)

            elif preset == "Arcade":
                if sound_type == "operator": freq = 1200 + (800 * (t / duration))
                elif sound_type == "equals": freq = 900 if t < 0.05 else (1200 if t < 0.10 else 1600)
                elif sound_type == "clear": freq = 1000 - (700 * (t / duration))
                else: freq = 880 + (200 * (t / duration))
                
                phase = (t * freq) % 1.0
                val = 190 if phase < 0.4 else 65
                decay = max(0.0, 1.0 - (t / duration))
                val = int(128 + (val - 128) * decay)

            elif preset == "Laser":
                if sound_type == "operator": freq = 2000 * math.exp(-30 * t)
                elif sound_type == "equals": freq = 300 + 1500 * math.sin(2 * math.pi * 15 * t)
                elif sound_type == "clear": freq = 1500 * math.exp(-15 * t)
                else: freq = 1200 * math.exp(-40 * t)
                
                phase = (t * freq) % 1.0
                val = 200 if phase < 0.5 else 55
                decay = max(0.0, 1.0 - (t / duration))
                val = int(128 + (val - 128) * decay)

            elif preset == "Smooth Chords":
                if sound_type == "operator": freq = 523.25  # C5
                elif sound_type == "equals": freq = 659.25   # E5
                elif sound_type == "clear": freq = 392.00    # G4
                else: freq = 440.00                          # A4
                
                phase = (t * freq) % 1.0
                tri = 4 * abs(phase - 0.5) - 1.0
                decay = max(0.0, 1.0 - (t / duration))
                val = 128 + int(50 * tri * decay)

            else:  # "8-Bit Retro"
                if sound_type == "operator": freq = 600 + (600 * (t / duration))
                elif sound_type == "equals":
                    if t < 0.06: freq = 400
                    elif t < 0.12: freq = 600
                    else: freq = 800
                elif sound_type == "clear": freq = 400 - (300 * (t / duration))
                else: freq = 440 - (200 * (t / duration))
                
                phase = (t * freq) % 1.0
                val = 190 if phase < 0.5 else 65
                decay = max(0.0, 1.0 - (t / duration))
                val = int(128 + (val - 128) * decay)

            data.append(max(0, min(255, val)))
            
        wav_file.writeframes(data)
    
    return buf.getvalue()

def play_sound(sound_type="number"):
    """Plays audio asynchronously according to the currently selected sound profile."""
    if current_sound_preset == "Mute":
        return
    try:
        wav_bytes = generate_preset_sound(sound_type, current_sound_preset)
        if wav_bytes:
            play_wav_bytes(wav_bytes)
    except Exception:
        pass


# ==========================================
# 2. CONFIGURATION & THEMES
# ==========================================

THEMES_FILE = "custom_themes.json"

DEFAULT_THEMES = {
    "Light": {
        "bg": "#f5f5f7", "display": "#ffffff", "btn": "#ffffff",
        "btn_op": "#e5e5ea", "btn_eq": "#ff9500", "fg": "#1c1c1e",
        "label_fg": "#3a3a3c"
    },
    "Dark": {
        "bg": "#1c1c1e", "display": "#2c2c2e", "btn": "#3a3a3c",
        "btn_op": "#48484a", "btn_eq": "#ff9500", "fg": "#ffffff",
        "label_fg": "#ffffff"
    },
    "Ocean": {
        "bg": "#0b2431", "display": "#123847", "btn": "#1c4f61",
        "btn_op": "#0e3947", "btn_eq": "#00b4d8", "fg": "#ffffff",
        "label_fg": "#ffffff"
    },
    "Midnight Violet": {
        "bg": "#120f18", "display": "#1e1829", "btn": "#262035",
        "btn_op": "#3b3052", "btn_eq": "#8b5cf6", "fg": "#f3e8ff",
        "label_fg": "#d8b4fe"
    },
    "Cyberpunk": {
        "bg": "#0a0a12", "display": "#121124", "btn": "#1a1836",
        "btn_op": "#2d2759", "btn_eq": "#00f0ff", "fg": "#00f0ff",
        "label_fg": "#ff007f"
    },
    "Matcha Latte": {
        "bg": "#f4f6f0", "display": "#ffffff", "btn": "#e8ede0",
        "btn_op": "#d6e0c7", "btn_eq": "#84a98c", "fg": "#2f3e46",
        "label_fg": "#52796f"
    },
    "Peach Sunset": {
        "bg": "#fff5f0", "display": "#ffffff", "btn": "#ffe8df",
        "btn_op": "#ffd1c2", "btn_eq": "#ff7043", "fg": "#4a2820",
        "label_fg": "#d85a38"
    },
    "Rose Gold": {
        "bg": "#fbeef2", "display": "#ffffff", "btn": "#f7dce3",
        "btn_op": "#eec4d0", "btn_eq": "#b76e79", "fg": "#5c2a33",
        "label_fg": "#b76e79"
    },
    "Nordic Frost": {
        "bg": "#eceff4", "display": "#ffffff", "btn": "#e5e9f0",
        "btn_op": "#d8dee9", "btn_eq": "#5e81ac", "fg": "#2e3440",
        "label_fg": "#4c566a"
    },
    "Vaporwave": {
        "bg": "#1a1030", "display": "#28184a", "btn": "#3a2361",
        "btn_op": "#4e2f7a", "btn_eq": "#ff6ec7", "fg": "#7ee8fa",
        "label_fg": "#ff6ec7"
    },
    "Forest": {
        "bg": "#1b2e1f", "display": "#243b29", "btn": "#2f4d35",
        "btn_op": "#3d6144", "btn_eq": "#a3c586", "fg": "#e8f0e3",
        "label_fg": "#a3c586"
    },
    "Monochrome": {
        "bg": "#e8e8e8", "display": "#ffffff", "btn": "#d4d4d4",
        "btn_op": "#b8b8b8", "btn_eq": "#1c1c1c", "fg": "#1c1c1c",
        "label_fg": "#4a4a4a"
    },
    "Solar Flare": {
        "bg": "#1f1300", "display": "#2e1d00", "btn": "#3d2900",
        "btn_op": "#5c3d00", "btn_eq": "#ffb703", "fg": "#ffe8b0",
        "label_fg": "#ffb703"
    },
    "Coffee": {
        "bg": "#efe6dd", "display": "#ffffff", "btn": "#dcc9b6",
        "btn_op": "#c4a988", "btn_eq": "#6f4e37", "fg": "#3e2723",
        "label_fg": "#6f4e37"
    },
    "Bubblegum": {
        "bg": "#ffe6f2", "display": "#ffffff", "btn": "#ffc2e0",
        "btn_op": "#ff9ecf", "btn_eq": "#ff2d95", "fg": "#5c1039",
        "label_fg": "#ff2d95"
    },
    "Midnight Sea": {
        "bg": "#02111b", "display": "#0a2239", "btn": "#12344d",
        "btn_op": "#1c4966", "btn_eq": "#3ddc97", "fg": "#e0fbfc",
        "label_fg": "#3ddc97"
    },
    "Lavender Fields": {
        "bg": "#f3f0fa", "display": "#ffffff", "btn": "#e5deF5",
        "btn_op": "#d4c7ec", "btn_eq": "#9b7ede", "fg": "#3b2a5c",
        "label_fg": "#9b7ede"
    },
    "Autumn Blaze": {
        "bg": "#2b1810", "display": "#3d2317", "btn": "#5a3421",
        "btn_op": "#7a4a2a", "btn_eq": "#e8751a", "fg": "#ffe8d1",
        "label_fg": "#e8751a"
    },
    "Mint Chip": {
        "bg": "#e8f9f1", "display": "#ffffff", "btn": "#c5f0dc",
        "btn_op": "#9ee6c4", "btn_eq": "#0d9c6e", "fg": "#0a3d2c",
        "label_fg": "#0d9c6e"
    },
    "Blood Moon": {
        "bg": "#160303", "display": "#2b0606", "btn": "#3f0a0a",
        "btn_op": "#5c0f0f", "btn_eq": "#e50914", "fg": "#ffd6d6",
        "label_fg": "#e50914"
    },
    "Sandstone": {
        "bg": "#f2e8d5", "display": "#ffffff", "btn": "#e3d3ae",
        "btn_op": "#d0ba85", "btn_eq": "#a97c50", "fg": "#4a3421",
        "label_fg": "#a97c50"
    },
    "Neon Jungle": {
        "bg": "#0a1f0a", "display": "#122b12", "btn": "#1c421c",
        "btn_op": "#286028", "btn_eq": "#39ff14", "fg": "#d4ffcc",
        "label_fg": "#39ff14"
    },
    "Steel": {
        "bg": "#2b2f33", "display": "#363b3f", "btn": "#454b50",
        "btn_op": "#565d63", "btn_eq": "#7fb3d5", "fg": "#f0f2f4",
        "label_fg": "#7fb3d5"
    },
    "Royal Gold": {
        "bg": "#1a1408", "display": "#2b220f", "btn": "#3d3115",
        "btn_op": "#544521", "btn_eq": "#d4af37", "fg": "#fff4d6",
        "label_fg": "#d4af37"
    },
    "Lemon Cream": {
        "bg": "#fffbe6", "display": "#ffffff", "btn": "#fff3b0",
        "btn_op": "#ffe873", "btn_eq": "#f5c400", "fg": "#4a3c00",
        "label_fg": "#c99a00"
    },
    "Cotton Candy Sky": {
        "bg": "#eaf6ff", "display": "#ffffff", "btn": "#d6ecff",
        "btn_op": "#c2e0ff", "btn_eq": "#5eb1ff", "fg": "#1c3a5c",
        "label_fg": "#5eb1ff"
    },
}

THEMES = dict(DEFAULT_THEMES)

def load_custom_themes():
    global THEMES
    if os.path.exists(THEMES_FILE):
        try:
            with open(THEMES_FILE, "r") as f:
                custom = json.load(f)
                THEMES.update(custom)
        except Exception:
            pass

def save_custom_theme(name, colors):
    custom_dict = {}
    if os.path.exists(THEMES_FILE):
        try:
            with open(THEMES_FILE, "r") as f:
                custom_dict = json.load(f)
        except Exception:
            pass
    custom_dict[name] = colors
    THEMES[name] = colors
    try:
        with open(THEMES_FILE, "w") as f:
            json.dump(custom_dict, f, indent=2)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save theme: {e}")

current_theme = "Light"
expression = ""
memory = 0.0
history = []

ROASTS = [
    "Calculator app peaked in 1997",
    "Calculator app has zero themes",
    "Calculator app has zero roasts. We win.",
    "Calculator app: 1 + 1 = boring",
    "Calculator app never left beta energy",
    "Calculator app dreams of 26 themes",
    "Calculator app: math homework tier",
    "Calculator app got cooked. Again.",
    "Calculator app can't even roast back",
]


# ==========================================
# 3. CORE CALCULATOR ENGINE & TIMEOUT WORKER
# ==========================================

def sanitize(expr):
    return (expr.replace("^", "**")
            .replace("√", "math.sqrt")
            .replace("sin", "math.sin")
            .replace("cos", "math.cos")
            .replace("tan", "math.tan")
            .replace("log", "math.log10")
            .replace("π", "math.pi")
            .replace("e", "math.e")
            .replace("AND", "&")
            .replace("XOR", "^")
            .replace("OR", "|")
            .replace("LSH", "<<")
            .replace("RSH", ">>"))

def _mp_eval_worker(expr, queue):
    try:
        queue.put(("ok", eval(expr)))
    except Exception as e:
        queue.put(("err", str(e)))

def eval_with_timeout(expr, timeout=1.5):
    queue = mp.Queue()
    proc = mp.Process(target=_mp_eval_worker, args=(expr, queue), daemon=True)
    proc.start()
    proc.join(timeout)
    if proc.is_alive():
        proc.terminate()
        proc.join()
        raise TimeoutError("Calculation too large")
    if not queue.empty():
        status, value = queue.get()
        if status == "err":
            raise RuntimeError(value)
        return value
    raise RuntimeError("Calculation failed")

def press(key):
    global expression, memory

    # --- Trigger Sound Effect ---
    if key in ["+", "-", "*", "/", "%", "^", "sin", "cos", "tan", "log", "√"]:
        play_sound("operator")
    elif key == "=":
        play_sound("equals")
    elif key in ["C", "del", "MC"]:
        play_sound("clear")
    else:
        play_sound("number")

    # --- Calculator Operation Logic ---
    if key == "C":
        expression = ""
    elif key == "del":
        expression = expression[:-1]
    elif key == "MC":
        memory = 0.0
    elif key == "MR":
        expression += str(memory)
    elif key == "M+":
        try:
            memory += float(eval_with_timeout(sanitize(expression)))
        except Exception:
            pass
    elif key == "M-":
        try:
            memory -= float(eval_with_timeout(sanitize(expression)))
        except Exception:
            pass
    elif key == "=":
        try:
            safe_expr = sanitize(expression)
            open_count = safe_expr.count("(")
            close_count = safe_expr.count(")")
            if open_count > close_count:
                safe_expr += ")" * (open_count - close_count)
            result = eval_with_timeout(safe_expr)
            if isinstance(result, float):
                result = round(result, 6)
            history.append(f"{expression} = {result}")
            update_history()
            expression = str(result)
            update_prog_display()
        except ZeroDivisionError:
            expression = "Error: div by 0"
        except TimeoutError:
            expression = "Error: too large"
        except Exception:
            expression = "Error"
    elif key in ["sin", "cos", "tan", "log", "√"]:
        expression += key + "("
    elif key in ["AND", "OR", "XOR", "LSH", "RSH"]:
        expression += f" {key} "
    elif key == "NOT":
        try:
            val = int(eval_with_timeout(sanitize(expression)))
            expression = str(~val)
            update_prog_display()
        except Exception:
            expression = "Error"
    elif key == "π":
        expression += "π"
    elif key == "e":
        expression += "e"
    elif key == "x²":
        expression += "**2"
    elif key == "%":
        try:
            val = float(eval_with_timeout(sanitize(expression)))
            result = val / 100
            if result == int(result):
                result = int(result)
            expression = str(result)
        except Exception:
            expression = "Error"
    elif key == "^":
        expression += "^"
    else:
        expression += key
    display_var.set(expression if expression else "0")
    update_prog_display()

def truncate_text(text, max_len=24):
    if len(text) > max_len:
        return text[:max_len-3] + "..."
    return text

def update_prog_display():
    try:
        val = int(float(eval_with_timeout(sanitize(expression))))
        hex_var.set(truncate_text(f"HEX: {hex(val)[2:].upper()}"))
        dec_var.set(truncate_text(f"DEC: {val}"))
        oct_var.set(truncate_text(f"OCT: {oct(val)[2:]}"))
        bin_var.set(truncate_text(f"BIN: {bin(val)[2:]}"))
    except Exception:
        hex_var.set("HEX: -")
        dec_var.set("DEC: -")
        oct_var.set("OCT: -")
        bin_var.set("BIN: -")

def update_history():
    history_box.delete(0, tk.END)
    for item in history[-8:][::-1]:
        history_box.insert(tk.END, item)

def roast():
    play_sound("equals")
    display_var.set(random.choice(ROASTS))

def copy_to_clipboard():
    play_sound("equals")
    try:
        root.clipboard_clear()
        root.clipboard_append(display_var.get())
        root.update()
        copy_status_var.set("Copied!")
        root.after(1200, lambda: copy_status_var.set(""))
    except Exception:
        copy_status_var.set("Copy failed")
        root.after(1200, lambda: copy_status_var.set(""))

def open_graph():
    play_sound("operator")
    try:
        expr = display_var.get().replace("^", "**")
        x = np.linspace(-10, 10, 400)
        y = eval(expr, {"x": x, "np": np, "sin": np.sin, "cos": np.cos, "tan": np.tan, "sqrt": np.sqrt, "log10": np.log10, "pi": np.pi, "e": np.e, "abs": np.abs})
        plt.figure(figsize=(6, 4))
        plt.plot(x, y, color="#ff9500" if current_theme != "Cyberpunk" else "#00f0ff", lw=2)
        plt.title(f"Graph of: {display_var.get()}")
        plt.xlabel("x")
        plt.ylabel("y")
        plt.grid(True, linestyle="--", alpha=0.6)
        plt.axhline(0, color='black', linewidth=1)
        plt.axvline(0, color='black', linewidth=1)
        plt.show()
    except Exception:
        display_var.set("Error: Invalid Equation")

def apply_theme(name):
    global current_theme
    current_theme = name
    t = THEMES[name]
    root.configure(bg=t["bg"])
    display.configure(bg=t["display"], fg=t["fg"], insertbackground=t["fg"])
    history_box.configure(bg=t["display"], fg=t["fg"])
    
    for (btn, text) in button_refs:
        if text == "=":
            btn.set_colors(t["btn_eq"], "white")
        elif text in ["C", "del", "%", "MC", "MR", "M+", "M-"]:
            btn.set_colors(t["btn_op"], t["fg"])
        else:
            btn.set_colors(t["btn"], t["fg"])
            
    roast_btn.set_colors("#e24b4a", "white")
    side.configure(bg=t["bg"])
    for lbl in side_labels:
        lbl.configure(bg=t["bg"], fg=t["label_fg"])
    for btn in side_buttons:
        btn.set_colors(t["btn_op"], t["fg"])
    conv_display.configure(bg=t["display"], fg=t["fg"], insertbackground=t["fg"])


# ==========================================
# 4. CUSTOM THEME STUDIO WINDOW
# ==========================================

def open_theme_creator():
    play_sound("operator")
    creator = tk.Toplevel(root)
    creator.title("Custom Theme Studio")
    creator.geometry("380x520")
    creator.resizable(False, False)
    creator.configure(bg="#2c2c2e")

    colors = dict(THEMES[current_theme])

    tk.Label(creator, text="Theme Studio", font=("Arial", 14, "bold"), fg="#ffffff", bg="#2c2c2e").pack(pady=10)

    name_frame = tk.Frame(creator, bg="#2c2c2e")
    name_frame.pack(fill="x", padx=20, pady=5)
    tk.Label(name_frame, text="Theme Name:", fg="#ffffff", bg="#2c2c2e", font=("Arial", 10, "bold")).pack(side="left")
    name_entry = tk.Entry(name_frame, font=("Arial", 10))
    name_entry.insert(0, "My Custom Theme")
    name_entry.pack(side="right", expand=True, fill="x", padx=(10, 0))

    elements = [
        ("Background (bg)", "bg"),
        ("Display Box (display)", "display"),
        ("Number Buttons (btn)", "btn"),
        ("Operator Keys (btn_op)", "btn_op"),
        ("Equals Key (btn_eq)", "btn_eq"),
        ("Text Color (fg)", "fg"),
        ("Sidebar Text (label_fg)", "label_fg"),
    ]

    swatches = {}

    def pick_color(key):
        play_sound("number")
        color = colorchooser.askcolor(initialcolor=colors[key], title=f"Select Color for {key}")
        if color[1]:
            colors[key] = color[1]
            swatches[key].configure(bg=color[1])
            update_preview()

    fields_frame = tk.Frame(creator, bg="#2c2c2e")
    fields_frame.pack(fill="both", expand=True, padx=20, pady=10)

    for label, key in elements:
        row = tk.Frame(fields_frame, bg="#2c2c2e")
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, fg="#ffffff", bg="#2c2c2e", font=("Arial", 9)).pack(side="left")
        
        btn_pick = tk.Button(row, text="Pick", font=("Arial", 8), command=lambda k=key: pick_color(k))
        btn_pick.pack(side="right", padx=(5, 0))

        swatch = tk.Label(row, bg=colors[key], width=4, relief="ridge")
        swatch.pack(side="right")
        swatches[key] = swatch

    preview_card = tk.Frame(creator, bg=colors["bg"], bd=2, relief="groove")
    preview_card.pack(fill="x", padx=20, pady=10)
    
    prev_disp = tk.Label(preview_card, text="123 + 456", bg=colors["display"], fg=colors["fg"], font=("Arial", 10), anchor="e")
    prev_disp.pack(fill="x", padx=10, pady=5)

    prev_btn_frame = tk.Frame(preview_card, bg=colors["bg"])
    prev_btn_frame.pack(pady=5)
    prev_b1 = tk.Label(prev_btn_frame, text=" 7 ", bg=colors["btn"], fg=colors["fg"], font=("Arial", 9, "bold"))
    prev_b1.pack(side="left", padx=2)
    prev_b2 = tk.Label(prev_btn_frame, text=" + ", bg=colors["btn_op"], fg=colors["fg"], font=("Arial", 9, "bold"))
    prev_b2.pack(side="left", padx=2)
    prev_b3 = tk.Label(prev_btn_frame, text=" = ", bg=colors["btn_eq"], fg="#ffffff", font=("Arial", 9, "bold"))
    prev_b3.pack(side="left", padx=2)

    def update_preview():
        preview_card.configure(bg=colors["bg"])
        prev_disp.configure(bg=colors["display"], fg=colors["fg"])
        prev_btn_frame.configure(bg=colors["bg"])
        prev_b1.configure(bg=colors["btn"], fg=colors["fg"])
        prev_b2.configure(bg=colors["btn_op"], fg=colors["fg"])
        prev_b3.configure(bg=colors["btn_eq"])

    def save_and_apply():
        t_name = name_entry.get().strip()
        if not t_name:
            messagebox.showerror("Error", "Please enter a valid theme name.")
            return
        play_sound("equals")
        save_custom_theme(t_name, colors)
        theme_menu["values"] = list(THEMES.keys())
        theme_var.set(t_name)
        apply_theme(t_name)
        creator.destroy()

    tk.Button(creator, text="💾 Save & Apply Theme", font=("Arial", 11, "bold"), bg="#ff9500", fg="#ffffff",
              activebackground="#e08200", command=save_and_apply).pack(fill="x", padx=20, pady=(0, 15))


# ==========================================
# 5. UNIT CONVERTER & KEYBOARD LISTENERS
# ==========================================

def convert_press(key):
    if key in ["C", "del"]:
        play_sound("clear")
    else:
        play_sound("number")

    current_val = conv_display_var.get()
    if key == "C":
        conv_display_var.set("0")
    elif key == "del":
        if len(current_val) > 1:
            conv_display_var.set(current_val[:-1])
        else:
            conv_display_var.set("0")
    elif key == ".":
        if "." not in current_val:
            conv_display_var.set(current_val + ".")
    else:
        if current_val == "0":
            conv_display_var.set(key)
        else:
            conv_display_var.set(current_val + key)
    execute_conversion()

def execute_conversion():
    try:
        val = float(conv_display_var.get())
        choice = convert_var.get()
        if choice == "km -> miles":
            res = val * 0.621371
        elif choice == "miles -> km":
            res = val / 0.621371
        elif choice == "kg -> lb":
            res = val * 2.20462
        elif choice == "lb -> kg":
            res = val / 2.20462
        elif choice == "C -> F":
            res = (val * 9/5) + 32
        elif choice == "F -> C":
            res = (val - 32) * 5/9
        convert_result.set(f"Result: {round(res, 4)}")
    except ValueError:
        convert_result.set("Invalid number")

def key_event(event):
    char = event.char
    if char in "0123456789+-*/.%()":
        press(char)
    elif event.keysym == "Return":
        press("=")
    elif event.keysym == "BackSpace":
        press("del")
    elif event.keysym == "Escape":
        press("C")


# ==========================================
# 6. MAIN APPLICATION UI SETUP
# ==========================================

if __name__ == "__main__":
    load_custom_themes()
    root = tk.Tk()
    root.title("calc. - v1.12.0")
    root.geometry("740x750")
    root.minsize(740, 750)
    root.resizable(False, False)

    display_var = tk.StringVar(value="0")
    display = tk.Entry(root, textvariable=display_var, font=("Arial", 20),
                        justify="right", bd=0, highlightthickness=0)
    display.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=(10, 4), pady=10, ipady=12)

    copy_status_var = tk.StringVar(value="")

    buttons = [
        ("MC", 1, 0), ("MR", 1, 1), ("M+", 1, 2), ("M-", 1, 3),
        ("C", 2, 0), ("del", 2, 1), ("%", 2, 2), ("/", 2, 3),
        ("7", 3, 0), ("8", 3, 1), ("9", 3, 2), ("*", 3, 3),
        ("4", 4, 0), ("5", 4, 1), ("6", 4, 2), ("-", 4, 3),
        ("1", 5, 0), ("2", 5, 1), ("3", 5, 2), ("+", 5, 3),
        ("0", 6, 0), (".", 6, 1), ("√", 6, 2), ("=", 6, 3),
        ("sin", 7, 0), ("cos", 7, 1), ("tan", 7, 2), ("log", 7, 3),
        ("^", 8, 0), ("π", 8, 1), ("e", 8, 2), ("x²", 8, 3),
        ("AND", 9, 0), ("OR", 9, 1), ("XOR", 9, 2), ("NOT", 9, 3),
        ("LSH", 10, 0), ("RSH", 10, 1)
    ]

    def make_button(parent, text, command):
        canvas = tk.Canvas(parent, width=70, height=40, highlightthickness=0, bd=0, cursor="hand2")
        state = {
            "fill": "#ffffff",
            "fg": "#000000",
            "text": text,
            "hover": False,
            "pressed": False,
            "job": None
        }

        def _draw_now():
            canvas.delete("all")
            w = canvas.winfo_width()
            h = canvas.winfo_height()
            if w < 10 or h < 10:
                w, h = 70, 40
        
            bg_color = root.cget("bg")
            canvas.configure(bg=bg_color)
        
            pad = 4 if state["pressed"] else (2 if state["hover"] else 3)
            r = 8
            x0, y0, x1, y1 = pad, pad, w - pad, h - pad
            
            active_eq_color = THEMES[current_theme]["btn_eq"]
            if state["hover"] and not state["pressed"]:
                fill_color = active_eq_color
                fg_color = "#ffffff"
            else:
                fill_color = state["fill"]
                fg_color = state["fg"]
        
            canvas.create_rectangle(x0 + r, y0, x1 - r, y1, fill=fill_color, outline=fill_color)
            canvas.create_rectangle(x0, y0 + r, x1, y1 - r, fill=fill_color, outline=fill_color)
            canvas.create_arc(x0, y0, x0 + 2*r, y0 + 2*r, start=90, extent=90, fill=fill_color, outline=fill_color)
            canvas.create_arc(x1 - 2*r, y0, x1, y0 + 2*r, start=0, extent=90, fill=fill_color, outline=fill_color)
            canvas.create_arc(x0, y1 - 2*r, x0 + 2*r, y1, start=180, extent=90, fill=fill_color, outline=fill_color)
            canvas.create_arc(x1 - 2*r, y1 - 2*r, x1, y1, start=270, extent=90, fill=fill_color, outline=fill_color)
        
            fsize = max(int((h - pad * 2) * (0.32 if state["pressed"] else 0.35)), 10)
            canvas.create_text(w / 2, h / 2, text=state["text"],
                               font=("Arial", fsize, "bold" if state["text"] in ["Roast Calculator App", "=", "Plot Graph", "🎨 Create Theme"] else "normal"), fill=fg_color)

        def redraw(event=None):
            if state["job"] is not None:
                canvas.after_cancel(state["job"])
            state["job"] = canvas.after(5, _draw_now)

        def on_enter(e):
            state["hover"] = True
            redraw()

        def on_leave(e):
            state["hover"] = False
            state["pressed"] = False
            redraw()

        def on_press(e):
            state["pressed"] = True
            redraw()

        def on_release(e):
            if state["pressed"]:
                state["pressed"] = False
                redraw()
                command()

        canvas.bind("<Configure>", redraw)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        canvas.bind("<Button-1>", on_press)
        canvas.bind("<ButtonRelease-1>", on_release)

        def set_colors(fill, fg):
            state["fill"] = fill
            state["fg"] = fg
            redraw()
        canvas.set_colors = set_colors
        return canvas

    copy_btn = make_button(root, "📋", copy_to_clipboard)
    copy_btn.grid(row=0, column=3, sticky="nsew", padx=(0, 10), pady=10)

    button_refs = []
    for (text, row, col) in buttons:
        btn = make_button(root, text, lambda t=text: press(t))
        if text == "LSH":
            btn.grid(row=row, column=col, columnspan=2, sticky="nsew", padx=4, pady=2)
        elif text == "RSH":
            btn.grid(row=row, column=2, columnspan=2, sticky="nsew", padx=4, pady=2)
        else:
            btn.grid(row=row, column=col, sticky="nsew", padx=4, pady=2)
        button_refs.append((btn, text))

    roast_btn = make_button(root, "Roast Calculator App", roast)
    roast_btn.grid(row=11, column=0, columnspan=4, sticky="nsew", padx=4, pady=(4, 10))

    for i in range(12):
        root.grid_rowconfigure(i, weight=1)
    for i in range(4):
        root.grid_columnconfigure(i, weight=1, uniform="calc_col")

    root.bind("<Key>", key_event)

    side = tk.Frame(root, width=220)
    side.grid(row=0, column=4, rowspan=12, sticky="nsew", padx=12, pady=10)
    side.grid_propagate(False)

    side_labels = []
    side_buttons = []

    copy_status_lbl = tk.Label(side, textvariable=copy_status_var, font=("Arial", 9, "italic"), fg="#34c759")
    copy_status_lbl.pack(anchor="e")

    lbl = tk.Label(side, text="Programmer Base", font=("Arial", 11, "bold")); lbl.pack(anchor="w")
    side_labels.append(lbl)
    
    hex_var = tk.StringVar(value="HEX: -")
    dec_var = tk.StringVar(value="DEC: -")
    oct_var = tk.StringVar(value="OCT: -")
    bin_var = tk.StringVar(value="BIN: -")
    
    for v in [hex_var, dec_var, oct_var, bin_var]:
        p_lbl = tk.Label(side, textvariable=v, font=("Courier", 10, "bold"), anchor="w", width=24)
        p_lbl.pack(fill="x")
        side_labels.append(p_lbl)

    # --- THEME SELECTOR ---
    lbl = tk.Label(side, text="Theme", font=("Arial", 11, "bold")); lbl.pack(anchor="w", pady=(4, 0))
    side_labels.append(lbl)
    theme_var = tk.StringVar(value=current_theme)
    theme_menu = ttk.Combobox(side, textvariable=theme_var, values=list(THEMES.keys()),
                               state="readonly", width=22)
    theme_menu.pack(anchor="w", pady=(0, 4))
    theme_menu.bind("<<ComboboxSelected>>", lambda e: apply_theme(theme_var.get()))

    create_theme_btn = make_button(side, "🎨 Create Theme", open_theme_creator)
    create_theme_btn.pack(fill="x", pady=(0, 4))
    side_buttons.append(create_theme_btn)

    # --- SOUND PROFILE SELECTOR ---
    lbl = tk.Label(side, text="Sound Profile", font=("Arial", 11, "bold")); lbl.pack(anchor="w", pady=(4, 0))
    side_labels.append(lbl)
    
    sound_var = tk.StringVar(value=current_sound_preset)
    
    def on_sound_change(event):
        global current_sound_preset
        current_sound_preset = sound_var.get()
        play_sound("equals")  # Preview sound profile upon selection
        
    sound_menu = ttk.Combobox(side, textvariable=sound_var, 
                              values=["Mute", "Mechanical Click", "8-Bit Retro", "Arcade", "Laser", "Smooth Chords"],
                              state="readonly", width=22)
    sound_menu.pack(anchor="w", pady=(0, 6))
    sound_menu.bind("<<ComboboxSelected>>", on_sound_change)

    # --- HISTORY ---
    lbl = tk.Label(side, text="History", font=("Arial", 11, "bold")); lbl.pack(anchor="w")
    side_labels.append(lbl)
    history_box = tk.Listbox(side, width=28, height=3, bd=0, highlightthickness=0, font=("Arial", 9))
    history_box.pack(pady=(0, 4))

    # --- UNIT CONVERTER ---
    lbl = tk.Label(side, text="Unit converter", font=("Arial", 11, "bold")); lbl.pack(anchor="w")
    side_labels.append(lbl)
    convert_var = tk.StringVar(value="km -> miles")
    convert_menu = ttk.Combobox(side, textvariable=convert_var,
                                 values=["km -> miles", "miles -> km", "kg -> lb",
                                         "lb -> kg", "C -> F", "F -> C"],
                                 state="readonly", width=22)
    convert_menu.pack(anchor="w", pady=(0, 2))
    convert_menu.bind("<<ComboboxSelected>>", lambda e: execute_conversion())

    conv_display_var = tk.StringVar(value="0")
    conv_display = tk.Entry(side, textvariable=conv_display_var, font=("Arial", 12),
                             justify="right", bd=0, highlightthickness=0)
    conv_display.pack(fill="x", pady=2, ipady=4)

    conv_buttons = [
        ("7", 0, 0), ("8", 0, 1), ("9", 0, 2),
        ("4", 1, 0), ("5", 1, 1), ("6", 1, 2),
        ("1", 2, 0), ("2", 2, 1), ("3", 2, 2),
        ("0", 3, 0), (".", 3, 1), ("C", 3, 2),
        ("del", 4, 0)
    ]

    conv_keypad_frame = tk.Frame(side)
    conv_keypad_frame.pack(fill="x", pady=2)
    for i in range(5):
        conv_keypad_frame.grid_rowconfigure(i, weight=1)
    for i in range(3):
        conv_keypad_frame.grid_columnconfigure(i, weight=1)

    for (text, r, c) in conv_buttons:
        cbtn = make_button(conv_keypad_frame, text, lambda t=text: convert_press(t))
        if text == "del":
            cbtn.grid(row=r, column=c, columnspan=3, sticky="nsew", padx=1, pady=1)
        else:
            cbtn.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
        side_buttons.append(cbtn)

    convert_result = tk.StringVar(value="Result: -")
    lbl = tk.Label(side, textvariable=convert_result, font=("Arial", 10, "bold")); lbl.pack(pady=(2, 4), anchor="w")
    side_labels.append(lbl)

    graph_btn = make_button(side, "Plot Graph", open_graph)
    graph_btn.pack(fill="x", pady=(0, 2))
    side_buttons.append(graph_btn)

    apply_theme(current_theme)
    root.mainloop()
