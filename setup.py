from __future__ import annotations

import sys
import os
from cx_Freeze import Executable, setup

setup(
    name="speakswap",
    version="v1.0.0",
    description="Speakswap GUI",
    executables=[Executable("main.py", icon="icon.ico", target_name="voice-translator.exe")],
    options={
        "build_exe": {
            "include_files": [("icon.png")],
            "zip_include_packages": ["env/"],
            "zip_exclude_packages": []
        }
    },
)