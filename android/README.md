# SpeakSwap Android

A mobile port of the SpeakSwap speech-to-speech translation application.

## Features

- Real-time speech recognition using Android's Speech Recognition API
- Text translation using Google's ML Kit Translation API
- Text-to-speech output using Android's TextToSpeech
- Support for multiple languages
- Modern Material 3 design with Jetpack Compose
- Dark/Light theme support
- Proper handling of Android permissions
- Offline translation support

## Requirements

- Android Studio Arctic Fox (2021.3.1) or newer
- Android SDK 24 or higher
- JDK 17

## Setup

1. Clone the repository
2. Open the `android` folder in Android Studio
3. Sync Gradle files
4. Run the app on an emulator or physical device

## Architecture

The app follows the MVVM (Model-View-ViewModel) architecture and is built with:

- **Jetpack Compose** for the UI
- **ML Kit** for translation
- **Room** for database operations
- **Kotlin Coroutines & Flow** for asynchronous operations
- **Android Speech Recognition API** for speech input
- **Android TextToSpeech** for speech output

## How to Use

1. Select source and target languages from the dropdowns
2. Tap the "Speak" button to start speech recognition
3. Speak clearly into your device microphone
4. View the translated text
5. Tap the "Listen" button to hear the translation spoken

## Credits

Based on the original SpeakSwap desktop application. 