package com.speakswap

import android.app.Application
import android.content.Context
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.google.mlkit.nl.translate.Translation
import com.google.mlkit.nl.translate.TranslatorOptions
import com.speakswap.service.RecognitionState
import com.speakswap.service.SpeechRecognitionService
import com.speakswap.service.TextToSpeechService
import com.speakswap.service.TTSState
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch

class MainViewModel(application: Application) : AndroidViewModel(application) {
    
    private val repository = (application as SpeakSwapApplication).repository
    private val speechRecognitionService = SpeechRecognitionService(application)
    private val textToSpeechService = TextToSpeechService(application)
    
    private val _uiState = MutableStateFlow<UiState>(UiState.Initial)
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
    
    private val _sourceText = MutableStateFlow("")
    val sourceText: StateFlow<String> = _sourceText.asStateFlow()
    
    private val _translatedText = MutableStateFlow("")
    val translatedText: StateFlow<String> = _translatedText.asStateFlow()
    
    private val _sourceLanguage = MutableStateFlow<Language?>(null)
    val sourceLanguage: StateFlow<Language?> = _sourceLanguage.asStateFlow()
    
    private val _targetLanguage = MutableStateFlow<Language?>(null)
    val targetLanguage: StateFlow<Language?> = _targetLanguage.asStateFlow()
    
    val languages = repository.getAllLanguages()
    
    init {
        viewModelScope.launch {
            speechRecognitionService.recognitionState.collect { state ->
                when (state) {
                    is RecognitionState.Result -> {
                        _sourceText.value = state.text
                        translate()
                    }
                    is RecognitionState.Error -> {
                        _uiState.value = UiState.Error(state.message)
                    }
                    else -> {}
                }
            }
        }
        
        viewModelScope.launch {
            textToSpeechService.ttsState.collect { state ->
                when (state) {
                    is TTSState.Error -> {
                        _uiState.value = UiState.Error(state.message)
                    }
                    else -> {}
                }
            }
        }
    }
    
    fun setSourceLanguage(language: Language) {
        _sourceLanguage.value = language
    }
    
    fun setTargetLanguage(language: Language) {
        _targetLanguage.value = language
    }
    
    fun setSourceText(text: String) {
        _sourceText.value = text
        translate()
    }
    
    private fun translate() {
        val source = _sourceLanguage.value
        val target = _targetLanguage.value
        val text = _sourceText.value
        
        if (source != null && target != null && text.isNotBlank()) {
            _uiState.value = UiState.Loading
            
            viewModelScope.launch {
                try {
                    val options = TranslatorOptions.Builder()
                        .setSourceLanguage(source.code)
                        .setTargetLanguage(target.code)
                        .build()
                    
                    val translator = Translation.getClient(options)
                    
                    translator.translate(text)
                        .addOnSuccessListener { translatedText ->
                            _translatedText.value = translatedText
                            _uiState.value = UiState.Success
                        }
                        .addOnFailureListener { exception ->
                            _uiState.value = UiState.Error(exception.message ?: "Translation failed")
                        }
                } catch (e: Exception) {
                    _uiState.value = UiState.Error(e.message ?: "Translation failed")
                }
            }
        }
    }
    
    fun startListening() {
        val language = _sourceLanguage.value?.code ?: return
        speechRecognitionService.startListening(language)
    }
    
    fun stopListening() {
        speechRecognitionService.stopListening()
    }
    
    fun speakTranslation() {
        val text = _translatedText.value
        val language = _targetLanguage.value?.code ?: return
        textToSpeechService.speak(text, language)
    }
    
    fun stopSpeaking() {
        textToSpeechService.stop()
    }
    
    fun toggleFavorite(language: Language) {
        viewModelScope.launch {
            repository.toggleFavorite(language)
        }
    }
    
    fun toggleInstalled(language: Language) {
        viewModelScope.launch {
            repository.toggleInstalled(language)
        }
    }
    
    override fun onCleared() {
        super.onCleared()
        speechRecognitionService.destroy()
        textToSpeechService.shutdown()
    }
}

sealed class UiState {
    object Initial : UiState()
    object Loading : UiState()
    object Success : UiState()
    data class Error(val message: String) : UiState()
} 