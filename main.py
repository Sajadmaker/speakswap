import os
import threading
import tkinter as tk
from gtts import gTTS
from tkinter import ttk, messagebox
import speech_recognition as sr
from playsound import playsound
from deep_translator import GoogleTranslator
from google.transliteration import transliterate_text
import queue
import time
import pyttsx3
import sounddevice as sd
import numpy as np
from scipy.io import wavfile
import json
from dotenv import load_dotenv
import wave
import io
import torch
from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
import torchaudio
import torchaudio.transforms as T
from PIL import Image, ImageTk
import requests
from io import BytesIO

# Load environment variables
load_dotenv()

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
        self.win = tk.Tk()
        self.win.geometry("1200x900")
        self.win.title("SpeakSwap 🎙️ - Modern Voice Translator")
        self.win.configure(bg="#ffffff")
        
        # Set icon
        try:
            icon = tk.PhotoImage(file="icon.png")
            self.win.iconphoto(False, icon)
        except:
            pass

        # Initialize variables
        self.keep_running = False
        self.translation_queue = queue.Queue()
        self.engine = pyttsx3.init()
        self.voice_settings = self.load_voice_settings()
        self.setup_ui()
        self.setup_keyboard_shortcuts()
        
        # Initialize Whisper model for better speech recognition
        self.setup_whisper_model()
        
    def setup_whisper_model(self):
        try:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model_id = "openai/whisper-large-v3"
            self.whisper_model = AutoModelForSpeechSeq2Seq.from_pretrained(
                model_id, torch_dtype=torch.float16, low_cpu_mem_usage=True
            ).to(device)
            self.whisper_processor = AutoProcessor.from_pretrained(model_id)
            self.whisper_pipe = pipeline(
                "automatic-speech-recognition",
                model=self.whisper_model,
                tokenizer=self.whisper_processor.tokenizer,
                feature_extractor=self.whisper_processor.feature_extractor,
                max_new_tokens=128
            )
        except Exception as e:
            print(f"Failed to initialize Whisper model: {str(e)}")
            self.whisper_pipe = None

    def load_voice_settings(self):
        try:
            with open('voice_settings.json', 'r') as f:
                return json.load(f)
        except:
            return {
                "rate": 150,
                "volume": 1.0,
                "pitch": 1.0,
                "voice_id": None,
                "use_whisper": True,
                "enhance_audio": True,
                "auto_scroll": True
            }

    def save_voice_settings(self):
        with open('voice_settings.json', 'w') as f:
            json.dump(self.voice_settings, f)

    def setup_ui(self):
        # Main container with padding
        self.main_container = tk.Frame(self.win, bg="#ffffff", padx=30, pady=20)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Header section with gradient effect
        self.header_frame = tk.Frame(self.main_container, bg="#ffffff")
        self.header_frame.pack(fill=tk.X, pady=(0, 20))

        # Logo and title
        try:
            logo_image = Image.open("icon.png")
            logo_image = logo_image.resize((40, 40))
            logo_photo = ImageTk.PhotoImage(logo_image)
            logo_label = tk.Label(
                self.header_frame,
                image=logo_photo,
                bg="#ffffff"
            )
            logo_label.image = logo_photo
            logo_label.pack(side=tk.LEFT, padx=(0, 10))
        except:
            pass

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
            text="Real-time Voice Translator",
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

        # Language selection frame with modern styling
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
        self.input_lang.set("English")
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

        # Text areas frame with scrollbars
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

        # Control buttons frame
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

        # About button
        self.about_button = ModernButton(
            self.button_frame,
            text="ℹ️ About",
            command=self.open_about_page,
            bg="#95a5a6"
        )
        self.about_button.pack(side=tk.LEFT, padx=10)

        # Status bar with progress
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

        # Initialize button states
        self.stop_button.config(state=tk.DISABLED)

    def animate_arrow(self):
        colors = ["#3498db", "#2980b9", "#3498db"]
        current_color = self.arrow_label.cget("fg")
        next_color = colors[(colors.index(current_color) + 1) % len(colors)]
        self.arrow_label.config(fg=next_color)
        self.win.after(1000, self.animate_arrow)

    def setup_keyboard_shortcuts(self):
        self.win.bind('<Control-s>', lambda e: self.run_translator())
        self.win.bind('<Control-x>', lambda e: self.kill_execution())
        self.win.bind('<Control-a>', lambda e: self.open_about_page())
        self.win.bind('<Control-l>', lambda e: self.clear_text())
        self.win.bind('<Control-,>', lambda e: self.open_settings())

    def open_settings(self):
        settings_window = tk.Toplevel(self.win)
        settings_window.title("Voice Settings")
        settings_window.geometry("400x600")
        settings_window.configure(bg="#ffffff")
        
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

        voices = self.engine.getProperty('voices')
        self.voice_var = tk.StringVar(value=self.voice_settings.get("voice_id", voices[0].id if voices else ""))
        
        voice_combo = ttk.Combobox(
            voice_frame,
            textvariable=self.voice_var,
            values=[voice.id for voice in voices],
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

        # Use Whisper checkbox
        self.use_whisper_var = tk.BooleanVar(value=self.voice_settings.get("use_whisper", True))
        use_whisper_check = ttk.Checkbutton(
            advanced_frame,
            text="Use Whisper for better recognition",
            variable=self.use_whisper_var
        )
        use_whisper_check.pack(anchor=tk.W, pady=5)

        # Enhance audio checkbox
        self.enhance_audio_var = tk.BooleanVar(value=self.voice_settings.get("enhance_audio", True))
        enhance_audio_check = ttk.Checkbutton(
            advanced_frame,
            text="Enhance audio quality",
            variable=self.enhance_audio_var
        )
        enhance_audio_check.pack(anchor=tk.W, pady=5)

        # Auto-scroll checkbox
        self.auto_scroll_var = tk.BooleanVar(value=self.voice_settings.get("auto_scroll", True))
        auto_scroll_check = ttk.Checkbutton(
            advanced_frame,
            text="Auto-scroll text",
            variable=self.auto_scroll_var
        )
        auto_scroll_check.pack(anchor=tk.W, pady=5)

        # Test button
        test_button = ModernButton(
            settings_window,
            text="Test Voice",
            command=lambda: self.test_voice(
                self.voice_var.get(),
                self.rate_var.get(),
                self.volume_var.get(),
                self.pitch_var.get()
            )
        )
        test_button.pack(pady=20)

        # Save button
        save_button = ModernButton(
            settings_window,
            text="Save Settings",
            command=lambda: self.save_voice_settings_and_close(settings_window)
        )
        save_button.pack(pady=10)

    def test_voice(self, voice_id, rate, volume, pitch):
        try:
            self.engine.setProperty('voice', voice_id)
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            self.engine.setProperty('pitch', pitch)
            self.engine.say("This is a test of the voice settings.")
            self.engine.runAndWait()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to test voice: {str(e)}")

    def save_voice_settings_and_close(self, window):
        self.voice_settings = {
            "voice_id": self.voice_var.get(),
            "rate": self.rate_var.get(),
            "volume": self.volume_var.get(),
            "pitch": self.pitch_var.get(),
            "use_whisper": self.use_whisper_var.get(),
            "enhance_audio": self.enhance_audio_var.get(),
            "auto_scroll": self.auto_scroll_var.get()
        }
        self.save_voice_settings()
        window.destroy()

    def clear_text(self):
        self.input_text.delete(1.0, tk.END)
        self.output_text.delete(1.0, tk.END)
        self.update_status("Text cleared")

    @property
    def language_codes(self):
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
            "Malayalam": "ml"
        }

    def update_status(self, message, is_error=False):
        self.status_label.config(
            text=message,
            fg="#e74c3c" if is_error else "#7f8c8d"
        )

    def show_progress(self, show=True):
        if show:
            self.progress_bar.start(10)
        else:
            self.progress_bar.stop()

    def process_audio(self, audio_data, sample_rate):
        if not self.voice_settings.get("enhance_audio", True):
            return audio_data

        # Apply audio processing for better quality
        audio_data = audio_data.astype(np.float32)
        
        # Normalize audio
        audio_data = audio_data / np.max(np.abs(audio_data))
        
        # Apply a simple low-pass filter
        from scipy.signal import butter, filtfilt
        nyquist = sample_rate / 2
        cutoff = 4000
        b, a = butter(4, cutoff/nyquist, btype='low')
        audio_data = filtfilt(b, a, audio_data)
        
        # Apply noise reduction
        noise_reduction = T.NoiseReduction()
        audio_tensor = torch.from_numpy(audio_data).unsqueeze(0)
        audio_tensor = noise_reduction(audio_tensor)
        audio_data = audio_tensor.squeeze(0).numpy()
        
        return audio_data

    def update_translation(self):
        if not self.keep_running:
            return

        try:
            r = sr.Recognizer()
            with sr.Microphone() as source:
                self.update_status("Listening...")
                self.show_progress(True)
                
                # Adjust for ambient noise
                r.adjust_for_ambient_noise(source, duration=0.5)
                
                # Set dynamic energy threshold
                r.dynamic_energy_threshold = True
                r.energy_threshold = 4000
                
                audio = r.listen(source, timeout=5, phrase_time_limit=10)
                
                try:
                    # Use Whisper for better recognition if enabled
                    if self.voice_settings.get("use_whisper", True) and self.whisper_pipe:
                        audio_data = np.frombuffer(audio.get_raw_data(), dtype=np.int16)
                        audio_data = self.process_audio(audio_data, audio.sample_rate)
                        result = self.whisper_pipe({"array": audio_data, "sampling_rate": audio.sample_rate})
                        speech_text = result["text"]
                    else:
                        speech_text = r.recognize_google(audio)

                    input_lang_code = self.language_codes.get(self.input_lang.get(), "auto")
                    output_lang_code = self.language_codes.get(self.output_lang.get(), "en")
                    
                    speech_text_transliteration = transliterate_text(
                        speech_text,
                        lang_code=input_lang_code
                    ) if input_lang_code not in ('auto', 'en') else speech_text
                    
                    self.input_text.insert(tk.END, f"{speech_text_transliteration}\n")
                    if self.voice_settings.get("auto_scroll", True):
                        self.input_text.see(tk.END)
                    
                    if speech_text.lower() in {'exit', 'stop'}:
                        self.keep_running = False
                        return
                    
                    self.update_status("Translating...")
                    translated_text = GoogleTranslator(
                        source=input_lang_code,
                        target=output_lang_code
                    ).translate(text=speech_text_transliteration)

                    self.output_text.insert(tk.END, translated_text + "\n")
                    if self.voice_settings.get("auto_scroll", True):
                        self.output_text.see(tk.END)
                    
                    self.update_status("Generating audio...")
                    
                    # Use pyttsx3 for better voice quality
                    self.engine.setProperty('voice', self.voice_settings["voice_id"])
                    self.engine.setProperty('rate', self.voice_settings["rate"])
                    self.engine.setProperty('volume', self.voice_settings["volume"])
                    self.engine.setProperty('pitch', self.voice_settings["pitch"])
                    
                    # Generate audio with pyttsx3
                    self.engine.say(translated_text)
                    self.engine.runAndWait()
                    
                    self.update_status("Ready")
                    self.show_progress(False)
                    
                except sr.UnknownValueError:
                    self.update_status("Could not understand audio", True)
                    self.show_progress(False)
                except sr.RequestError:
                    self.update_status("Could not request from Google", True)
                    self.show_progress(False)
                except Exception as e:
                    self.update_status(f"Error: {str(e)}", True)
                    self.show_progress(False)

        except Exception as e:
            self.update_status(f"Error: {str(e)}", True)
            self.show_progress(False)

        if self.keep_running:
            self.win.after(100, self.update_translation)

    def run_translator(self):
        if not self.keep_running:
            self.keep_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.update_status("Starting translation...")
            threading.Thread(target=self.update_translation, daemon=True).start()

    def kill_execution(self):
        self.keep_running = False
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.update_status("Stopped")
        self.show_progress(False)

    def open_about_page(self):
        about_window = tk.Toplevel(self.win)
        about_window.title("About SpeakSwap")
        about_window.geometry("500x400")
        about_window.configure(bg="#ffffff")
        
        try:
            about_window.iconphoto(False, tk.PhotoImage(file="icon.png"))
        except:
            pass

        # Title
        title_label = tk.Label(
            about_window,
            text="SpeakSwap",
            font=("Helvetica", 24, "bold"),
            bg="#ffffff",
            fg="#2c3e50"
        )
        title_label.pack(pady=(20, 10))
        
        # Subtitle
        subtitle_label = tk.Label(
            about_window,
            text="Modern Voice Translator",
            font=("Helvetica", 14),
            bg="#ffffff",
            fg="#7f8c8d"
        )
        subtitle_label.pack(pady=(0, 20))

        # About text
        about_text = tk.Text(
            about_window,
            height=10,
            width=50,
            font=("Helvetica", 11),
            bg="#f8f9fa",
            fg="#2c3e50",
            padx=15,
            pady=15,
            relief=tk.FLAT
        )
        about_text.insert("1.0", """
        A modern voice translation application that converts speech from one 
        language to another in real-time while preserving the speaker's tone 
        and emotion.

        Features:
        • Real-time voice translation
        • Support for multiple languages
        • Modern, intuitive interface
        • Keyboard shortcuts
        • Progress indicators
        • Error handling and feedback
        • Customizable voice settings
        • High-quality audio processing
        • Automatic noise adjustment
        • Dynamic energy threshold
        • Whisper-based speech recognition
        • Advanced audio enhancement
        • Auto-scrolling text
        • Voice customization
        """)
        about_text.config(state=tk.DISABLED)
        about_text.pack(pady=10)

        # Developer info
        dev_label = tk.Label(
            about_window,
            text="Developed by The Minions Team",
            font=("Helvetica", 12),
            bg="#ffffff",
            fg="#7f8c8d"
        )
        dev_label.pack(pady=(20, 5))

        # Close button
        close_button = ModernButton(
            about_window,
            text="Close",
            command=about_window.destroy
        )
        close_button.pack(pady=20)

    def run(self):
        self.win.mainloop()

if __name__ == "__main__":
    app = SpeakSwapApp()
    app.run()