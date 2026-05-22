import importlib.util
import os
import platform
import subprocess
import shutil
from pathlib import Path


def get_platform_name():
    return platform.system()


def command_path(name):
    return shutil.which(name)


def module_available(name):
    return importlib.util.find_spec(name) is not None


def get_speech_backends():
    system = get_platform_name()
    backends = []
    repo_root = Path(__file__).resolve().parent
    nvda_dlls = [
        repo_root / "nvdaControllerClient64.dll",
        repo_root / "nvdaControllerClient32.dll",
    ]
    if system == "Windows" and any(path.exists() for path in nvda_dlls):
        backends.append(("nvda", "NVDA controller (when running)"))
    if system == "Darwin" and command_path("say"):
        backends.append(("say", "macOS say"))
    if system == "Linux" and command_path("spd-say"):
        backends.append(("spd-say", "Speech Dispatcher"))
    if system in {"Linux", "Darwin"} and command_path("espeak-ng"):
        backends.append(("espeak-ng", "eSpeak NG"))
    if system in {"Linux", "Darwin"} and command_path("espeak"):
        backends.append(("espeak", "eSpeak"))
    if module_available("pyttsx3"):
        backends.append(("pyttsx3", "pyttsx3"))
    return backends


def get_default_open_command():
    system = get_platform_name()
    if system == "Windows":
        return "os.startfile"
    if system == "Darwin" and command_path("open"):
        return "open"
    if system == "Linux" and command_path("xdg-open"):
        return "xdg-open"
    return None


def open_external_file(path):
    system = get_platform_name()
    if system == "Windows":
        os.startfile(path)
        return
    if system == "Darwin":
        opener = command_path("open")
        if opener:
            subprocess.Popen([opener, path])
            return
    if system == "Linux":
        opener = command_path("xdg-open")
        if opener:
            subprocess.Popen([opener, path])
            return
    raise RuntimeError("No desktop file opener is available.")


def get_shells():
    system = get_platform_name()
    if system == "Windows":
        return {
            name: path
            for name, path in {
                "cmd": command_path("cmd.exe"),
                "powershell": command_path("powershell.exe") or command_path("pwsh"),
            }.items()
            if path
        }
    return {
        shell_name: shell_path
        for shell_name in ("zsh", "bash", "sh", "fish")
        for shell_path in [command_path(shell_name)]
        if shell_path
    }


def get_support_report():
    system = get_platform_name()
    speech_backends = get_speech_backends()
    report = {
        "platform": system,
        "speech_backends": speech_backends,
        "python_modules": {
            "wx": module_available("wx"),
            "pyttsx3": module_available("pyttsx3"),
            "sounddevice": module_available("sounddevice"),
            "soundfile": module_available("soundfile"),
            "numpy": module_available("numpy"),
        },
        "commands": {
            "ffplay": command_path("ffplay"),
            "ffmpeg": command_path("ffmpeg"),
            "open_command": get_default_open_command(),
        },
        "shells": get_shells(),
    }

    report["capabilities"] = {
        "desktop_ui": report["python_modules"]["wx"],
        "speech": bool(speech_backends),
        "audio_playback": bool(
            report["commands"]["ffplay"]
            or (system == "Darwin" and command_path("afplay"))
            or report["python_modules"]["sounddevice"]
        ),
        "audio_recording": report["python_modules"]["sounddevice"] and report["python_modules"]["soundfile"],
        "open_external_files": bool(report["commands"]["open_command"]),
        "host_shells": bool(report["shells"]),
    }
    return report


def format_support_report():
    report = get_support_report()
    speech_names = ", ".join(label for _, label in report["speech_backends"]) or "none"
    shell_names = ", ".join(report["shells"].keys()) or "none"
    command = report["commands"]["open_command"] or "none"
    modules = ", ".join(
        f"{name}={'yes' if available else 'no'}"
        for name, available in report["python_modules"].items()
    )
    capabilities = ", ".join(
        f"{name}={'yes' if available else 'no'}"
        for name, available in report["capabilities"].items()
    )
    return (
        f"Platform: {report['platform']}\n"
        f"Speech backends: {speech_names}\n"
        f"Host shells: {shell_names}\n"
        f"Default file opener: {command}\n"
        f"Python modules: {modules}\n"
        f"Capabilities: {capabilities}"
    )
