import wx
import os
import re
import subprocess
import threading
import shutil
import json
from api import BlindApp

try:
    from yt_dlp import YoutubeDL
    HAS_YTDLP = True
except ImportError:
    HAS_YTDLP = False


class YouTubePlayerApp(BlindApp):
    def __init__(self, api):
        super().__init__(api)
        self.name = "YouTube Player"
        self.description = "Search and play YouTube videos using yt-dlp."
        self.category = "Media"
        self.help_text = "Enter a YouTube URL or search query, select a result, and press Play. Use Stop to end playback."
        self.docs = "Uses yt-dlp to fetch video info and audio streams. Plays audio via ffplay. Requires yt-dlp installed (pip install yt-dlp)."
        self.ffplay_path = shutil.which("ffplay")
        self.playback_process = None
        self.current_title = ""
        self.search_results = []

    def run(self):
        self.frame = wx.Frame(None, title="YouTube Player", size=(600, 500))
        panel = wx.Panel(self.frame)
        panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        sizer = wx.BoxSizer(wx.VERTICAL)

        title = wx.StaticText(panel, label="YouTube Player")
        title.SetForegroundColour(wx.Colour(255, 255, 255))
        title.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(title, 0, wx.ALL | wx.CENTER, 15)

        if not HAS_YTDLP:
            warn = wx.StaticText(panel, label="yt-dlp is not installed. Run: pip install yt-dlp")
            warn.SetForegroundColour(wx.Colour(255, 100, 100))
            sizer.Add(warn, 0, wx.ALL | wx.CENTER, 10)

        url_lbl = wx.StaticText(panel, label="YouTube URL or Search Query:")
        url_lbl.SetForegroundColour(wx.Colour(200, 200, 200))
        sizer.Add(url_lbl, 0, wx.LEFT | wx.TOP, 10)

        input_row = wx.BoxSizer(wx.HORIZONTAL)
        self.url_input = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.url_input.SetBackgroundColour(wx.Colour(30, 30, 30))
        self.url_input.SetForegroundColour(wx.Colour(255, 255, 255))
        self.url_input.Bind(wx.EVT_SET_FOCUS, lambda e: (self.api.speak("YouTube URL or search query"), e.Skip()))
        input_row.Add(self.url_input, 1, wx.EXPAND)

        search_btn = wx.Button(panel, label="Search")
        search_btn.Bind(wx.EVT_BUTTON, self.on_search)
        self.url_input.Bind(wx.EVT_TEXT_ENTER, self.on_search)
        input_row.Add(search_btn, 0, wx.LEFT, 8)
        sizer.Add(input_row, 0, wx.EXPAND | wx.ALL, 10)

        results_lbl = wx.StaticText(panel, label="Results:")
        results_lbl.SetForegroundColour(wx.Colour(200, 200, 200))
        sizer.Add(results_lbl, 0, wx.LEFT, 10)

        self.results_list = wx.ListBox(panel, style=wx.LB_SINGLE)
        self.results_list.SetBackgroundColour(wx.Colour(20, 20, 20))
        self.results_list.SetForegroundColour(wx.Colour(255, 255, 255))
        self.results_list.Bind(wx.EVT_LISTBOX, self.on_result_focused)
        self.results_list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_play)
        sizer.Add(self.results_list, 1, wx.EXPAND | wx.ALL, 10)

        self.status_lbl = wx.StaticText(panel, label="Status: Ready")
        self.status_lbl.SetForegroundColour(wx.Colour(180, 255, 180))
        sizer.Add(self.status_lbl, 0, wx.LEFT | wx.RIGHT, 10)

        btn_row = wx.BoxSizer(wx.HORIZONTAL)
        play_btn = wx.Button(panel, label="Play")
        play_btn.Bind(wx.EVT_BUTTON, self.on_play)
        stop_btn = wx.Button(panel, label="Stop")
        stop_btn.Bind(wx.EVT_BUTTON, self.on_stop)
        btn_row.Add(play_btn, 1, wx.EXPAND | wx.ALL, 5)
        btn_row.Add(stop_btn, 1, wx.EXPAND | wx.ALL, 5)
        sizer.Add(btn_row, 0, wx.EXPAND | wx.ALL, 10)

        panel.SetSizer(sizer)
        self.frame.Bind(wx.EVT_CHAR_HOOK, self.on_frame_key)
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        self.frame.Show()
        self.api.speak("YouTube Player opened. Enter a URL or search query.")
        self.url_input.SetFocus()

    def on_search(self, event):
        if not HAS_YTDLP:
            self.api.speak("yt-dlp is not installed.")
            return
        query = self.url_input.GetValue().strip()
        if not query:
            self.api.speak("Enter a URL or search query.")
            return
        self.search_results = []
        self.results_list.Clear()
        self.api.speak("Searching...")
        self.status_lbl.SetLabel("Status: Searching...")
        threading.Thread(target=self._do_search, args=(query,), daemon=True).start()

    def _do_search(self, query):
        is_url = re.match(r'https?://', query)
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
            }
            if is_url:
                ydl_opts["noplaylist"] = True
            else:
                ydl_opts["default_search"] = "ytsearch10"
                ydl_opts["extract_flat"] = True
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(query, download=False)
                if info is None:
                    wx.CallAfter(self._search_done, [])
                    return
                if "entries" in info:
                    entries = info["entries"]
                else:
                    entries = [info]
                results = []
                for e in entries:
                    if e is None:
                        continue
                    title = e.get("title", "Unknown Title")
                    vid_id = e.get("id", "")
                    vid_url = f"https://youtube.com/watch?v={vid_id}"
                    duration = int(e.get("duration", 0) or 0)
                    dur_str = f"{duration // 60}:{duration % 60:02d}" if duration else ""
                    label = f"{title}  ({dur_str})" if dur_str else title
                    results.append((label, vid_url, title))
                wx.CallAfter(self._search_done, results)
        except Exception as ex:
            wx.CallAfter(self._search_error, str(ex))

    def _search_done(self, results):
        self.search_results = results
        self.results_list.Clear()
        for label, _, _ in results:
            self.results_list.Append(label)
        if results:
            self.results_list.SetSelection(0)
            self.results_list.SetFocus()
            self.api.speak(f"Found {len(results)} results. Select one and press Play.")
            self.status_lbl.SetLabel("Status: Results loaded")
        else:
            self.api.speak("No results found.")
            self.status_lbl.SetLabel("Status: No results")

    def _search_error(self, error):
        self.api.speak(f"Search failed: {error}")
        self.status_lbl.SetLabel(f"Status: Error - {error}")

    def on_result_focused(self, event):
        sel = self.results_list.GetSelection()
        if sel != wx.NOT_FOUND and sel < len(self.search_results):
            label, _, title = self.search_results[sel]
            self.current_title = title
            if not self.api.is_enhanced_mode():
                self.api.speak(label)

    def on_play(self, event):
        if not HAS_YTDLP:
            self.api.speak("yt-dlp is not installed.")
            return
        sel = self.results_list.GetSelection()
        if sel == wx.NOT_FOUND or sel >= len(self.search_results):
            self.api.speak("Select a result first.")
            return
        label, url, title = self.search_results[sel]
        self.current_title = title
        self.api.speak(f"Loading {title}")
        self.status_lbl.SetLabel(f"Status: Loading {title}")
        threading.Thread(target=self._do_play, args=(url,), daemon=True).start()

    def _do_play(self, url):
        self.on_stop()
        try:
            ydl_opts = {
                "quiet": True,
                "no_warnings": True,
                "format": "bestaudio/best",
                "noplaylist": True,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "Unknown")
                self.current_title = title
                audio_url = None
                formats = info.get("requested_formats") or info.get("formats")
                if info.get("url"):
                    audio_url = info["url"]
                elif formats:
                    audio_url = formats[0].get("url")
                if not audio_url:
                    wx.CallAfter(self._play_error, "Could not extract audio stream.")
                    return
            if self.ffplay_path:
                self.playback_process = subprocess.Popen(
                    [self.ffplay_path, "-nodisp", "-autoexit", "-loglevel", "quiet", audio_url],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                wx.CallAfter(self._play_started, title)
            else:
                wx.CallAfter(self._play_error, "ffplay not found. Install FFmpeg.")
        except Exception as ex:
            wx.CallAfter(self._play_error, str(ex))

    def _play_started(self, title):
        self.api.speak(f"Now playing: {title}")
        self.status_lbl.SetLabel(f"Status: Playing - {title}")

    def _play_error(self, error):
        self.api.speak(f"Playback failed: {error}")
        self.status_lbl.SetLabel(f"Status: Error - {error}")

    def on_stop(self, event=None):
        if self.playback_process and self.playback_process.poll() is None:
            try:
                self.playback_process.terminate()
                self.playback_process.wait(timeout=2)
            except Exception:
                try:
                    self.playback_process.kill()
                except Exception:
                    pass
        self.playback_process = None
        if event:
            self.api.speak("Playback stopped.")
            self.status_lbl.SetLabel("Status: Stopped")

    def on_frame_key(self, event):
        if event.GetKeyCode() == wx.WXK_ESCAPE:
            self.on_close()
        else:
            event.Skip()

    def on_close(self, event=None):
        self.on_stop()
        if self.frame:
            self.frame.Destroy()
        self.api.sounds.play("close")
        self.api.desktop.on_app_closed(self)
