import wx
import os
import importlib.util
import speech
import kernel
import sounds
import threading
import traceback
from api import SystemAPI
from app_paths import get_data_dir

class DesktopFrame(wx.Frame):
    def __init__(self):
        super().__init__(None, title="PyOS Desktop", size=(800, 600))
        
        # Core OS path
        self.data_dir = get_data_dir()
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)
            
        self.os_kernel = kernel.VirtualOS()
        self.sound_manager = sounds.SoundManager(self.data_dir)
        self.api = SystemAPI(self, self.os_kernel, speech.engine, self.sound_manager)
        
        # Start background services
        self.api.message_service.start()
        self.music_thread = None
        self._start_music_service()
        
        self.apps = []
        self.app_buttons = []
        self.active_app = None
        
        # Play startup sound via theme
        self.api.play_sound("startup")

        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Desktop Header
        self.header = wx.StaticText(self.panel, label="PyOS Desktop")
        self.header.SetForegroundColour(wx.Colour(255, 255, 255))
        self.header.SetFont(wx.Font(18, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        self.sizer.Add(self.header, 0, wx.ALL | wx.CENTER, 20)

        self.scrolled_window = wx.ScrolledWindow(self.panel, style=wx.VSCROLL)
        self.scrolled_window.SetScrollRate(0, 20)
        self.scrolled_window.SetBackgroundColour(wx.Colour(0, 0, 0))
        self.app_sizer = wx.BoxSizer(wx.VERTICAL)
        self.scrolled_window.SetSizer(self.app_sizer)
        self.sizer.Add(self.scrolled_window, 1, wx.EXPAND | wx.ALL, 10)

        self.panel.SetSizer(self.sizer)

        # Global Hotkeys
        self.Bind(wx.EVT_CHAR_HOOK, self.on_key_down)

        self.load_plugins()
        wx.CallAfter(self.greet)

    def _start_music_service(self):
        self.music_thread = threading.Thread(target=self._background_music_thread, daemon=True)
        self.music_thread.start()

    def _background_music_thread(self):
        import time
        import json
        import sounddevice as sd
        import soundfile as sf
        import numpy as np
        
        # Wait for initial startup sound
        time.sleep(3)
        
        music_config_path = self.api.get_data_path("music_config.json")
        current_music = None
        stream = None
        
        while True:
            # Check for config update
            if os.path.exists(music_config_path):
                try:
                    with open(music_config_path, "r") as f:
                        data = json.load(f)
                        new_music = data.get("music", "None")
                except Exception:
                    new_music = "None"
            else:
                new_music = "None"
                
            # If music selection changed, stop stream and reset
            if new_music != current_music:
                current_music = new_music
                if stream:
                    stream.stop()
                    stream.close()
                    stream = None
            
            # Start playback if needed and not already playing
            if current_music != "None" and stream is None:
                music_dir = os.path.join(os.getcwd(), "music")
                music_path = os.path.join(music_dir, current_music)
                
                if os.path.exists(music_path):
                    try:
                        file = sf.SoundFile(music_path)
                        def callback(outdata, frames, time, status):
                            data = file.read(frames, fill_value=0)
                            if len(data) < frames:
                                file.seek(0)
                                data = np.concatenate([data, file.read(frames - len(data), fill_value=0)])
                            outdata[:] = data
                        
                        stream = sd.OutputStream(
                            samplerate=file.samplerate,
                            channels=file.channels,
                            callback=callback
                        )
                        stream.start()
                    except Exception:
                        time.sleep(5)
                else:
                    time.sleep(1)
            else:
                time.sleep(1)
        
    def on_key_down(self, event):
        keycode = event.GetKeyCode()
        if keycode == wx.WXK_F1:
            self.show_help()
        elif event.ControlDown() and keycode == ord('D'):
            self.show_docs()
        else:
            event.Skip()

    def show_help(self):
        if self.active_app:
            msg = f"Help for {self.active_app.name}: {self.active_app.help_text}"
        else:
            msg = "PyOS Desktop Help: Use Tab to navigate apps, Enter to launch, and F1 for help. Ctrl+D for app documentation."
        self.api.speak(msg)

    def show_docs(self):
        if self.active_app:
            msg = f"Documentation for {self.active_app.name}: {self.active_app.docs}"
        else:
            msg = "Desktop Documentation: PyOS is a modular OS for the blind. Developers can add apps to the apps folder."
        self.api.speak(msg)

    def greet(self):
        if not getattr(self.api.engine, "prefers_native_screen_reader", False):
            msg = "Welcome to PyOS. Use Tab to navigate through apps, and press Enter to launch."
            self.api.speak(msg)
        if self.app_buttons:
            self.app_buttons[0].SetFocus()

    def load_plugins(self):
        apps_dir = os.path.join(os.getcwd(), "apps")
        if not os.path.exists(apps_dir):
            os.makedirs(apps_dir)
        
        self.apps = []
        for filename in os.listdir(apps_dir):
            if filename.endswith(".py") and filename != "__init__.py":
                self.load_app_from_file(os.path.join(apps_dir, filename))

        self.refresh_app_list()

    def load_app_from_file(self, path):
        try:
            module_name = os.path.basename(path)[:-3]
            spec = importlib.util.spec_from_file_location(module_name, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            from api import BlindApp
            for attr in dir(module):
                cls = getattr(module, attr)
                if isinstance(cls, type) and issubclass(cls, BlindApp) and cls is not BlindApp:
                    try:
                        app_instance = cls(self.api)
                        self.apps.append(app_instance)
                        print(f"Loaded app: {app_instance.name}")
                    except Exception as e:
                        print(f"Error instantiating {cls.__name__} from {path}: {e}")
        except Exception as e:
            print(f"Failed to load module at {path}: {e}")

    def refresh_app_list(self):
        self.app_sizer.Clear(True)
        self.app_buttons = []

        for app in self.apps:
            btn = wx.Button(self.scrolled_window, label=app.name)
            btn.SetFont(wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_MEDIUM))
            btn.SetBackgroundColour(wx.Colour(40, 40, 40))
            btn.SetForegroundColour(wx.Colour(255, 255, 255))
            btn.SetName(app.name)
            btn.SetToolTip(app.description)
            btn.SetHelpText(app.description)
            
            btn.Bind(wx.EVT_BUTTON, lambda evt, a=app: self.on_launch_app(a))
            btn.Bind(wx.EVT_SET_FOCUS, lambda evt, a=app: self.on_item_focused(a))
            
            self.app_sizer.Add(btn, 0, wx.EXPAND | wx.ALL, 5)
            self.app_buttons.append(btn)
        
        self.app_sizer.Layout()
        self.panel.Layout()

    def on_item_focused(self, app):
        try:
            if self.IsActive():
                self.api.play_sound("nav")
                if not getattr(self.api.engine, "prefers_native_screen_reader", False):
                    self.api.speak(f"{app.name}: {app.description}")
        except Exception as e:
            print(f"Error in focus speech: {e}")

    def on_launch_app(self, app):
        try:
            self.active_app = app
            self.api.play_sound("launch")
            self.api.speak(f"Launching {app.name}")
            app.run()
        except Exception as e:
            msg = f"Failed to launch {app.name}: {e}"
            self.api.speak(msg)

    def on_app_closed(self, app_instance):
        self.active_app = None
        try:
            self.api.speak(f"{app_instance.name} closed.", interrupt=False)
        except Exception: pass
        wx.CallAfter(self._return_focus, app_instance.name)

    def _return_focus(self, app_name):
        # Update app_buttons list to remove any buttons that were destroyed
        self.app_buttons = [btn for btn in self.app_buttons if btn and btn.IsShownOnScreen()]
        
        if self.app_buttons:
            for btn in self.app_buttons:
                if btn.GetLabel() == app_name:
                    btn.SetFocus()
                    break
            else:
                self.app_buttons[0].SetFocus()

if __name__ == "__main__":
    app = wx.App()
    desktop = DesktopFrame()
    desktop.Show()
    app.MainLoop()
