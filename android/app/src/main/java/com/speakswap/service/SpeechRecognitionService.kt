package com.speakswap.service

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import java.util.*

class SpeechRecognitionService(private val context: Context) {
    
    private val speechRecognizer: SpeechRecognizer = SpeechRecognizer.createSpeechRecognizer(context)
    
    private val _recognitionState = MutableStateFlow<RecognitionState>(RecognitionState.Idle)
    val recognitionState: StateFlow<RecognitionState> = _recognitionState.asStateFlow()
    
    init {
        speechRecognizer.setRecognitionListener(object : RecognitionListener {
            override fun onReadyForSpeech(params: Bundle?) {
                _recognitionState.value = RecognitionState.Ready
            }
            
            override fun onBeginningOfSpeech() {
                _recognitionState.value = RecognitionState.Speaking
            }
            
            override fun onRmsChanged(rmsdB: Float) {
                // Handle volume level changes if needed
            }
            
            override fun onBufferReceived(buffer: ByteArray?) {
                // Handle buffer if needed
            }
            
            override fun onEndOfSpeech() {
                _recognitionState.value = RecognitionState.Processing
            }
            
            override fun onResults(results: Bundle?) {
                val matches = results?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    _recognitionState.value = RecognitionState.Result(matches[0])
                } else {
                    _recognitionState.value = RecognitionState.Error("No results found")
                }
            }
            
            override fun onError(error: Int) {
                val errorMessage = when (error) {
                    SpeechRecognizer.ERROR_AUDIO -> "Audio recording error"
                    SpeechRecognizer.ERROR_CLIENT -> "Client side error"
                    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> "Insufficient permissions"
                    SpeechRecognizer.ERROR_NETWORK -> "Network error"
                    SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> "Network timeout"
                    SpeechRecognizer.ERROR_NO_MATCH -> "No recognition match"
                    SpeechRecognizer.ERROR_RECOGNIZER_BUSY -> "Recognition service busy"
                    SpeechRecognizer.ERROR_SERVER -> "Server error"
                    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> "No speech input"
                    else -> "Unknown error occurred"
                }
                _recognitionState.value = RecognitionState.Error(errorMessage)
            }
            
            override fun onPartialResults(partialResults: Bundle?) {
                val matches = partialResults?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
                if (!matches.isNullOrEmpty()) {
                    _recognitionState.value = RecognitionState.PartialResult(matches[0])
                }
            }
            
            override fun onEvent(eventType: Int, params: Bundle?) {
                // Handle events if needed
            }
        })
    }
    
    fun startListening(language: String) {
        val intent = Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM)
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, language)
            putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1)
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }
        speechRecognizer.startListening(intent)
    }
    
    fun stopListening() {
        speechRecognizer.stopListening()
    }
    
    fun destroy() {
        speechRecognizer.destroy()
    }
}

sealed class RecognitionState {
    object Idle : RecognitionState()
    object Ready : RecognitionState()
    object Speaking : RecognitionState()
    object Processing : RecognitionState()
    data class Result(val text: String) : RecognitionState()
    data class PartialResult(val text: String) : RecognitionState()
    data class Error(val message: String) : RecognitionState()
} 