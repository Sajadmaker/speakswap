from __future__ import annotations

import sys
import os
from cx_Freeze import Executable, setup

# Dependencies from requirements.txt
build_exe_options = {
    "packages": [
        "tkinter", "gtts", "speech_recognition", "playsound", "deep_translator",
        "google.transliteration", "queue", "time", "pyttsx3", "sounddevice",
        "numpy", "scipy", "json", "dotenv", "wave", "io", "torch", "transformers",
        "torchaudio", "PIL", "requests"
    ],
    "include_files": [
        "icon.png",
        "icon.ico",
        "voice_settings.json"
    ],
    "excludes": [],
    "include_msvcr": True,
    "zip_include_packages": ["env/"],
    "zip_exclude_packages": []
}

# Base for Windows systems
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="speakswap",
    version="v1.0.0",
    description="SpeakSwap - Modern Voice Translator",
    options={"build_exe": build_exe_options},
    executables=[
        Executable(
            "main.py",
            base=base,
            icon="icon.ico",
            target_name="SpeakSwap.exe",
            copyright="Copyright © 2024 The Minions Team"
        )
    ]
)