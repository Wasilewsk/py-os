import wx
import os
import json
import sys
import subprocess
import threading
import time

OOBE_MUSIC = "1996 Internet Starter Kit - Velkommen - Original Mix.wav"

class UpdateWizard(wx.Frame):
    def __init__(self, api, state_path, on_finish):
        super().__init__(None, title="PyOS Update", size=(650, 450),
                         style=wx.DEFAULT_FRAME_STYLE | wx.STAY_ON_TOP)
        self.api = api
        self.state_path = state_path
        self.on_finish = on_finish
        self._cancelled = False

        with open(state_path, "r") as f:
            self.state = json.load(f)
        self.phase = self.state.get("phase", 1)

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(0, 0, 139))
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.AddStretchSpacer()

        self.header = wx.StaticText(self.panel, label="")
        self.header.SetForegroundColour(wx.Colour(255, 255, 255))
        self.header.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.sizer.Add(self.header, 0, wx.ALL | wx.CENTER, 15)

        self.msg = wx.StaticText(self.panel, label="")
        self.msg.SetForegroundColour(wx.Colour(200, 200, 200))
        self.msg.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        self.sizer.Add(self.msg, 0, wx.ALL | wx.CENTER, 10)

        self.progress = wx.Gauge(self.panel, range=100, size=(400, 24))
        self.progress.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.progress.SetForegroundColour(wx.Colour(0, 255, 0))
        self.sizer.Add(self.progress, 0, wx.ALL | wx.CENTER, 15)

        self.sub_msg = wx.StaticText(self.panel, label="")
        self.sub_msg.SetForegroundColour(wx.Colour(180, 180, 255))
        self.sizer.Add(self.sub_msg, 0, wx.ALL | wx.CENTER, 5)

        self.sizer.AddStretchSpacer()
        self.panel.SetSizer(self.sizer)

        self.Centre()
        self.Bind(wx.EVT_CLOSE, self.on_close)

        if self.phase == 1:
            self._play_oobe_music()

        self._run_phase()

    def _play_oobe_music(self):
        music_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music", OOBE_MUSIC)
        if os.path.exists(music_path):
            config_file = self.api.get_data_path("music_config.json")
            try:
                with open(config_file, "w") as f:
                    json.dump({"music": OOBE_MUSIC}, f)
            except Exception:
                pass

    def _run_phase(self):
        threading.Thread(target=self._do_phase, daemon=True).start()

    def _do_phase(self):
        if self.phase == 1:
            self._phase_install()
        elif self.phase == 2:
            self._phase_getting_ready(1)
        elif self.phase == 3:
            self._phase_getting_ready(2)
        elif self.phase == 4:
            self._phase_getting_ready(3)

    def _set_ui(self, header, msg, sub=""):
        wx.CallAfter(self.header.SetLabel, header)
        wx.CallAfter(self.msg.SetLabel, msg)
        wx.CallAfter(self.sub_msg.SetLabel, sub)

    def _set_progress(self, val):
        wx.CallAfter(self.progress.SetValue, val)

    def _phase_install(self):
        self._set_ui("Please wait while PyOS updates your system",
                      "Configuring updates...",
                      "Do not turn off your computer.")
        bars = [
            ("Installing update 1 of 3...", 30),
            ("Installing update 2 of 3...", 60),
            ("Installing update 3 of 3...", 100),
        ]
        total_sec = 50
        steps = 100
        for i in range(steps + 1):
            if self._cancelled:
                return
            pct = int(i * 100 / steps)
            self._set_progress(pct)

            elapsed_ratio = i / steps
            for label, threshold in bars:
                if pct <= threshold:
                    wx.CallAfter(self.sub_msg.SetLabel, label)
                    break

            time.sleep(total_sec / steps)

        self.state["phase"] = 2
        self._save_and_reboot()

    def _phase_getting_ready(self, num):
        self._set_ui("Getting ready...",
                      f"Please wait while PyOS prepares your system ({num}/3).",
                      "Do not turn off your computer.")
        total_sec = 10
        for i in range(101):
            if self._cancelled:
                return
            self._set_progress(i)
            time.sleep(total_sec / 100)

        if self.phase >= 4:
            self._finish_updates()
        else:
            self.state["phase"] = self.phase + 1
            self._save_and_reboot()

    def _save_and_reboot(self):
        try:
            with open(self.state_path, "w") as f:
                json.dump(self.state, f)
        except Exception:
            pass
        wx.CallAfter(self._reboot)

    def _reboot(self):
        subprocess.Popen([sys.executable, os.path.join(os.getcwd(), "desktop.py")], cwd=os.getcwd())
        wx.GetApp().ExitMainLoop()

    def _finish_updates(self):
        try:
            if os.path.exists(self.state_path):
                os.remove(self.state_path)
        except Exception:
            pass
        wx.CallAfter(self.on_finish)
        wx.CallAfter(self.Close)

    def on_close(self, event=None):
        self._cancelled = True
        self.Destroy()
