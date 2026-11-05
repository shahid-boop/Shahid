"""Tkinter desktop HUD; keeps the UI independent from provider internals."""
from __future__ import annotations
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from config_manager import Settings
from engine_pipeline import ChatEngine, ProviderError
from memory_manager import MemoryManager
from desktop.live_audio_controller import LiveAudioController

class AssistantUI:
    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings.load()
        self.engine = ChatEngine(self.settings)
        self.memory = MemoryManager()
        self._live_controller: LiveAudioController | None = None
        self.root = tk.Tk()
        self.root.title("Shahid Assistant")
        self.root.geometry("720x560")
        self.root.minsize(520, 420)
        self.root.configure(bg="#0b1020")
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#0b1020")
        style.configure("TLabel", background="#0b1020", foreground="#eaf1ff")
        style.configure("Title.TLabel", font=("Segoe UI", 16, "bold"), foreground="#8edcff")
        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="◉  SHAHID ASSISTANT", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Windows 11 · Local desktop interface").pack(anchor="w", pady=(4, 12))
        self.output = tk.Text(outer, wrap="word", bg="#121b30", fg="#edf2ff",
                              insertbackground="white", relief="flat", padx=12, pady=12,
                              font=("Segoe UI", 10), state="disabled")
        self.output.pack(fill="both", expand=True)
        self.output.tag_configure("user", foreground="#82d8ff", spacing1=8, spacing3=8)
        self.output.tag_configure("assistant", foreground="#d6dfff", spacing1=8, spacing3=8)
        self.input = tk.Text(outer, height=3, wrap="word", bg="#121b30", fg="#edf2ff",
                             insertbackground="white", relief="flat", padx=10, pady=8)
        self.input.pack(fill="x", pady=(12, 8))
        row = ttk.Frame(outer)
        row.pack(fill="x")
        self.status = ttk.Label(row, text="Ready")
        self.status.pack(side="left")
        self.send_button = tk.Button(row, text="Send", command=self.send, bg="#72d0ff",
                                     fg="#07101e", activebackground="#a1e0ff", relief="flat",
                                     padx=20, pady=7)
        self.send_button.pack(side="right")
        self.speak_replies = tk.BooleanVar(value=False)
        ttk.Checkbutton(row, text="Speak replies", variable=self.speak_replies).pack(side="left", padx=(12, 0))
        self.voice_button = tk.Button(row, text="Voice input", command=self.listen_once,
                                      bg="#263a59", fg="#edf2ff", activebackground="#354d70",
                                      relief="flat", padx=12, pady=7)
        self.voice_button.pack(side="right", padx=(8, 0))
        self.tools_button = tk.Button(row, text="Tools", command=self.open_tools,
                                      bg="#263a59", fg="#edf2ff", activebackground="#354d70",
                                      relief="flat", padx=12, pady=7)
        self.tools_button.pack(side="right", padx=(8, 0))
        self.live_stop_button = tk.Button(row, text="Stop Live", command=self.stop_live_voice,
                                          bg="#6b3440", fg="#ffffff", relief="flat",
                                          padx=10, pady=7, state="disabled")
        self.live_stop_button.pack(side="right", padx=(8, 0))
        self.live_start_button = tk.Button(row, text="Gemini Live", command=self.start_live_voice,
                                           bg="#344d79", fg="#ffffff", relief="flat",
                                           padx=10, pady=7)
        self.live_start_button.pack(side="right", padx=(8, 0))
        self.send_button.configure(command=self.send_with_voice)
        self.input.bind("<Control-Return>", self._send_shortcut)
        self.input.bind("<Control-Return>", self._send_shortcut_with_voice)
        self._append("assistant", "Ready. Configure .env to connect an AI provider.")
        self._append("assistant", "Gemini Live is manual-start only and asks before microphone access.")
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _send_shortcut(self, _event):
        self.send()
        return "break"

    def _send_shortcut_with_voice(self, _event):
        self.send_with_voice()
        return "break"

    def open_tools(self) -> None:
        window = getattr(self, "_tools_window", None)
        if window is not None and window.winfo_exists():
            window.lift()
            return
        from main import build_registry
        from desktop.skill_console import SkillConsole
        self._tools_window = tk.Toplevel(self.root)
        self._tools_window.title("Shahid Assistant · Tools")
        self._tools_window.geometry("720x680")
        SkillConsole(self._tools_window, build_registry()).pack(fill="both", expand=True)

    def _live_callback(self, *args) -> None:
        try:
            self.root.after(0, self._live_state, *args)
        except tk.TclError:
            pass

    def _live_state(self, state: str, detail: str = "") -> None:
        if state == "connecting":
            self.status.configure(text="Gemini Live · Connecting / listening")
            self.live_start_button.configure(state="disabled")
            self.live_stop_button.configure(state="normal")
        elif state == "error":
            self.status.configure(text="Gemini Live error")
            self.live_start_button.configure(state="normal")
            self.live_stop_button.configure(state="disabled")
            self._append("assistant", f"Gemini Live unavailable: {detail}")
        else:
            self.status.configure(text="Ready")
            self.live_start_button.configure(state="normal")
            self.live_stop_button.configure(state="disabled")

    def _live_transcript(self, kind: str, value: str) -> None:
        try:
            self.root.after(0, self._append, "assistant", f"{kind}: {value}")
        except tk.TclError:
            pass

    def start_live_voice(self) -> None:
        if self._live_controller is not None and self._live_controller.running:
            self.status.configure(text="Gemini Live is already active")
            return
        if not self.settings.google_api_key:
            messagebox.showerror(
                "Gemini Live setup",
                "GOOGLE_API_KEY is missing. Add it to .env before starting Gemini Live.",
                parent=self.root,
            )
            return
        approved = messagebox.askyesno(
            "Allow Gemini Live microphone and speaker",
            "Start a real-time Gemini Live session now?\n\n"
            "This will open your microphone and speaker and send microphone audio "
            "to Google's Gemini Live service until you press Stop Live. Continue?",
            parent=self.root,
        )
        if not approved:
            self.status.configure(text="Gemini Live cancelled")
            return
        self._live_controller = LiveAudioController(
            self.settings.google_api_key,
            on_state=self._live_callback,
            on_transcript=self._live_transcript,
        )
        try:
            started = self._live_controller.start(approved=True)
            if not started:
                self.status.configure(text="Gemini Live did not start")
        except Exception as exc:
            self._live_state("error", str(exc))

    def stop_live_voice(self) -> None:
        if self._live_controller is None or not self._live_controller.running:
            self._live_state("stopped")
            return
        self._live_controller.stop()
        self.status.configure(text="Gemini Live · Stopping")

    def send_with_voice(self) -> None:
        message = self.input.get("1.0", "end").strip()
        if not message:
            return
        self.input.delete("1.0", "end")
        self._append("user", message)
        self.send_button.configure(state="disabled")
        self.voice_button.configure(state="disabled")
        self.status.configure(text="Thinking…")
        speak = bool(self.speak_replies.get())
        threading.Thread(target=self._answer_with_voice, args=(message, speak), daemon=True).start()

    def _answer_with_voice(self, message: str, speak: bool = False) -> None:
        try:
            self.memory.append("user", message)
            history = [{"role":"system","content":"You are Shahid Assistant, a helpful Windows desktop assistant. Be accurate and state limitations."}]
            history.extend(self.memory.get_messages())
            reply = self.engine.chat(history)
            self.memory.append("assistant", reply)
            status = "Ready"
            if speak:
                try:
                    from speech_engine import SpeechEngine
                    SpeechEngine().speak(reply)
                except Exception as exc:
                    status = "Ready · voice output unavailable"
                    reply += f"\n\n[Voice output unavailable: {exc}]"
            result = (reply, status)
        except ProviderError as exc:
            result = (f"Provider error: {exc}", "Provider error")
        except Exception as exc:
            result = (f"Unexpected error while generating a response: {exc}", "Error")
        self.root.after(0, self._finish_with_voice, *result)

    def listen_once(self) -> None:
        self.voice_button.configure(state="disabled")
        self.send_button.configure(state="disabled")
        self.status.configure(text="Listening…")
        threading.Thread(target=self._listen_once, daemon=True).start()

    def _listen_once(self) -> None:
        try:
            from speech_engine import SpeechEngine
            text = SpeechEngine().listen()
            self.root.after(0, self._voice_ready, text)
        except Exception as exc:
            self.root.after(0, self._voice_failed, str(exc))

    def _voice_ready(self, text: str) -> None:
        self.voice_button.configure(state="normal")
        self.send_button.configure(state="normal")
        if not text.strip():
            self.status.configure(text="No speech detected")
            return
        self.input.delete("1.0", "end")
        self.input.insert("1.0", text)
        self.send_with_voice()

    def _voice_failed(self, error: str) -> None:
        self.voice_button.configure(state="normal")
        self.send_button.configure(state="normal")
        self.status.configure(text="Voice input unavailable")
        self._append("assistant", f"Voice input unavailable: {error}")

    def _finish_with_voice(self, reply: str, status: str) -> None:
        self.voice_button.configure(state="normal")
        self._finish(reply, status)

    def _append(self, role: str, text: str) -> None:
        self.output.configure(state="normal")
        self.output.insert("end", ("You: " if role == "user" else "Shahid: ") + text + "\n", role)
        self.output.see("end")
        self.output.configure(state="disabled")

    def send(self) -> None:
        message = self.input.get("1.0", "end").strip()
        if not message:
            return
        self.input.delete("1.0", "end")
        self._append("user", message)
        self.send_button.configure(state="disabled")
        self.status.configure(text="Thinking…")
        threading.Thread(target=self._answer, args=(message,), daemon=True).start()

    def _answer(self, message: str) -> None:
        try:
            self.memory.append("user", message)
            history = [{"role":"system","content":"You are Shahid Assistant, a helpful Windows desktop assistant. Be accurate and state limitations."}]
            history.extend(self.memory.get_messages())
            reply = self.engine.chat(history)
            self.memory.append("assistant", reply)
            result = (reply, "Ready")
        except ProviderError as exc:
            result = (f"Provider error: {exc}", "Provider error")
        except Exception:
            result = ("Unexpected error while generating a response.", "Error")
        self.root.after(0, self._finish, *result)

    def _finish(self, reply: str, status: str) -> None:
        self._append("assistant", reply)
        self.status.configure(text=status)
        self.send_button.configure(state="normal")
        self.input.focus_set()

    def close(self) -> None:
        if self._live_controller is not None:
            self._live_controller.stop()
        self.root.destroy()

    def run(self) -> None:
        self.root.mainloop()

def run_ui() -> None:
    AssistantUI().run()
