package com.minions.speakswap.service

import android.content.Context
import android.speech.tts.TextToSpeech
import android.speech.tts.UtteranceProgressListener
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.*

class TextToSpeechService(private val context: Context) {
    
    private var textToSpeech: TextToSpeech? = null
    private var isInitialized = false
    
    private val _ttsState = MutableStateFlow<TTSState>(TTSState.Idle)
    val ttsState: StateFlow<TTSState> = _ttsState.asStateFlow()
    
    init {
        textToSpeech = TextToSpeech(context) { status ->
            if (status == TextToSpeech.SUCCESS) {
                isInitialized = true
                _ttsState.value = TTSState.Ready
            } else {
                _ttsState.value = TTSState.Error("Failed to initialize TTS")
            }
        }
        
        textToSpeech?.setOnUtteranceProgressListener(object : UtteranceProgressListener() {
            override fun onStart(utteranceId: String?) {
                _ttsState.value = TTSState.Speaking
            }
            
            override fun onDone(utteranceId: String?) {
                _ttsState.value = TTSState.Ready
            }
            
            override fun onError(utteranceId: String?) {
                _ttsState.value = TTSState.Error("TTS error occurred")
            }
            
            override fun onError(utteranceId: String?, errorCode: Int) {
                _ttsState.value = TTSState.Error("TTS error: $errorCode")
            }
        })
    }
    
    fun speak(text: String, language: String) {
        if (!isInitialized) {
            _ttsState.value = TTSState.Error("TTS not initialized")
            return
        }
        
        val result = textToSpeech?.setLanguage(Locale(language))
        if (result == TextToSpeech.LANG_MISSING_DATA || result == TextToSpeech.LANG_NOT_SUPPORTED) {
            _ttsState.value = TTSState.Error("Language not supported")
            return
        }
        
        textToSpeech?.speak(text, TextToSpeech.QUEUE_FLUSH, null, "utteranceId")
    }
    
    fun stop() {
        textToSpeech?.stop()
        _ttsState.value = TTSState.Ready
    }
    
    fun shutdown() {
        textToSpeech?.stop()
        textToSpeech?.shutdown()
        textToSpeech = null
        isInitialized = false
        _ttsState.value = TTSState.Idle
    }
}

sealed class TTSState {
    object Idle : TTSState()
    object Ready : TTSState()
    object Speaking : TTSState()
    data class Error(val message: String) : TTSState()
} 