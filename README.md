<div align="center">
<h1>SpeakSwap: Real-Time Voice Translator 🎙️</h1>
<a href="#"><img alt="language" src="https://user-images.githubusercontent.com/132539454/278971782-9453805e-e2e6-4d99-b1de-cf8fcd3e7105.svg"></a>
</div>

A modern, real-time voice translation application that converts speech from one language to another while preserving the speaker's tone and emotion.

## Features ✨

- Real-time voice translation
- Support for multiple languages
- Modern, intuitive interface
- High-quality voice synthesis
- Advanced audio processing
- Whisper-based speech recognition
- Customizable voice settings
- Keyboard shortcuts
- Progress indicators
- Auto-scrolling text
- Error handling and feedback

## Supported Languages 🌍

- English
- Hindi
- Bengali
- Spanish
- Chinese (Simplified)
- Russian
- Japanese
- Korean
- German
- French
- Tamil
- Telugu
- Kannada
- Gujarati
- Punjabi
- Malayalam

## Prerequisites 📋

- Python 3.8 or higher
- Windows 10/11
- Microphone
- Speakers/Headphones
- Internet connection

## Installation 🚀

1. Clone the repository:
```bash
git clone https://github.com/sajadmaker/speakswap.git
cd speakswap
```

2. Create a virtual environment (recommended):
```bash
# Create virtualenv
python -m venv env
# Windows
env\Scripts\activate
```

3. Install dependencies:
```bash
pip install --upgrade wheel
pip install -r requirements.txt
```

## Usage 💡

1. Run the application:
```bash
python main.py
```

2. Select input and output languages from the dropdown menus
3. Click "Start Translation" or press Ctrl+S to begin
4. Speak into your microphone
5. The application will:
   - Convert your speech to text
   - Translate the text
   - Read the translation aloud
6. Click "Stop" or press Ctrl+X to end the session

### Keyboard Shortcuts ⌨️

- `Ctrl+S`: Start translation
- `Ctrl+X`: Stop translation
- `Ctrl+A`: Open about page
- `Ctrl+L`: Clear text
- `Ctrl+,`: Open settings

## Voice Settings ⚙️

Access voice settings by clicking the settings button (⚙️) or pressing Ctrl+,

- Speech Rate: Adjust the speed of voice output
- Volume: Control the output volume
- Pitch: Modify the voice pitch
- Voice Selection: Choose from available system voices
- Advanced Settings:
  - Use Whisper for better recognition
  - Enhance audio quality
  - Auto-scroll text

## Building Executable 🏗️

This project uses [cx_Freeze](https://github.com/marcelotduarte/cx_Freeze/tree/main) to build executable files. The build settings can be changed by modifying the [setup.py](setup.py) file.

### Build installer containing all the files:
```bash
# Windows
python setup.py bdist_msi
# Linux
python setup.py bdist_rpm
# Mac
python setup.py bdist_mac
```

The executable will be created in the `build` directory.

## Troubleshooting 🔧

1. **Microphone not working:**
   - Check system microphone settings
   - Ensure microphone is selected in the application
   - Test microphone in system settings

2. **No sound output:**
   - Verify system audio settings
   - Check if speakers/headphones are connected
   - Test system audio

3. **Translation issues:**
   - Check internet connection
   - Verify language selection
   - Ensure clear speech input

## Contributing 🤝

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits 👏

Developed by The Minions Team(sajad,harikrishnan,adwait & jishnnu)

## Support 💬

For support, please open an issue in the GitHub repository or contact the development team.

---

<div align="center">
Made with ❤️ by <a href="https://github.com/sajadmaker">Sajad Maker</a>
</div>
