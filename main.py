import os
import threading
import tkinter as tk
from gtts import gTTS
from tkinter import ttk
import speech_recognition as sr
from playsound import playsound
from deep_translator import GoogleTranslator
from google.transliteration import transliterate_text


# Create an instance of Tkinter frame or window
win = tk.Tk()

# Set the geometry of tkinter frame
win.geometry("800x600")
win.title("SpeakSwap 🎙️ - Modern Voice Translator")
icon = tk.PhotoImage(file="icon.png")
win.iconphoto(False, icon)

# Configure the style for a more modern look
style = ttk.Style()
style.theme_use('clam')  # Using clam theme as base
style.configure("TButton", padding=10, relief="flat", background="#4a86e8", foreground="white")
style.configure("TLabel", font=("Helvetica", 12))
style.configure("TCombobox", padding=6)

# Setting background color
win.configure(bg="#f0f0f0")

# Create a frame for the main content
main_frame = tk.Frame(win, bg="#f0f0f0", padx=20, pady=20)
main_frame.pack(fill=tk.BOTH, expand=True)

# Title label with modern styling
title_label = tk.Label(main_frame, text="SpeakSwap", font=("Helvetica", 24, "bold"), bg="#f0f0f0", fg="#4a86e8")
title_label.pack(pady=(0, 20))

# Create labels and text boxes for the recognized and translated text
input_frame = tk.Frame(main_frame, bg="#f0f0f0")
input_frame.pack(fill=tk.X, pady=10)

input_label = tk.Label(input_frame, text="Recognized Text", font=("Helvetica", 12, "bold"), bg="#f0f0f0")
input_label.pack(anchor=tk.W)

input_text = tk.Text(input_frame, height=5, width=60, font=("Helvetica", 11), 
                     bd=2, relief=tk.GROOVE, padx=10, pady=10)
input_text.pack(fill=tk.X)

output_frame = tk.Frame(main_frame, bg="#f0f0f0")
output_frame.pack(fill=tk.X, pady=10)

output_label = tk.Label(output_frame, text="Translated Text", font=("Helvetica", 12, "bold"), bg="#f0f0f0")
output_label.pack(anchor=tk.W)

output_text = tk.Text(output_frame, height=5, width=60, font=("Helvetica", 11), 
                      bd=2, relief=tk.GROOVE, padx=10, pady=10)
output_text.pack(fill=tk.X)

# Create a dictionary of language names and codes
language_codes = {
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
    "Malayalam": "ml"  # Added Malayalam language
}

language_names = list(language_codes.keys())

# Create a frame for language selection
lang_frame = tk.Frame(main_frame, bg="#f0f0f0")
lang_frame.pack(fill=tk.X, pady=10)

# Create left and right frames for input and output language selection
input_lang_frame = tk.Frame(lang_frame, bg="#f0f0f0")
input_lang_frame.pack(side=tk.LEFT, padx=(0, 10))

output_lang_frame = tk.Frame(lang_frame, bg="#f0f0f0")
output_lang_frame.pack(side=tk.RIGHT, padx=(10, 0))

# Input language dropdown
input_lang_label = tk.Label(input_lang_frame, text="Input Language:", font=("Helvetica", 11), bg="#f0f0f0")
input_lang_label.pack(anchor=tk.W)

input_lang = ttk.Combobox(input_lang_frame, values=language_names, width=20)
def update_input_lang_code(event):
    selected_language_name = event.widget.get()
    selected_language_code = language_codes[selected_language_name]
    # Update the selected language code
    input_lang.set(selected_language_name)
input_lang.bind("<<ComboboxSelected>>", lambda e: update_input_lang_code(e))
if input_lang.get() == "": input_lang.set("English")  # Default to English
input_lang.pack(pady=5)

# Arrow label
arrow_label = tk.Label(lang_frame, text="→", font=("Helvetica", 20), bg="#f0f0f0")
arrow_label.place(relx=0.5, rely=0.5, anchor="center")

# Output language dropdown
output_lang_label = tk.Label(output_lang_frame, text="Output Language:", font=("Helvetica", 11), bg="#f0f0f0")
output_lang_label.pack(anchor=tk.W)

output_lang = ttk.Combobox(output_lang_frame, values=language_names, width=20)
def update_output_lang_code(event):
    selected_language_name = event.widget.get()
    selected_language_code = language_codes[selected_language_name]
    # Update the selected language code
    output_lang.set(selected_language_name)
output_lang.bind("<<ComboboxSelected>>", lambda e: update_output_lang_code(e))
if output_lang.get() == "": output_lang.set("English")  # Default to English
output_lang.pack(pady=5)

# Create a frame for buttons
button_frame = tk.Frame(main_frame, bg="#f0f0f0")
button_frame.pack(fill=tk.X, pady=20)

keep_running = False

def update_translation():
    global keep_running

    if keep_running:
        r = sr.Recognizer()

        with sr.Microphone() as source:
            print("Speak Now!\n")
            audio = r.listen(source)
            
            try:
                speech_text = r.recognize_google(audio)
                
                # Get the actual language code for translation
                input_lang_code = language_codes.get(input_lang.get(), "auto")
                output_lang_code = language_codes.get(output_lang.get(), "en")
                
                speech_text_transliteration = transliterate_text(speech_text, lang_code=input_lang_code) if input_lang_code not in ('auto', 'en') else speech_text
                input_text.insert(tk.END, f"{speech_text_transliteration}\n")
                if speech_text.lower() in {'exit', 'stop'}:
                    keep_running = False
                    return
                
                translated_text = GoogleTranslator(source=input_lang_code, target=output_lang_code).translate(text=speech_text_transliteration)

                voice = gTTS(translated_text, lang=output_lang_code)
                voice.save('voice.mp3')
                playsound('voice.mp3')
                os.remove('voice.mp3')

                output_text.insert(tk.END, translated_text + "\n")
                
            except sr.UnknownValueError:
                output_text.insert(tk.END, "Could not understand!\n")
            except sr.RequestError:
                output_text.insert(tk.END, "Could not request from Google!\n")

    win.after(100, update_translation)

def run_translator():
    global keep_running
    
    if not keep_running:
        keep_running = True
        update_translation_thread = threading.Thread(target=update_translation)        # using multi threading for efficient cpu usage
        update_translation_thread.start()

def kill_execution():
    global keep_running
    keep_running = False

def open_about_page():      # about page
    about_window = tk.Toplevel()
    about_window.title("About SpeakSwap")
    about_window.geometry("500x400")
    about_window.iconphoto(False, icon)
    about_window.configure(bg="#f0f0f0")

    # Title
    title_label = tk.Label(about_window, text="SpeakSwap", font=("Helvetica", 20, "bold"), bg="#f0f0f0", fg="#4a86e8")
    title_label.pack(pady=(20, 10))
    
    # Subtitle
    subtitle_label = tk.Label(about_window, text="Modern Voice Translator", font=("Helvetica", 14), bg="#f0f0f0")
    subtitle_label.pack(pady=(0, 20))

    # Create a text widget to display the about text
    about_text = tk.Text(about_window, height=10, width=50, font=("Helvetica", 11), 
                         bd=2, relief=tk.GROOVE, padx=10, pady=10)
    about_text.insert("1.0", """
    A machine learning project that translates voice from one language 
    to another in real time while preserving the tone and emotion of 
    the speaker, and outputs the result in MP3 format.
    
    Choose input and output languages from the dropdown menu and 
    start the translation!
    """)
    about_text.config(state=tk.DISABLED)
    about_text.pack(pady=10)

    # Developer info
    dev_label = tk.Label(about_window, text="Developed by:", font=("Helvetica", 12, "bold"), bg="#f0f0f0")
    dev_label.pack(pady=(20, 5))
    
    dev_names = tk.Label(about_window, text="The Minions Team", font=("Helvetica", 11), bg="#f0f0f0")
    dev_names.pack()

    # Create a "Close" button
    close_button = tk.Button(about_window, text="Close", command=about_window.destroy,
                            font=("Helvetica", 11), bg="#4a86e8", fg="white", 
                            padx=20, pady=5, relief=tk.FLAT)
    close_button.pack(pady=20)

def open_webpage(url):      # Opens a web page in the user's default web browser.
    import webbrowser
    webbrowser.open(url)

# Create the styled buttons
run_button = tk.Button(button_frame, text="Start Translation", command=run_translator,
                      font=("Helvetica", 12), bg="#4a86e8", fg="white", 
                      padx=15, pady=8, relief=tk.FLAT)
run_button.pack(side=tk.LEFT, padx=(0, 10))

kill_button = tk.Button(button_frame, text="Stop", command=kill_execution,
                       font=("Helvetica", 12), bg="#e84a5f", fg="white", 
                       padx=15, pady=8, relief=tk.FLAT)
kill_button.pack(side=tk.LEFT, padx=10)

about_button = tk.Button(button_frame, text="About SpeakSwap", command=open_about_page,
                        font=("Helvetica", 12), bg="#5a5a5a", fg="white", 
                        padx=15, pady=8, relief=tk.FLAT)
about_button.pack(side=tk.LEFT, padx=10)

# Status bar
status_frame = tk.Frame(win, bg="#dcdcdc", height=30)
status_frame.pack(side=tk.BOTTOM, fill=tk.X)

status_label = tk.Label(status_frame, text="Ready", font=("Helvetica", 9), bg="#dcdcdc", fg="#5a5a5a")
status_label.pack(side=tk.LEFT, padx=10)

# Version label
version_label = tk.Label(status_frame, text="v1.0", font=("Helvetica", 9), bg="#dcdcdc", fg="#5a5a5a")
version_label.pack(side=tk.RIGHT, padx=10)

# Run the Tkinter event loop
win.mainloop()