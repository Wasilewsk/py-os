import wx
import threading
import requests
import json
from api import BlindApp

OLLAMA_API = "http://localhost:11434"

class AssistantApp(BlindApp):
    def __init__(self, api):
        super().__init__(api)
        self.name = "AI Assistant"
        self.description = "Voice-enabled assistant powered by Ollama."
        self.category = "Tools"
        self.help_text = "Select a model, type a question and press Enter. The assistant will speak the answer."
        self.docs = "AI Assistant uses a local Ollama server to provide intelligent responses. You can choose from installed models."
        self.model = "llama3"
        self.models = []

    def run(self):
        self.frame = wx.Frame(None, title='AI Assistant', size=(550, 400))
        panel = wx.Panel(self.frame)
        panel.SetBackgroundColour(wx.Colour(20, 20, 50))
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.status_label = wx.StaticText(panel, label="AI Assistant")
        self.status_label.SetForegroundColour(wx.Colour(255, 255, 255))
        self.status_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(self.status_label, 0, wx.ALL | wx.CENTER, 10)

        model_row = wx.BoxSizer(wx.HORIZONTAL)
        model_lbl = wx.StaticText(panel, label="Model:")
        model_lbl.SetForegroundColour(wx.Colour(200, 200, 255))
        model_row.Add(model_lbl, 0, wx.ALL | wx.CENTER, 5)

        self.model_choice = wx.Choice(panel, choices=["llama3"])
        self.model_choice.SetBackgroundColour(wx.Colour(30, 30, 60))
        self.model_choice.SetForegroundColour(wx.Colour(255, 255, 255))
        self.model_choice.SetSelection(0)
        self.model_choice.Bind(wx.EVT_CHOICE, self.on_model_change)
        model_row.Add(self.model_choice, 1, wx.EXPAND | wx.ALL, 5)

        refresh_btn = wx.Button(panel, label="Refresh Models")
        refresh_btn.SetBackgroundColour(wx.Colour(40, 40, 80))
        refresh_btn.SetForegroundColour(wx.Colour(255, 255, 255))
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh_models)
        model_row.Add(refresh_btn, 0, wx.ALL, 5)
        sizer.Add(model_row, 0, wx.EXPAND | wx.ALL, 10)

        self.input_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.input_ctrl.SetBackgroundColour(wx.Colour(30, 30, 60))
        self.input_ctrl.SetForegroundColour(wx.Colour(255, 255, 255))
        sizer.Add(self.input_ctrl, 0, wx.EXPAND | wx.ALL, 10)

        self.history = wx.TextCtrl(panel, style=wx.TE_MULTILINE | wx.TE_READONLY)
        self.history.SetBackgroundColour(wx.Colour(10, 10, 30))
        self.history.SetForegroundColour(wx.Colour(200, 200, 255))
        sizer.Add(self.history, 1, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(sizer)
        self.input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_ask)
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self.frame.Show()
        self.api.speak("AI Assistant is ready. Select a model and type your question.")
        self.input_ctrl.SetFocus()
        threading.Thread(target=self._fetch_models, daemon=True).start()

    def on_model_change(self, event):
        sel = self.model_choice.GetSelection()
        if 0 <= sel < len(self.models):
            self.model = self.models[sel]
            self.api.speak(f"Model set to {self.model}")

    def on_refresh_models(self, event):
        self.api.speak("Refreshing models...")
        threading.Thread(target=self._fetch_models, daemon=True).start()

    def _fetch_models(self):
        try:
            resp = requests.get(f"{OLLAMA_API}/api/tags", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                model_names = [m["name"] for m in data.get("models", [])]
                if model_names:
                    wx.CallAfter(self._update_model_list, model_names)
                    return
        except Exception:
            pass
        wx.CallAfter(self.api.speak, "Could not fetch models. Make sure Ollama is running.")

    def _update_model_list(self, model_names):
        self.models = model_names
        self.model_choice.Clear()
        for name in model_names:
            self.model_choice.Append(name)
        if self.model in model_names:
            self.model_choice.SetSelection(model_names.index(self.model))
        else:
            self.model_choice.SetSelection(0)
            self.model = model_names[0] if model_names else "llama3"
        self.api.speak(f"Loaded {len(model_names)} models")

    def on_ask(self, event):
        prompt = self.input_ctrl.GetValue().strip()
        self.input_ctrl.Clear()
        if not prompt: return
        self.history.AppendText(f"You: {prompt}\n")
        self.status_label.SetLabel("Assistant is thinking...")
        self.api.speak("Thinking...")
        threading.Thread(target=self.call_ollama, args=(prompt,), daemon=True).start()

    def call_ollama(self, prompt):
        try:
            payload = {"model": self.model, "prompt": prompt, "stream": False}
            response = requests.post(f"{OLLAMA_API}/api/generate", json=payload, timeout=30)
            if response.status_code == 200:
                result = response.json().get("response", "I couldn't generate a response.")
                wx.CallAfter(self.show_response, result)
            else:
                wx.CallAfter(self.show_response, f"Error {response.status_code}")
        except Exception:
            wx.CallAfter(self.show_response, "Connection Error. Make sure Ollama is running.")

    def show_response(self, text):
        self.status_label.SetLabel("Assistant is ready")
        self.history.AppendText(f"AI: {text}\n")
        self.api.speak(text)
