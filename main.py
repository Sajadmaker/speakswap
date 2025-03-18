import os
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import speech_recognition as sr
import pyttsx3
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import json
from dotenv import load_dotenv
import wave
import io
import torch
import torchaudio
import torchaudio.transforms as T
from PIL import Image, ImageTk
import requests
from io import BytesIO
import queue
import time
import traceback
import tempfile
import sys
from pathlib import Path

# Try importing optional dependencies
try:
    from playsound import playsound
    PLAYSOUND_AVAILABLE = True
except ImportError:
    PLAYSOUND_AVAILABLE = False

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False

try:
    from deep_translator import GoogleTranslator
    TRANSLATOR_AVAILABLE = True
except ImportError:
    TRANSLATOR_AVAILABLE = False

try:
    from google.transliteration import transliterate_text
    TRANSLITERATION_AVAILABLE = True
except ImportError:
    TRANSLITERATION_AVAILABLE = False

try:
    from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# Load environment variables
load_dotenv()

# Constants
APP_NAME = "SpeakSwap 🎙️ - Modern Voice Translator"
APP_VERSION = "1.0.1"
DEFAULT_WINDOW_SIZE = "1200x900"
TEMP_DIR = tempfile.gettempdir()

class ModernButton(tk.Button):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            font=("Helvetica", 11),
            bg="#4a86e8",
            fg="white",
            padx=20,
            pady=10,
            relief=tk.FLAT,
            cursor="hand2"
        )
        self.bind("<Enter>", lambda e: self.config(bg="#357abd"))
        self.bind("<Leave>", lambda e: self.config(bg="#4a86e8"))

class ModernText(tk.Text):
    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.config(
            font=("Helvetica", 11),
            bg="#f8f9fa",
            fg="#2c3e50",
            padx=15,
            pady=15,
            relief=tk.FLAT,
            wrap=tk.WORD
        )
        self.bind("<Key>", self._on_key_press)
        
    def _on_key_press(self, event):
        if event.keysym == 'Return' and event.state & 0x1:  # Shift+Enter
            self.insert(tk.END, '\n')
            return 'break'

class SpeakSwapApp:
    def __init__(self):
        # Initialize variables
        self.win = None
        self.keep_running = False
        self.translation_thread = None
        self.translation_queue = queue.Queue()
        self.whisper_model = None
        self.whisper_processor = None
        self.whisper_pipe = None
        self.engine = None
        
        # Initialize UI and other components
        self.init_app()
        
    def init_app(self):
        """Initialize the application components in the correct order"""
        # Initialize main window
        self.win = tk.Tk()
        self.win.geometry(DEFAULT_WINDOW_SIZE)
        self.win.title(APP_NAME)
        self.win.configure(bg="#ffffff")
        self.win.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Initialize TTS engine
        try:
            self.engine = pyttsx3.init()
        except Exception as e:
            print(f"Failed to initialize TTS engine: {str(e)}")
            self.engine = None
        
        # Load settings
        self.voice_settings = self.load_voice_settings()
        
        # Set window icon
        self.set_window_icon()
        
        # Initialize language codes
        self._language_codes = self.get_language_codes()
        
        # Setup UI components
        self.setup_ui()
        
        # Setup keyboard shortcuts
        self.setup_keyboard_shortcuts()
        
        # Initialize Whisper model if available
        if WHISPER_AVAILABLE and self.voice_settings.get("use_whisper", True):
            threading.Thread(target=self.setup_whisper_model, daemon=True).start()
    
    def get_language_codes(self):
        """Return a dictionary of supported languages and their codes"""
        return {
            "English": "en",
            "Hindi": "hi",
            "Bengali": "bn",
            "Spanish": "es",
            "Chinese (Simplified)": "zh-CN",
            "Russian": "ru",
            "Japanese": "ja",
            "Korean": "ko",
            "German": "de",
            "French": "fr",
            "Tamil": "ta",
            "Telugu": "te",
            "Kannada": "kn",
            "Gujarati": "gu",
            "Punjabi": "pa",
            "Malayalam": "ml",
            "Italian": "it",
            "Portuguese": "pt",
            "Arabic": "ar",
            "Dutch": "nl",
            "Greek": "el",
            "Hebrew": "he",
            "Swedish": "sv",
            "Turkish": "tr",
            "Vietnamese": "vi",
            "Thai": "th",
            "Ukrainian": "uk",
            "Polish": "pl",
            "Auto Detect": "auto"
        }
    
    @property
    def language_codes(self):
        return self._language_codes
            
    def set_window_icon(self):
        """Set the window icon if the file exists"""
        try:
            icon_paths = ["icon.png", "assets/icon.png", 
                         os.path.join(os.path.dirname(__file__), "icon.png"),
                         os.path.join(os.path.dirname(__file__), "assets/icon.png")]
            
            for path in icon_paths:
                if os.path.exists(path):
                    icon = tk.PhotoImage(file=path)
                    self.win.iconphoto(False, icon)
                    return
        except Exception as e:
            print(f"Failed to set window icon: {str(e)}")
    
    def setup_whisper_model(self):
        """Initialize the Whisper model for speech recognition"""
        try:
            self.update_status("Loading Whisper model...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            
            # Use a smaller model by default to save memory
            model_id = "openai/whisper-base"
            if torch.cuda.is_available() and torch.cuda.get_device_properties(0).total_memory >= 8e9:
                # Use larger model if GPU has 8+ GB memory
                model_id = "openai/whisper-large-v3"
            
            self.whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id, 
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                low_cpu_mem_usage=True
            ).to(device)
            
            self.whisper_processor = AutoProcessor.from_pretrained(model_id)
            
            self.whisper_pipe = pipeline(
                "automatic-speech-recognition",
                model=self.whisper_model,
                tokenizer=self.whisper_processor.tokenizer,
                feature_extractor=self.whisper_processor.feature_extractor,
                max_new_tokens=128,
                chunk_length_s=30,
                batch_size=16
            )
            
            self.update_status("Whisper model loaded successfully")
        except Exception as e:
            error_msg = f"Failed to initialize Whisper model: {str(e)}"
            print(error_msg)
            self.update_status(error_msg, is_error=True)
            self.whisper_pipe = None
    
    def load_voice_settings(self):
        """Load voice settings from file or use defaults"""
        try:
            settings_paths = ["voice_settings.json", 
                            os.path.join(os.path.dirname(__file__), "voice_settings.json")]
            
            for path in settings_paths:
                if os.path.exists(path):
                    with open(path, 'r') as f:
                        return json.load(f)
        except Exception as e:
            print(f"Failed to load voice settings: {str(e)}")
            
        # Default settings
        return {
            "rate": 150,
            "volume": 1.0,
            "pitch": 1.0,
            "voice_id": None,
            "use_whisper": WHISPER_AVAILABLE,
            "enhance_audio": True,
            "auto_scroll": True,
            "use_gtts": GTTS_AVAILABLE,
            "fallback_to_gtts": True
        }

    def save_voice_settings(self):
        """Save voice settings to file"""
        try:
            settings_path = os.path.join(os.path.dirname(__file__), "voice_settings.json")
            with open(settings_path, 'w') as f:
                json.dump(self.voice_settings, f)
        except Exception as e:
            print(f"Failed to save voice settings: {str(e)}")
            self.update_status("Could not save settings", is_error=True)

    def setup_ui(self):
        """Setup the user interface components"""
        # Main container with padding
        self.main_container = tk.Frame(self.win, bg="#ffffff", padx=30, pady=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Header section with gradient effect
        self.setup_header_section()
        
        # Language selection frame
        self.setup_language_selection()
        
        # Text areas frame with scrollbars
        self.setup_text_areas()
        
        # Control buttons frame
        self.setup_control_buttons()
        
        # Status bar with progress
        self.setup_status_bar()
        
        # Initialize button states
        self.stop_button.config(state=tk.DISABLED)
        
        # Run dependency check
        self.check_dependencies()

    def setup_header_section(self):
        """Setup header section with title and settings button"""
        self.header_frame = tk.Frame(self.main_container, bg="#ffffff")
        self.header_frame.pack(fill=tk.X, pady=(0, 20))

        # Logo and title
        try:
            icon_paths = ["icon.png", "assets/icon.png", 
                         os.path.join(os.path.dirname(__file__), "icon.png"),
                         os.path.join(os.path.dirname(__file__), "assets/icon.png")]
            
            for path in icon_paths:
                if os.path.exists(path):
                    logo_image = Image.open(path)
                    logo_image = logo_image.resize((40, 40))
                    logo_photo = ImageTk.PhotoImage(logo_image)
                    logo_label = tk.Label(
                        self.header_frame,
                        image=logo_photo,
                        bg="#ffffff"
                    )
                    logo_label.image = logo_photo
                    logo_label.pack(side=tk.LEFT, padx=(0, 10))
                    break
        except Exception as e:
            print(f"Failed to load logo: {str(e)}")

        self.title_label = tk.Label(
            self.header_frame,
            text="SpeakSwap",
            font=("Helvetica", 32, "bold"),
            bg="#ffffff",
            fg="#2c3e50"
        )
        self.title_label.pack(side=tk.LEFT)

        self.subtitle_label = tk.Label(
            self.header_frame,
            text=f"Real-time Voice Translator v{APP_VERSION}",
            font=("Helvetica", 14),
            bg="#ffffff",
            fg="#7f8c8d"
        )
        self.subtitle_label.pack(side=tk.LEFT, padx=(10, 0))

        # Settings button
        self.settings_button = ModernButton(
            self.header_frame,
            text="⚙️ Settings",
            command=self.open_settings,
            bg="#95a5a6"
        )
        self.settings_button.pack(side=tk.RIGHT)

    def setup_language_selection(self):
        """Setup language selection dropdowns"""
        self.lang_frame = tk.Frame(self.main_container, bg="#ffffff")
        self.lang_frame.pack(fill=tk.X, pady=(0, 20))

        # Input language selection
        self.input_lang_frame = tk.Frame(self.lang_frame, bg="#ffffff")
        self.input_lang_frame.pack(side=tk.LEFT, expand=True)

        self.input_lang_label = tk.Label(
            self.input_lang_frame,
            text="Input Language",
            font=("Helvetica", 12, "bold"),
            bg="#ffffff",
            fg="#2c3e50"
        )
        self.input_lang_label.pack(anchor=tk.W)

        self.input_lang = ttk.Combobox(
            self.input_lang_frame,
            values=list(self.language_codes.keys()),
            width=25,
            font=("Helvetica", 11)
        )
        self.input_lang.set("Auto Detect")
        self.input_lang.pack(pady=(5, 0))

        # Arrow with animation
        self.arrow_label = tk.Label(
            self.lang_frame,
            text="→",
            font=("Helvetica", 24),
            bg="#ffffff",
            fg="#3498db"
        )
        self.arrow_label.place(relx=0.5, rely=0.5, anchor="center")
        self.animate_arrow()

        # Output language selection
        self.output_lang_frame = tk.Frame(self.lang_frame, bg="#ffffff")
        self.output_lang_frame.pack(side=tk.RIGHT, expand=True)

        self.output_lang_label = tk.Label(
            self.output_lang_frame,
            text="Output Language",
            font=("Helvetica", 12, "bold"),
            bg="#ffffff",
            fg="#2c3e50"
        )
        self.output_lang_label.pack(anchor=tk.W)

        self.output_lang = ttk.Combobox(
            self.output_lang_frame,
            values=list(self.language_codes.keys()),
            width=25,
            font=("Helvetica", 11)
        )
        self.output_lang.set("English")
        self.output_lang.pack(pady=(5, 0))

        # Swap languages button
        self.swap_button = ModernButton(
            self.lang_frame,
            text="🔄",
            command=self.swap_languages,
            bg="#3498db",
            padx=10
        )
        self.swap_button.place(relx=0.5, rely=0.5, anchor="center")

    def setup_text_areas(self):
        """Setup text areas for input and output"""
        self.text_frame = tk.Frame(self.main_container, bg="#ffffff")
        self.text_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Input text area with scrollbar
        self.input_frame = tk.Frame(self.text_frame, bg="#ffffff")
        self.input_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        self.input_scrollbar = ttk.Scrollbar(self.input_frame)
        self.input_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.input_text = ModernText(
            self.input_frame,
            height=8,
            yscrollcommand=self.input_scrollbar.set
        )
        self.input_text.pack(fill=tk.BOTH, expand=True)
        self.input_scrollbar.config(command=self.input_text.yview)

        # Output text area with scrollbar
        self.output_frame = tk.Frame(self.text_frame, bg="#ffffff")
        self.output_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(10, 0))

        self.output_scrollbar = ttk.Scrollbar(self.output_frame)
        self.output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.output_text = ModernText(
            self.output_frame,
            height=8,
            yscrollcommand=self.output_scrollbar.set
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)
        self.output_scrollbar.config(command=self.output_text.yview)

    def setup_control_buttons(self):
        """Setup control buttons for the application"""
        self.button_frame = tk.Frame(self.main_container, bg="#ffffff")
        self.button_frame.pack(fill=tk.X, pady=(0, 20))

        # Start button
        self.start_button = ModernButton(
            self.button_frame,
            text="🎙️ Start Translation",
            command=self.run_translator
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        # Stop button
        self.stop_button = ModernButton(
            self.button_frame,
            text="⏹️ Stop",
            command=self.kill_execution,
            bg="#e74c3c"
        )
        self.stop_button.pack(side=tk.LEFT, padx=10)

        # Clear button
        self.clear_button = ModernButton(
            self.button_frame,
            text="🗑️ Clear",
            command=self.clear_text,
            bg="#95a5a6"
        )
        self.clear_button.pack(side=tk.LEFT, padx=10)
        
        # Manual translate button
        self.manual_translate_button = ModernButton(
            self.button_frame,
            text="🔄 Translate Text",
            command=self.translate_text_input,
            bg="#2ecc71"
        )
        self.manual_translate_button.pack(side=tk.LEFT, padx=10)

        # About button
        self.about_button = ModernButton(
            self.button_frame,
            text="ℹ️ About",
            command=self.open_about_page,
            bg="#95a5a6"
        )
        self.about_button.pack(side=tk.LEFT, padx=10)

    def setup_status_bar(self):
        """Setup status bar with progress indicator"""
        self.status_frame = tk.Frame(self.win, bg="#f8f9fa", height=30)
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.status_label = tk.Label(
            self.status_frame,
            text="Ready",
            font=("Helvetica", 9),
            bg="#f8f9fa",
            fg="#7f8c8d"
        )
        self.status_label.pack(side=tk.LEFT, padx=10)

        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.status_frame,
            variable=self.progress_var,
            maximum=100,
            mode='indeterminate'
        )
        self.progress_bar.pack(side=tk.RIGHT, padx=10, fill=tk.X, expand=True)

    def check_dependencies(self):
        """Check for required dependencies and show warnings if needed"""
        missing_deps = []
        
        if not TRANSLATOR_AVAILABLE:
            missing_deps.append("deep-translator")
        
        if not WHISPER_AVAILABLE and self.voice_settings.get("use_whisper", True):
            missing_deps.append("transformers")
            # Disable whisper since it's not available
            self.voice_settings["use_whisper"] = False
            self.save_voice_settings()
        
        if not PLAYSOUND_AVAILABLE and not self.engine:
            missing_deps.append("playsound or pyttsx3")
        
        if missing_deps:
            messagebox.showwarning(
                "Missing Dependencies",
                f"The following packages are missing or failed to load:\n" +
                "\n".join(f"- {dep}" for dep in missing_deps) +
                "\n\nSome features may not work properly. " +
                "Please install them using pip install package_name."
            )

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts for the application"""
        self.win.bind('<Control-s>', lambda e: self.run_translator())
        self.win.bind('<Control-x>', lambda e: self.kill_execution())
        self.win.bind('<Control-a>', lambda e: self.open_about_page())
        self.win.bind('<Control-l>', lambda e: self.clear_text())
        self.win.bind('<Control-t>', lambda e: self.translate_text_input())
        self.win.bind('<Control-comma>', lambda e: self.open_settings())
        self.win.bind('<F5>', lambda e: self.run_translator())
        self.win.bind('<Escape>', lambda e: self.kill_execution())

    def animate_arrow(self):
        """Animate the arrow between input and output languages"""
        if not hasattr(self, 'win') or not self.win:
            return
            
        colors = ["#3498db", "#2980b9", "#3498db"]
        current_color = self.arrow_label.cget("fg")
        next_color = colors[(colors.index(current_color) + 1) % len(colors)]
        self.arrow_label.config(fg=next_color)
        self.win.after(1000, self.animate_arrow)

    def swap_languages(self):
        """Swap input and output languages"""
        input_lang = self.input_lang.get()
        output_lang = self.output_lang.get()
        
        # Don't swap if one of the languages is Auto Detect
        if input_lang == "Auto Detect" or output_lang == "Auto Detect":
            return
            
        self.input_lang.set(output_lang)
        self.output_lang.set(input_lang)
        
        # Also swap text content
        input_text = self.input_text.get("1.0", tk.END).strip()
        output_text = self.output_text.get("1.0", tk.END).strip()
        
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        
        if output_text:
            self.input_text.insert(tk.END, output_text)
        
        if input_text:
            self.output_text.insert(tk.END, input_text)

    def open_settings(self):
        """Open settings dialog"""
        if not self.engine:
            messagebox.showerror("Error", "TTS engine not available. Cannot modify voice settings.")
            return
            
        settings_window = tk.Toplevel(self.win)
        settings_window.title("Voice Settings")
        settings_window.geometry("400x600")
        settings_window.configure(bg="#ffffff")
        settings_window.transient(self.win)
        settings_window.grab_set()
        
        try:
            settings_window.iconphoto(False, tk.PhotoImage(file="icon.png"))
        except:
            pass

        # Title
        title_label = tk.Label(
            settings_window,
            text="Voice Settings",
            font=("Helvetica", 20, "bold"),
            bg="#ffffff",
            fg="#2c3e50"
        )
        title_label.pack(pady=(20, 10))

        # Voice selection
        voice_frame = tk.Frame(settings_window, bg="#ffffff")
        voice_frame.pack(fill=tk.X, padx=20, pady=10)

        voice_label = tk.Label(
            voice_frame,
            text="Voice",
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#2c3e50"
        )
        voice_label.pack(anchor=tk.W)

        try:
            voices = self.engine.getProperty('voices')
            voice_ids = [voice.id for voice in voices]
            voice_names = [f"{voice.name} ({voice.id})" for voice in voices]
        except:
            voices = []
            voice_ids = ["default"]
            voice_names = ["Default Voice"]

        self.voice_var = tk.StringVar(value=self.voice_settings.get("voice_id", voice_ids[0] if voice_ids else "default"))
        
        voice_combo = ttk.Combobox(
            voice_frame,
            textvariable=self.voice_var,
            values=voice_ids,
            width=30
        )
        voice_combo.pack(pady=5)

        # Rate slider
        rate_frame = tk.Frame(settings_window, bg="#ffffff")
        rate_frame.pack(fill=tk.X, padx=20, pady=10)

        rate_label = tk.Label(
            rate_frame,
            text="Speech Rate",
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#2c3e50"
        )
        rate_label.pack(anchor=tk.W)

        self.rate_var = tk.DoubleVar(value=self.voice_settings.get("rate", 150))
        rate_scale = ttk.Scale(
            rate_frame,
            from_=50,
            to=300,
            variable=self.rate_var,
            orient=tk.HORIZONTAL
        )
        rate_scale.pack(fill=tk.X, pady=5)
        
        # Rate value display
        self.rate_value_label = tk.Label(
            rate_frame,
            text=f"Value: {int(self.rate_var.get())}",
            bg="#ffffff"
        )
        self.rate_value_label.pack(anchor=tk.E)
        rate_scale.bind("<Motion>", lambda e: self.rate_value_label.config(text=f"Value: {int(self.rate_var.get())}"))

        # Volume slider
        volume_frame = tk.Frame(settings_window, bg="#ffffff")
        volume_frame.pack(fill=tk.X, padx=20, pady=10)

        volume_label = tk.Label(
            volume_frame,
            text="Volume",
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#2c3e50"
        )
        volume_label.pack(anchor=tk.W)

        self.volume_var = tk.DoubleVar(value=self.voice_settings.get("volume", 1.0))
        volume_scale = ttk.Scale(
            volume_frame,
            from_=0.0,
            to=1.0,
            variable=self.volume_var,
            orient=tk.HORIZONTAL
        )
        volume_scale.pack(fill=tk.X, pady=5)
        
        # Volume value display
        self.volume_value_label = tk.Label(
            volume_frame,
            text=f"Value: {self.volume_var.get():.1f}",
            bg="#ffffff"
        )
        self.volume_value_label.pack(anchor=tk.E)
        volume_scale.bind("<Motion>", lambda e: self.volume_value_label.config(text=f"Value: {self.volume_var.get():.1f}"))

        # Pitch slider
        pitch_frame = tk.Frame(settings_window, bg="#ffffff")
        pitch_frame.pack(fill=tk.X, padx=20, pady=10)

        pitch_label = tk.Label(
            pitch_frame,
            text="Pitch",
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#2c3e50"
        )
        pitch_label.pack(anchor=tk.W)

        self.pitch_var = tk.DoubleVar(value=self.voice_settings.get("pitch", 1.0))
        pitch_scale = ttk.Scale(
            pitch_frame,
            from_=0.5,
            to=2.0,
            variable=self.pitch_var,
            orient=tk.HORIZONTAL
        )
        pitch_scale.pack(fill=tk.X, pady=5)
        
        # Pitch value display
        self.pitch_value_label = tk.Label(
            pitch_frame,
            text=f"Value: {self.pitch_var.get():.1f}",
            bg="#ffffff"
        )
        self.pitch_value_label.pack(anchor=tk.E)
        pitch_scale.bind("<Motion>", lambda e: self.pitch_value_label.config(text=f"Value: {self.pitch_var.get():.1f}"))

        # Advanced settings
        advanced_frame = tk.Frame(settings_window, bg="#ffffff")
        advanced_frame.pack(fill=tk.X, padx=20, pady=10)

        advanced_label = tk.Label(
            advanced_frame,
            text="Advanced Settings",
            font=("Helvetica", 12, "bold"),
            bg="#ffffff",
            fg="#2c3e50"
        )
        advanced_label.pack(anchor=tk.W)

        # Use Whisper checkbox - only if available
        self.use_whisper_var = tk.BooleanVar(value=self.voice_settings.get("use_whisper", WHISPER_AVAILABLE))
        use_whisper_check = ttk.Checkbutton(
            advanced_frame,
            text="Use Whisper for better recognition",
            variable=self.use_whisper_var,
            state=tk.NORMAL if WHISPER_AVAILABLE else tk.DISABLED
        )
        use_whisper_check.pack(anchor=tk.W, pady=5)
        
        # Use gTTS checkbox - only if available
        self.use_gtts_var = tk.BooleanVar(value=self.voice_settings.get("use_gtts", GTTS_AVAILABLE))
        use_gtts_check = ttk.Checkbutton(
            advanced_frame,
            text="Use Google TTS for output (requires internet)",
            variable=self.use_gtts_var,
            state=tk.NORMAL if GTTS_AVAILABLE else tk.DISABLED
        )
        use_gtts_check.pack(anchor=tk.W, pady=5)
        
        # Fallback to gTTS checkbox
        self.fallback_gtts_var = tk.BooleanVar(value=self.voice_settings.get("fallback_to_gtts", True))
        fallback_gtts_check = ttk.Checkbutton(
            advanced_frame,
            text="Fallback to Google TTS if local TTS fails",
            variable=self.fallback_gtts_var,
            state=tk.NORMAL if GTTS_AVAILABLE else tk.DISABLED
# Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=self.voice_settings.get("auto_scroll", True))
        auto_scroll_check = ttk.Checkbutton(
            advanced_frame,
            text="Auto-scroll text areas",
            variable=self.auto_scroll_var
        )
        auto_scroll_check.pack(anchor=tk.W, pady=5)
        
        # Test voice button
        test_button = ModernButton(
            settings_window,
            text="Test Voice",
            command=lambda: self.test_voice_settings(
                self.voice_var.get(),
                self.rate_var.get(),
                self.volume_var.get(),
                self.pitch_var.get()
            )
        )
        test_button.pack(pady=10)

        # Save and Cancel buttons
        button_frame = tk.Frame(settings_window, bg="#ffffff")
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=20, pady=20)

        cancel_button = ModernButton(
            button_frame,
            text="Cancel",
            command=settings_window.destroy,
            bg="#95a5a6"
        )
        cancel_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        save_button = ModernButton(
            button_frame,
            text="Save Settings",
            command=lambda: self.save_voice_settings_from_dialog(settings_window)
        )
        save_button.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

    def save_voice_settings_from_dialog(self, settings_window):
        """Save voice settings from the dialog and close it"""
        try:
            self.voice_settings["voice_id"] = self.voice_var.get()
            self.voice_settings["rate"] = self.rate_var.get()
            self.voice_settings["volume"] = self.volume_var.get()
            self.voice_settings["pitch"] = self.pitch_var.get()
            self.voice_settings["use_whisper"] = self.use_whisper_var.get()
            self.voice_settings["use_gtts"] = self.use_gtts_var.get()
            self.voice_settings["fallback_to_gtts"] = self.fallback_gtts_var.get()
            self.voice_settings["auto_scroll"] = self.auto_scroll_var.get()
            
            # Apply settings immediately
            if self.engine:
                self.apply_voice_settings()
            
            # Save settings to file
            self.save_voice_settings()
            
            # Close dialog
            settings_window.destroy()
            
            # Update status
            self.update_status("Voice settings saved")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")

    def apply_voice_settings(self):
        """Apply voice settings to the TTS engine"""
        if not self.engine:
            return
            
        try:
            self.engine.setProperty('rate', self.voice_settings.get("rate", 150))
            self.engine.setProperty('volume', self.voice_settings.get("volume", 1.0))
            
            voice_id = self.voice_settings.get("voice_id")
            if voice_id:
                self.engine.setProperty('voice', voice_id)
                
        except Exception as e:
            print(f"Failed to apply voice settings: {str(e)}")

    def test_voice_settings(self, voice_id, rate, volume, pitch):
        """Test voice settings with a sample text"""
        if not self.engine:
            messagebox.showerror("Error", "TTS engine not available")
            return
            
        test_text = "This is a test of the voice settings. How does it sound?"
        
        try:
            # Create a temporary engine for testing to avoid changing current settings
            test_engine = pyttsx3.init()
            test_engine.setProperty('rate', rate)
            test_engine.setProperty('volume', volume)
            
            # Set voice if available
            if voice_id:
                test_engine.setProperty('voice', voice_id)
                
            # Queue text and start speaking
            test_engine.say(test_text)
            test_engine.runAndWait()
            
            # Clean up engine
            test_engine.stop()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to test voice: {str(e)}")
            
    def open_about_page(self):
        """Open about page with app information"""
        about_window = tk.Toplevel(self.win)
        about_window.title("About SpeakSwap")
        about_window.geometry("500x400")
        about_window.configure(bg="#ffffff")
        about_window.transient(self.win)
        about_window.grab_set()
        
        try:
            about_window.iconphoto(False, tk.PhotoImage(file="icon.png"))
        except:
            pass

        # App info
        info_frame = tk.Frame(about_window, bg="#ffffff")
        info_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        title_label = tk.Label(
            info_frame,
            text=APP_NAME,
            font=("Helvetica", 20, "bold"),
            bg="#ffffff",
            fg="#2c3e50"
        )
        title_label.pack(pady=(0, 10))

        version_label = tk.Label(
            info_frame,
            text=f"Version {APP_VERSION}",
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#7f8c8d"
        )
        version_label.pack(pady=(0, 20))

        desc_text = tk.Text(
            info_frame,
            wrap=tk.WORD,
            height=10,
            font=("Helvetica", 11),
            bg="#f8f9fa",
            fg="#2c3e50",
            padx=15,
            pady=15,
            relief=tk.FLAT
        )
        desc_text.insert(tk.END, (
            "SpeakSwap is an easy-to-use voice translation tool that "
            "enables real-time translation between multiple languages.\n\n"
            "Features:\n"
            "• Real-time speech recognition\n"
            "• Support for multiple languages\n"
            "• Customizable voice settings\n"
            "• Text-to-speech capabilities\n\n"
            "SpeakSwap uses several open-source technologies including "
            "Whisper, deep-translator, pyttsx3, and more."
        ))
        desc_text.config(state=tk.DISABLED)  # Make read-only
        desc_text.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

        # Close button
        close_button = ModernButton(
            info_frame,
            text="Close",
            command=about_window.destroy
        )
        close_button.pack()

    def clear_text(self):
        """Clear all text areas"""
        self.input_text.delete("1.0", tk.END)
        self.output_text.delete("1.0", tk.END)
        self.update_status("Text cleared")

    def update_status(self, message, is_error=False):
        """Update status bar message and color"""
        if not hasattr(self, 'status_label') or not self.status_label:
            return
            
        self.status_label.config(
            text=message,
            fg="#e74c3c" if is_error else "#7f8c8d"
        )
        self.win.update_idletasks()

    def run_translator(self):
        """Start the translation process"""
        if self.keep_running:
            messagebox.showinfo("Info", "Translation is already running")
            return
            
        # Check if languages are selected
        if not self.input_lang.get() or not self.output_lang.get():
            messagebox.showerror("Error", "Please select input and output languages")
            return
            
        # Check translator availability
        if not TRANSLATOR_AVAILABLE:
            messagebox.showerror("Error", "Translation library is not available. Please install deep-translator.")
            return
            
        # Start translation thread
        self.keep_running = True
        self.translation_thread = threading.Thread(target=self.translation_worker, daemon=True)
        self.translation_thread.start()
        
        # Update UI
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress_bar.start(10)
        self.update_status("Listening for speech...")

    def kill_execution(self):
        """Stop the translation process"""
        if not self.keep_running:
            return
            
        self.keep_running = False
        self.update_status("Stopping translation...")
        
        # Wait for thread to finish with timeout
        if self.translation_thread and self.translation_thread.is_alive():
            self.translation_thread.join(timeout=2.0)
            
        # Update UI
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress_bar.stop()
        self.update_status("Translation stopped")

    def translate_text_input(self):
        """Translate the text in the input field"""
        if not TRANSLATOR_AVAILABLE:
            messagebox.showerror("Error", "Translation library is not available. Please install deep-translator.")
            return
            
        input_text = self.input_text.get("1.0", tk.END).strip()
        if not input_text:
            messagebox.showinfo("Info", "No text to translate")
            return
            
        # Get language codes
        source_lang = self.language_codes[self.input_lang.get()]
        target_lang = self.language_codes[self.output_lang.get()]
        
        if source_lang == "auto" and not self.detect_language(input_text):
            messagebox.showerror("Error", "Cannot detect language. Please select a specific input language.")
            return
            
        # Start translation in a separate thread
        threading.Thread(
            target=self.process_text_translation,
            args=(input_text, source_lang, target_lang),
            daemon=True
        ).start()

    def process_text_translation(self, input_text, source_lang, target_lang):
        """Process text translation in a separate thread"""
        self.update_status("Translating text...")
        self.progress_bar.start(10)
        
        try:
            # Detect language if auto is selected
            if source_lang == "auto":
                detected_lang = self.detect_language(input_text)
                if detected_lang:
                    source_lang = detected_lang
                    self.update_status(f"Detected language: {detected_lang}")
                else:
                    # Fallback to English
                    source_lang = "en"
                    self.update_status("Could not detect language, using English as source")
            
            # Translate text
            translated_text = self.translate_text(input_text, source_lang, target_lang)
            
            if translated_text:
                # Update output text
                self.output_text.delete("1.0", tk.END)
                self.output_text.insert(tk.END, translated_text)
                
                # Auto-scroll to top
                if self.voice_settings.get("auto_scroll", True):
                    self.output_text.see("1.0")
                
                # Speak translated text if requested
                threading.Thread(
                    target=self.speak_text,
                    args=(translated_text, target_lang),
                    daemon=True
                ).start()
                
                self.update_status("Translation complete")
            else:
                self.update_status("Translation failed", is_error=True)
        except Exception as e:
            error_msg = f"Translation error: {str(e)}"
            print(error_msg)
            self.update_status(error_msg, is_error=True)
        finally:
            self.progress_bar.stop()

    def detect_language(self, text):
        """Detect language of the given text"""
        if not TRANSLATOR_AVAILABLE:
            return None
            
        try:
            from deep_translator import GoogleTranslator
            # Use the first few words for detection
            sample = " ".join(text.split()[:20])
            detected = GoogleTranslator().detect(sample)
            return detected
        except Exception as e:
            print(f"Language detection error: {str(e)}")
            return None

    def translate_text(self, text, source_lang, target_lang):
        """Translate text from source language to target language"""
        if not TRANSLATOR_AVAILABLE:
            return None
            
        try:
            from deep_translator import GoogleTranslator
            # Handle long texts by splitting into chunks
            chunk_size = 4000  # Google API limit is around 5000 chars
            chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]
            
            translated_chunks = []
            for chunk in chunks:
                # Replace source_lang with 'auto' if it equals 'auto'
                actual_source = 'auto' if source_lang == 'auto' else source_lang
                translator = GoogleTranslator(source=actual_source, target=target_lang)
                translated = translator.translate(chunk)
                translated_chunks.append(translated)
            
            return " ".join(translated_chunks)
        except Exception as e:
            print(f"Translation error: {str(e)}")
            # Try with fallback service if Google fails
            try:
                from deep_translator import MyMemoryTranslator
                translator = MyMemoryTranslator(source=source_lang, target=target_lang)
                return translator.translate(text[:9999])  # MyMemory has a 10k char limit
            except Exception as e2:
                print(f"Fallback translation error: {str(e2)}")
                return None

    def speak_text(self, text, language_code):
        """Speak the translated text in the target language"""
        if not text:
            return
            
        # Try using local TTS engine first
        if self.engine and not self.voice_settings.get("use_gtts", False):
            try:
                self.update_status("Speaking...")
                
                # Apply voice settings
                self.apply_voice_settings()
                
                # Queue text and start speaking
                self.engine.say(text)
                self.engine.runAndWait()
                
                self.update_status("Speaking complete")
                return
            except Exception as e:
                print(f"Local TTS error: {str(e)}")
                if not self.voice_settings.get("fallback_to_gtts", True):
                    self.update_status("Text-to-speech failed", is_error=True)
                    return
        
        # If local TTS failed or not available, try gTTS
        if GTTS_AVAILABLE and (self.voice_settings.get("use_gtts", False) or 
                               self.voice_settings.get("fallback_to_gtts", True)):
            try:
                self.update_status("Using Google TTS...")
                
                from gtts import gTTS
                tts = gTTS(text=text, lang=language_code)
                
                # Save to temporary file
                temp_file = os.path.join(TEMP_DIR, "speakswap_tts.mp3")
                tts.save(temp_file)
                
                # Play using playsound if available
                if PLAYSOUND_AVAILABLE:
                    playsound(temp_file)
                    self.update_status("Speaking complete")
                else:
                    self.update_status("Cannot play speech (playsound not installed)", is_error=True)
                
                # Clean up temp file
                try:
                    os.remove(temp_file)
                except:
                    pass
                    
            except Exception as e:
                print(f"Google TTS error: {str(e)}")
                self.update_status("Text-to-speech failed", is_error=True)

    def translation_worker(self):
        """Worker thread for continuous speech recognition and translation"""
        # Initialize recognizer
        recognizer = sr.Recognizer()
        
        # Get language codes
        source_lang = self.language_codes[self.input_lang.get()]
        target_lang = self.language_codes[self.output_lang.get()]
        
        # Setup audio stream
        audio_buffer = queue.Queue()
        stop_audio_event = threading.Event()
        audio_thread = threading.Thread(
            target=self.audio_stream_worker,
            args=(audio_buffer, stop_audio_event),
            daemon=True
        )
        audio_thread.start()
        
        while self.keep_running:
            try:
                # Check if we have audio data
                try:
                    audio_data = audio_buffer.get(timeout=1.0)
                except queue.Empty:
                    continue
                
                self.update_status("Recognizing speech...")
                
                # Use Whisper if available and enabled
                if self.whisper_pipe and self.voice_settings.get("use_whisper", False):
                    # Convert audio data to numpy array
                    temp_file = os.path.join(TEMP_DIR, "speech_input.wav")
                    with wave.open(temp_file, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(44100)
                        wf.writeframes(audio_data.get_wav_data())
                    
                    # Process with Whisper
                    result = self.whisper_pipe(temp_file)
                    recognized_text = result["text"]
                    
                    # Clean up temp file
                    try:
                        os.remove(temp_file)
                    except:
                        pass
                else:
                    # Fallback to standard recognizer
                    if source_lang == "auto":
                        # Let Google detect the language
                        recognized_text = recognizer.recognize_google(audio_data)
                    else:
                        # Use specified language
                        recognized_text = recognizer.recognize_google(audio_data, language=source_lang)
                
                if recognized_text:
                    # Update input text
                    current_text = self.input_text.get("1.0", tk.END).strip()
                    
                    self.input_text.delete("1.0", tk.END)
                    if current_text:
                        new_text = f"{current_text}\n{recognized_text}"
                    else:
                        new_text = recognized_text
                    
                    self.input_text.insert(tk.END, new_text)
                    
                    # Auto-scroll if enabled
                    if self.voice_settings.get("auto_scroll", True):
                        self.input_text.see(tk.END)
                    
                    # Translate the recognized text
                    self.update_status("Translating...")
                    translated_text = self.translate_text(recognized_text, source_lang, target_lang)
                    
                    if translated_text:
                        # Update output text
                        current_output = self.output_text.get("1.0", tk.END).strip()
                        
                        self.output_text.delete("1.0", tk.END)
                        if current_output:
                            new_output = f"{current_output}\n{translated_text}"
                        else:
                            new_output = translated_text
                        
                        self.output_text.insert(tk.END, new_output)
                        
                        # Auto-scroll if enabled
                        if self.voice_settings.get("auto_scroll", True):
                            self.output_text.see(tk.END)
                        
                        # Speak the translated text
                        self.speak_text(translated_text, target_lang)
                    else:
                        self.update_status("Translation failed", is_error=True)
                
                # Short pause between recognition attempts
                time.sleep(0.5)
                
            except sr.UnknownValueError:
                self.update_status("Speech not recognized, listening...")
            except sr.RequestError as e:
                error_msg = f"Recognition service error: {str(e)}"
                print(error_msg)
                self.update_status(error_msg, is_error=True)
                time.sleep(2)  # Pause before retry
            except Exception as e:
                error_msg = f"Error in translation worker: {str(e)}"
                print(error_msg)
                traceback.print_exc()
                self.update_status(error_msg, is_error=True)
                time.sleep(2)  # Pause before retry
        
        # Cleanup
        stop_audio_event.set()
        if audio_thread.is_alive():
            audio_thread.join(timeout=2.0)

    def audio_stream_worker(self, audio_queue, stop_event):
        """Worker thread for continuous audio streaming"""
        # Setup audio stream with error handling
        microphone = None
        audio_stream = None
        
        try:
            recognizer = sr.Recognizer()
            
            # Apply audio settings
            recognizer.dynamic_energy_threshold = True
            recognizer.energy_threshold = 300  # Adjust based on testing
            recognizer.pause_threshold = 0.8   # Shorter pause for more responsive recognition
            
            # Get default microphone
            microphone = sr.Microphone()
            
            with microphone as source:
                # Adjust for ambient noise
                recognizer.adjust_for_ambient_noise(source, duration=1)
                self.update_status("Microphone ready, listening...")
                
                # Monitor audio continuously
                while not stop_event.is_set():
                    try:
                        # Listen for audio with timeout
                        audio_data = recognizer.listen(source, timeout=10.0, phrase_time_limit=5.0)
                        audio_queue.put(audio_data)
                    except sr.WaitTimeoutError:
                        # No speech detected within timeout
                        continue
                    except Exception as e:
                        error_msg = f"Audio streaming error: {str(e)}"
                        print(error_msg)
                        self.update_status(error_msg, is_error=True)
                        time.sleep(1)  # Short pause before retry
            
        except Exception as e:
            error_msg = f"Failed to initialize audio stream: {str(e)}"
            print(error_msg)
            traceback.print_exc()
            self.update_status(error_msg, is_error=True)
        finally:
            # Clean up resources
            if audio_stream and hasattr(audio_stream, 'close'):
                audio_stream.close()

    def enhance_audio(self, audio_data):
        """Apply audio enhancement to improve speech recognition quality"""
        if not self.voice_settings.get("enhance_audio", True):
            return audio_data
            
        try:
            # Get audio as numpy array
            audio_array = np.frombuffer(audio_data, dtype=np.int16)
            
            # Apply simple noise reduction (high-pass filter)
            from scipy import signal
            b, a = signal.butter(4, 100/(44100/2), 'highpass')
            filtered_audio = signal.filtfilt(b, a, audio_array)
            
            # Normalize audio
            normalized_audio = filtered_audio * (32767 / max(abs(filtered_audio)))
            
            # Convert back to bytes
            enhanced_audio = normalized_audio.astype(np.int16).tobytes()
            return enhanced_audio
        except Exception as e:
            print(f"Audio enhancement error: {str(e)}")
            return audio_data  # Return original if enhancement fails

    def on_close(self):
        """Handle application cleanup and exit"""
        # Stop any running threads
        self.keep_running = False
        
        # Wait for threads to finish
        if self.translation_thread and self.translation_thread.is_alive():
            self.translation_thread.join(timeout=2.0)
        
        # Clean up TTS engine
        if self.engine:
            try:
                self.engine.stop()
            except:
                pass
        
        # Clean up Whisper model
        if self.whisper_model:
            try:
                # Force cleanup
                import gc
                self.whisper_model = None
                self.whisper_processor = None
                self.whisper_pipe = None
                gc.collect()
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
            except:
                pass
        
        # Delete any temporary files
        try:
            temp_files = [
                os.path.join(TEMP_DIR, "speakswap_tts.mp3"),
                os.path.join(TEMP_DIR, "speech_input.wav")
            ]
            for file in temp_files:
                if os.path.exists(file):
                    os.remove(file)
        except:
            pass
        
        # Close the window
        self.win.destroy()

    def run(self):
        """Start the application main loop"""
        if self.win:
            self.win.mainloop()

def main():
    """Main entry point for the application"""
    try:
        app = SpeakSwapApp()
        app.run()
    except Exception as e:
        print(f"Application error: {str(e)}")
        traceback.print_exc()
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")

if __name__ == "__main__":
    main()