import wx

from api import BlindApp


class PlatformDiagnosticsApp(BlindApp):
    def __init__(self, api):
        super().__init__(api)
        self.name = "Platform Diagnostics"
        self.description = "Inspect platform support, speech backends, shells, and optional dependencies."
        self.category = "System"
        self.help_text = "Use Refresh to rescan support, and Read Summary to hear the current report."
        self.docs = (
            "Platform Diagnostics shows which speech backends, audio helpers, host shells, and "
            "optional Python packages are available on the current machine."
        )
        self.report_ctrl = None

    def run(self):
        self.frame = wx.Frame(None, title="Platform Diagnostics", size=(700, 520))
        panel = wx.Panel(self.frame)
        panel.SetBackgroundColour(wx.Colour(15, 15, 15))

        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="Platform Diagnostics")
        title.SetForegroundColour(wx.Colour(255, 255, 255))
        title.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(title, 0, wx.ALL | wx.CENTER, 14)

        intro = wx.StaticText(
            panel,
            label="See what this machine currently supports across Windows, macOS, or Linux.",
        )
        intro.SetForegroundColour(wx.Colour(205, 205, 205))
        sizer.Add(intro, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.report_ctrl = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
        )
        self.report_ctrl.SetBackgroundColour(wx.Colour(20, 20, 20))
        self.report_ctrl.SetForegroundColour(wx.Colour(235, 235, 235))
        self.report_ctrl.SetFont(wx.Font(12, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        sizer.Add(self.report_ctrl, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        button_row = wx.BoxSizer(wx.HORIZONTAL)
        refresh_btn = wx.Button(panel, label="Refresh")
        read_btn = wx.Button(panel, label="Read Summary")
        close_btn = wx.Button(panel, label="Close")
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh)
        read_btn.Bind(wx.EVT_BUTTON, self.on_read_summary)
        close_btn.Bind(wx.EVT_BUTTON, self.on_close)
        button_row.Add(refresh_btn, 0, wx.RIGHT, 8)
        button_row.Add(read_btn, 0, wx.RIGHT, 8)
        button_row.AddStretchSpacer(1)
        button_row.Add(close_btn, 0)
        sizer.Add(button_row, 0, wx.EXPAND | wx.ALL, 12)

        panel.SetSizer(sizer)
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self.frame.Show()
        self.refresh_report(announce=True)

    def refresh_report(self, announce=False):
        report_text = self.api.format_support_report()
        self.report_ctrl.SetValue(report_text)
        if announce:
            summary = self._spoken_summary()
            self.api.speak(summary)

    def _spoken_summary(self):
        report = self.api.get_support_report()
        speech = "available" if report["capabilities"]["speech"] else "missing"
        desktop = "available" if report["capabilities"]["desktop_ui"] else "missing"
        audio_playback = "available" if report["capabilities"]["audio_playback"] else "missing"
        audio_recording = "available" if report["capabilities"]["audio_recording"] else "missing"
        shells = ", ".join(report["shells"].keys()) or "none"
        return (
            f"Platform Diagnostics. Platform {report['platform']}. Desktop UI {desktop}. "
            f"Speech {speech}. Audio playback {audio_playback}. Audio recording {audio_recording}. "
            f"Host shells: {shells}."
        )

    def on_refresh(self, event=None):
        self.refresh_report(announce=True)

    def on_read_summary(self, event=None):
        self.api.speak(self._spoken_summary())
