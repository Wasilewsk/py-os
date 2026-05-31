import copy
import os

import wx

from api import BlindApp


class ThemeCreatorApp(BlindApp):
    def __init__(self, api):
        super().__init__(api)
        self.name = "Theme Creator"
        self.description = "Create a new sound theme or open an existing one to edit."
        self.category = "System"
        self.help_text = "Choose Create New Theme or Open Theme. In the editor, select a sound or background music slot, browse for a file, and save."
        self.docs = (
            "Theme Creator lets you create and edit themes for the existing sound slots: "
            "startup, nav, alert, launch, close, alarm, timer, and background music."
        )
        self.sound_slots = [
            ("startup", "startup"),
            ("shutdown", "shutdown"),
            ("nav", "nav"),
            ("alert", "alert"),
            ("launch", "launch"),
            ("close", "close"),
            ("alarm", "alarm"),
            ("timer", "timer"),
            ("background music", "background_music"),
        ]
        self.slot_labels = [label for label, _key in self.sound_slots]
        self.slot_keys = [key for _label, key in self.sound_slots]
        self.slot_to_label = {key: label for label, key in self.sound_slots}
        self.label_to_slot = {label: key for label, key in self.sound_slots}
        self.theme_name = ""
        self.theme_data = {}
        self.is_new_theme = False

        self.title_label = None
        self.subtitle_label = None
        self.theme_name_input = None
        self.sound_list = None
        self.assignment_display = None
        self.browse_button = None
        self.save_button = None

    def run(self):
        self.theme_name = ""
        self.theme_data = {}
        self.is_new_theme = False
        self._show_launcher()

    def _discard_active_frame(self):
        if self.frame:
            try:
                self.frame.Unbind(wx.EVT_CLOSE)
            except Exception:
                pass
            active = self.frame
            self.frame = None
            active.Destroy()

    def _base_panel(self, title, subtitle, size=(560, 460)):
        self._discard_active_frame()
        self.frame = wx.Frame(None, title=title, size=size)
        panel = wx.Panel(self.frame)
        panel.SetBackgroundColour(wx.Colour(0, 0, 0))
        sizer = wx.BoxSizer(wx.VERTICAL)

        self.title_label = wx.StaticText(panel, label=title)
        self.title_label.SetForegroundColour(wx.Colour(255, 255, 255))
        self.title_label.SetFont(wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        sizer.Add(self.title_label, 0, wx.ALL | wx.CENTER, 14)

        self.subtitle_label = wx.StaticText(panel, label=subtitle)
        self.subtitle_label.SetForegroundColour(wx.Colour(210, 210, 210))
        self.subtitle_label.Wrap(500)
        sizer.Add(self.subtitle_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        panel.SetSizer(sizer)
        self.frame.Bind(wx.EVT_CLOSE, self.on_close)
        return panel, sizer

    def _show_launcher(self):
        panel, sizer = self._base_panel(
            "Theme Creator",
            "Choose whether to create a new theme or open an existing theme to edit.",
            size=(520, 260),
        )

        create_button = wx.Button(panel, label="Create New Theme")
        open_button = wx.Button(panel, label="Open Theme")

        create_button.SetBackgroundColour(wx.Colour(30, 90, 30))
        create_button.SetForegroundColour(wx.Colour(255, 255, 255))
        open_button.SetBackgroundColour(wx.Colour(40, 40, 90))
        open_button.SetForegroundColour(wx.Colour(255, 255, 255))

        sizer.Add(create_button, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)
        sizer.Add(open_button, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 16)

        create_button.Bind(wx.EVT_BUTTON, self.on_create_new_theme)
        open_button.Bind(wx.EVT_BUTTON, self.on_open_theme)

        self.frame.Show()
        create_button.SetFocus()
        self.api.speak("Theme Creator opened. Choose Create New Theme or Open Theme.")

    def on_create_new_theme(self, event=None):
        self.is_new_theme = True
        self.theme_name = ""
        self.theme_data = {}
        self._show_theme_name_screen()

    def _show_theme_name_screen(self):
        panel, sizer = self._base_panel(
            "Theme Creator",
            "Enter name for new theme:",
            size=(520, 240),
        )

        self.theme_name_input = wx.TextCtrl(panel, style=wx.TE_PROCESS_ENTER)
        self.theme_name_input.SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        next_button = wx.Button(panel, label="Next")

        sizer.Add(self.theme_name_input, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        sizer.Add(next_button, 0, wx.ALIGN_CENTER | wx.BOTTOM, 12)

        self.theme_name_input.Bind(wx.EVT_TEXT_ENTER, self.on_confirm_theme_name)
        next_button.Bind(wx.EVT_BUTTON, self.on_confirm_theme_name)

        self.frame.Show()
        self.theme_name_input.SetFocus()
        self.api.speak("Enter a name for your new theme, then press Next.")

    def on_confirm_theme_name(self, event=None):
        proposed_name = self.theme_name_input.GetValue().strip()
        if not proposed_name:
            self.api.speak("Theme name is required.")
            self.theme_name_input.SetFocus()
            return
        if any(char in proposed_name for char in ("/", "\\")):
            self.api.speak("Theme name cannot contain slashes.")
            self.theme_name_input.SetFocus()
            return
        if proposed_name in self.api.sounds.themes:
            self.api.speak("That theme already exists. Use Open Theme to edit it, or choose a different name.")
            self.theme_name_input.SetFocus()
            return

        self.theme_name = proposed_name
        self.theme_data = {}
        self._show_theme_editor()

    def on_open_theme(self, event=None):
        theme_names = sorted(self.api.sounds.get_available_themes(), key=str.lower)
        if not theme_names:
            self.api.speak("There are no themes to open.")
            return

        dialog = wx.SingleChoiceDialog(
            self.frame,
            "Choose a theme to edit.",
            "Open Theme",
            theme_names,
        )
        try:
            if dialog.ShowModal() != wx.ID_OK:
                self.api.speak("Open Theme cancelled.")
                return
            selected = dialog.GetStringSelection()
        finally:
            dialog.Destroy()

        self.is_new_theme = False
        self.theme_name = selected
        self.theme_data = copy.deepcopy(self.api.sounds.themes.get(selected, {}))
        self._show_theme_editor()

    def _show_theme_editor(self):
        panel, sizer = self._base_panel(
            "Theme Creator",
            f"Theme name: {self.theme_name}",
            size=(640, 520),
        )

        list_label = wx.StaticText(panel, label="Theme sounds:")
        list_label.SetForegroundColour(wx.Colour(255, 255, 255))
        sizer.Add(list_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.sound_list = wx.ListBox(panel, choices=self.slot_labels, style=wx.LB_SINGLE)
        self.sound_list.SetBackgroundColour(wx.Colour(20, 20, 20))
        self.sound_list.SetForegroundColour(wx.Colour(255, 255, 255))
        sizer.Add(self.sound_list, 1, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        current_label = wx.StaticText(panel, label="Current sound assignment:")
        current_label.SetForegroundColour(wx.Colour(255, 255, 255))
        sizer.Add(current_label, 0, wx.LEFT | wx.RIGHT | wx.BOTTOM, 8)

        self.assignment_display = wx.TextCtrl(
            panel,
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2,
        )
        self.assignment_display.SetBackgroundColour(wx.Colour(25, 25, 25))
        self.assignment_display.SetForegroundColour(wx.Colour(220, 220, 220))
        self.assignment_display.SetMinSize((-1, 110))
        sizer.Add(self.assignment_display, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        button_row = wx.BoxSizer(wx.HORIZONTAL)
        self.browse_button = wx.Button(panel, label="Browse...")
        self.save_button = wx.Button(panel, label="Save Theme")
        self.browse_button.SetBackgroundColour(wx.Colour(40, 40, 90))
        self.browse_button.SetForegroundColour(wx.Colour(255, 255, 255))
        self.save_button.SetBackgroundColour(wx.Colour(0, 100, 0))
        self.save_button.SetForegroundColour(wx.Colour(255, 255, 255))

        button_row.Add(self.browse_button, 0, wx.RIGHT, 10)
        button_row.AddStretchSpacer(1)
        button_row.Add(self.save_button, 0)
        sizer.Add(button_row, 0, wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)

        self.sound_list.Bind(wx.EVT_LISTBOX, self.on_sound_selected)
        self.sound_list.Bind(wx.EVT_LISTBOX_DCLICK, self.on_browse_file)
        self.browse_button.Bind(wx.EVT_BUTTON, self.on_browse_file)
        self.save_button.Bind(wx.EVT_BUTTON, self.on_save_theme)

        self.frame.Show()
        if self.slot_labels:
            self.sound_list.SetSelection(0)
            self._refresh_assignment_display()
        self.sound_list.SetFocus()
        self.api.speak(
            f"Editing theme {self.theme_name}. Select a sound name or background music, browse for an audio file, then save the theme."
        )

    def on_sound_selected(self, event=None):
        self._refresh_assignment_display()
        slot_key = self.get_selected_slot_key()
        if slot_key:
            slot_label = self.slot_to_label.get(slot_key, slot_key)
            if not self.api.is_enhanced_mode():
                self.api.speak(f"{slot_label} selected. {self._assignment_summary(slot_key)}")

    def get_selected_slot_key(self):
        if not self.sound_list:
            return None
        selection = self.sound_list.GetSelection()
        if selection == wx.NOT_FOUND:
            return None
        return self.label_to_slot.get(self.sound_list.GetString(selection))

    def _assignment_summary(self, slot_key):
        value = self.theme_data.get(slot_key)
        if isinstance(value, str) and value:
            return f"Assigned to file {os.path.basename(value)}."
        if isinstance(value, list) and value:
            return "Currently using a saved tone sequence."
        return "No sound assigned yet."

    def _format_assignment(self, slot_key):
        slot_label = self.slot_to_label.get(slot_key, slot_key)
        value = self.theme_data.get(slot_key)
        if isinstance(value, str) and value:
            return f"Sound: {slot_label}\nType: Audio file\nPath: {value}"
        if isinstance(value, list) and value:
            return f"Sound: {slot_label}\nType: Tone sequence\nValue: {value}"
        return f"Sound: {slot_label}\nType: Not assigned"

    def _refresh_assignment_display(self):
        slot_key = self.get_selected_slot_key()
        if not slot_key:
            self.assignment_display.SetValue("Select a sound name first.")
            return
        self.assignment_display.SetValue(self._format_assignment(slot_key))

    def on_browse_file(self, event=None):
        slot_key = self.get_selected_slot_key()
        if not slot_key:
            self.api.speak("Select a sound name before browsing for a file.")
            return
        slot_label = self.slot_to_label.get(slot_key, slot_key)

        wildcard = (
            "Audio files (*.wav;*.mp3;*.ogg;*.flac)|*.wav;*.mp3;*.ogg;*.flac|"
            "WAV files (*.wav)|*.wav|MP3 files (*.mp3)|*.mp3|"
            "OGG files (*.ogg)|*.ogg|FLAC files (*.flac)|*.flac"
        )
        dialog = wx.FileDialog(
            self.frame,
            f"Choose audio file for {slot_label}",
            wildcard=wildcard,
            style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
        )
        try:
            if dialog.ShowModal() != wx.ID_OK:
                self.api.speak("Browse cancelled.")
                return
            selected_path = dialog.GetPath()
        finally:
            dialog.Destroy()

        self.theme_data[slot_key] = selected_path
        self._refresh_assignment_display()
        self.api.speak(f"{slot_label} set to {os.path.basename(selected_path)}.")

    def _validate_theme_before_save(self):
        missing_events = []
        for slot_label, slot_key in self.sound_slots:
            value = self.theme_data.get(slot_key)
            if not value:
                missing_events.append(slot_label)
                continue
            if isinstance(value, str) and not os.path.exists(value):
                raise ValueError(f"The file for {slot_label} does not exist anymore.")
        if missing_events:
            missing_text = ", ".join(missing_events)
            raise ValueError(f"Assign a sound file for each sound before saving. Missing: {missing_text}.")

    def on_save_theme(self, event=None):
        try:
            self._validate_theme_before_save()
        except ValueError as error:
            self.api.speak(str(error))
            return

        self.api.sounds.themes[self.theme_name] = copy.deepcopy(self.theme_data)
        self.api.sounds.save_custom_themes()
        self.api.sounds.save_theme_name(self.theme_name)
        self.api.sounds.current_theme = self.theme_name
        self.api.speak(f"Theme {self.theme_name} saved and applied.")
        self.on_close()
