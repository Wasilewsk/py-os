import wx
import threading
import time
import json
import os
from api import BlindApp

class TimerApp(BlindApp):
    def __init__(self, api):
        super().__init__(api)
        self.name = "Timer"
        self.description = "Set a simple countdown timer."
        self.help_text = "Enter seconds and press Enter. The app will alert you when done."
        self.docs = "Timer runs in the background and plays an alarm after the specified duration."
        self.auto_closing_after_finish = False
        self.cancel_btn = None
        self.timer_running = False
        self.timer_seconds = 0

    def run(self):
        self.frame = wx.Frame(None, title="Timer", size=(300, 200))
        panel = wx.Panel(self.frame)
        panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        sizer = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(panel, label="Enter seconds:")
        label.SetForegroundColour(wx.Colour(255, 255, 255))
        sizer.Add(label, 0, wx.ALL | wx.CENTER, 10)
        self.input_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.input_ctrl.Bind(wx.EVT_SET_FOCUS, lambda e: (self.api.speak("Enter seconds"), e.Skip()))
        sizer.Add(self.input_ctrl, 0, wx.EXPAND | wx.ALL, 10)
        start_btn = wx.Button(panel, label="Start Timer")
        self.cancel_btn = wx.Button(panel, label="Cancel Timer")
        self.cancel_btn.Disable()
        sizer.Add(start_btn, 0, wx.ALL | wx.CENTER, 10)
        sizer.Add(self.cancel_btn, 0, wx.ALL | wx.CENTER, 10)
        panel.SetSizer(sizer)
        start_btn.Bind(wx.EVT_BUTTON, self.on_start)
        self.cancel_btn.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_start)
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self.frame.Show()
        self.api.speak("Timer opened.")
        self.input_ctrl.SetFocus()

    def on_start(self, event):
        val = self.input_ctrl.GetValue()
        try:
            seconds = int(val)
            self.timer_running = True
            self.timer_seconds = seconds
            self.cancel_btn.Enable()
            self.api.speak(f"Timer started for {seconds} seconds.")
            threading.Thread(target=self.run_timer, args=(seconds,), daemon=True).start()
            self.frame.Hide()
        except ValueError:
            self.api.speak("Error: Please enter a valid number.")

    def on_cancel(self, event):
        self.timer_running = False
        self.input_ctrl.Enable()
        self.cancel_btn.Disable()
        self.frame.Show()
        self.api.speak("Timer cancelled.")

    def run_timer(self, seconds):
        elapsed = 0
        while elapsed < seconds and self.timer_running:
            remaining = seconds - elapsed
            if remaining > 0 and remaining % 10 == 0:
                wx.CallAfter(self.api.speak, f"{remaining} seconds remaining")
            time.sleep(1)
            elapsed += 1
        if self.timer_running:
            wx.CallAfter(self._finish_timer)

    def _finish_timer(self):
        self.timer_running = False
        self.api.speak("Timer finished!")
        self.api.play_sound("timer")
        self.cancel_btn.Disable()
        self.auto_closing_after_finish = True
        wx.CallLater(1200, lambda: self.on_close(play_close_sound=False))

    def on_close(self, event=None, play_close_sound=True):
        if self.frame:
            self.frame.Destroy()
            self.frame = None
        if play_close_sound:
            self.api.sounds.play("close")
        self.api.desktop.on_app_closed(self)
        self.auto_closing_after_finish = False

class RemindersApp(BlindApp):
    def __init__(self, api):
        super().__init__(api)
        self.name = "Reminders"
        self.description = "Save and hear your reminders."
        self.help_text = "Type a reminder and press Enter to save. Use arrows to browse saved reminders."
        self.docs = "Reminders are stored in the app data folder and persist between sessions."
        self.db_path = self.api.get_data_path("reminders.json")
        self.load_reminders()

    def load_reminders(self):
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    self.reminders = json.load(f)
            except: self.reminders = []
        else: self.reminders = []

    def save_reminders(self):
        try:
            with open(self.db_path, "w") as f:
                json.dump(self.reminders, f)
        except: pass

    def run(self):
        self.frame = wx.Frame(None, title="Reminders", size=(400, 400))
        panel = wx.Panel(self.frame)
        panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.input_ctrl = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.input_ctrl.Bind(wx.EVT_SET_FOCUS, lambda e: (self.api.speak("New reminder text"), e.Skip()))
        sizer.Add(self.input_ctrl, 0, wx.EXPAND | wx.ALL, 10)
        add_btn = wx.Button(panel, label="Add Reminder")
        sizer.Add(add_btn, 0, wx.ALL | wx.CENTER, 5)
        self.list = wx.ListBox(panel, style=wx.LB_SINGLE)
        self.list.SetBackgroundColour(wx.Colour(20, 20, 20))
        self.list.SetForegroundColour(wx.Colour(255, 255, 255))
        sizer.Add(self.list, 1, wx.EXPAND | wx.ALL, 10)
        panel.SetSizer(sizer)
        for r in self.reminders: self.list.Append(r)
        add_btn.Bind(wx.EVT_BUTTON, self.on_add)
        self.input_ctrl.Bind(wx.EVT_TEXT_ENTER, self.on_add)
        self.list.Bind(wx.EVT_LISTBOX, self.on_select)
        self.list.Bind(wx.EVT_KEY_DOWN, self.on_list_key)
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self.frame.Show()
        self.api.speak(f"Reminders opened. {len(self.reminders)} saved.")
        self.input_ctrl.SetFocus()

    def on_add(self, event):
        text = self.input_ctrl.GetValue().strip()
        if text:
            self.reminders.append(text)
            self.list.Append(text)
            self.save_reminders()
            self.input_ctrl.Clear()
            self.api.speak(f"Reminder added: {text}")

    def on_select(self, event):
        item = self.list.GetStringSelection()
        self.api.speak(item)

    def on_list_key(self, event):
        if event.GetKeyCode() == wx.WXK_DELETE:
            idx = self.list.GetSelection()
            if idx != wx.NOT_FOUND:
                text = self.reminders.pop(idx)
                self.list.Delete(idx)
                self.save_reminders()
                self.api.speak(f"Deleted: {text}")
        else:
            event.Skip()

class StopwatchApp(BlindApp):
    def __init__(self, api):
        super().__init__(api)
        self.name = "Stopwatch"
        self.description = "Count elapsed time with lap support."
        self.help_text = "Press Start/Stop or Space to toggle. L key records a lap. R key resets."
        self.docs = "Stopwatch tracks elapsed time and supports recording lap times."
        self.running = False
        self.elapsed = 0
        self.lap_count = 0
        self.lap_times = []
        self.stopwatch_thread = None

    def run(self):
        self.frame = wx.Frame(None, title="Stopwatch", size=(350, 450))
        panel = wx.Panel(self.frame)
        panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Stopwatch")
        title.SetForegroundColour(wx.Colour(255, 255, 255))
        title.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(title, 0, wx.ALL | wx.CENTER, 12)

        self.time_display = wx.StaticText(panel, label="00:00")
        self.time_display.SetForegroundColour(wx.Colour(0, 255, 0))
        self.time_display.SetFont(wx.Font(28, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(self.time_display, 0, wx.ALL | wx.CENTER, 15)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        self.start_stop_btn = wx.Button(panel, label="Start")
        self.lap_reset_btn = wx.Button(panel, label="Lap")
        self.lap_reset_btn.Disable()
        btn_row.Add(self.start_stop_btn, 1, wx.EXPAND | wx.ALL, 5)
        btn_row.Add(self.lap_reset_btn, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_row, 0, wx.EXPAND | wx.ALL, 10)

        close_btn = wx.Button(panel, label="Close")
        sizer.Add(close_btn, 0, wx.ALL | wx.CENTER, 10)

        lap_label = wx.StaticText(panel, label="Lap Times:")
        lap_label.SetForegroundColour(wx.Colour(200, 200, 200))
        sizer.Add(lap_label, 0, wx.LEFT | wx.RIGHT, 10)

        self.lap_list = wx.ListBox(panel, style=wx.LB_SINGLE)
        self.lap_list.SetBackgroundColour(wx.Colour(20, 20, 20))
        self.lap_list.SetForegroundColour(wx.Colour(255, 255, 255))
        sizer.Add(self.lap_list, 1, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(sizer)

        self.start_stop_btn.Bind(wx.EVT_BUTTON, self.on_start_stop)
        self.lap_reset_btn.Bind(wx.EVT_BUTTON, self.on_lap_reset)
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        self.frame.Bind(wx.EVT_CHAR_HOOK, self.on_frame_key)
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)

        self.frame.Show()
        self.api.speak("Stopwatch opened. Press Start to begin.")
        self.start_stop_btn.SetFocus()

    def on_frame_key(self, event):
        key = event.GetKeyCode()
        if key == wx.WXK_SPACE:
            self.on_start_stop()
        elif key in (ord('L'), ord('l')):
            self.on_lap_reset()
        elif key in (ord('R'), ord('r')):
            self.on_lap_reset()
        else:
            event.Skip()

    def on_start_stop(self, event=None):
        if not self.running:
            self.running = True
            self.start_stop_btn.SetLabel("Stop")
            self.lap_reset_btn.SetLabel("Lap")
            self.lap_reset_btn.Enable()
            self.stopwatch_thread = threading.Thread(target=self._run_stopwatch, daemon=True)
            self.stopwatch_thread.start()
            self.api.speak("Stopwatch started.")
        else:
            self.running = False
            self.start_stop_btn.SetLabel("Start")
            self.lap_reset_btn.SetLabel("Reset")
            self.api.speak(f"Stopwatch stopped at {self._format_time(self.elapsed)}.")

    def on_lap_reset(self, event=None):
        if self.running:
            self.lap_count += 1
            self.lap_times.append(self.elapsed)
            lap_str = f"Lap {self.lap_count}: {self._format_time(self.elapsed)}"
            self.lap_list.Append(lap_str)
            self.lap_list.SetSelection(self.lap_list.GetCount() - 1)
            self.api.speak(lap_str)
        else:
            self.elapsed = 0
            self.lap_count = 0
            self.lap_times = []
            self.lap_list.Clear()
            self.time_display.SetLabel("00:00")
            self.lap_reset_btn.SetLabel("Lap")
            self.lap_reset_btn.Disable()
            self.api.speak("Stopwatch reset.")

    def _run_stopwatch(self):
        while self.running:
            time.sleep(1)
            self.elapsed += 1
            wx.CallAfter(self._update_display)
            if self.elapsed % 10 == 0:
                wx.CallAfter(self.api.speak, self._format_time(self.elapsed))

    def _update_display(self):
        self.time_display.SetLabel(self._format_time(self.elapsed))

    def _format_time(self, total_seconds):
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def on_close(self, event=None):
        self.running = False
        if self.frame:
            self.frame.Destroy()
        self.api.sounds.play("close")
        self.api.desktop.on_app_closed(self)
