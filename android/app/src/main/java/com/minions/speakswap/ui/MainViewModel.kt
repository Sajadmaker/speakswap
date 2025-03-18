package com.minions.speakswap.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.google.mlkit.nl.translate.Translation
import com.google.mlkit.nl.translate.TranslatorOptions
import com.minions.speakswap.SpeakSwapApplication
import com.minions.speakswap.data.Language
import com.minions.speakswap.service.RecognitionState
import com.minions.speakswap.service.SpeechRecognitionService
import com.minions.speakswap.service.TTSState
import com.minions.speakswap.service.TextToSpeechService
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import java.util.Locale

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
    
    private val _isListening = MutableStateFlow(false)
    val isListening: StateFlow<Boolean> = _isListening.asStateFlow()
    
    private val _isSpeaking = MutableStateFlow(false)
    val isSpeaking: StateFlow<Boolean> = _isSpeaking.asStateFlow()
    
    val languages = repository.getAllLanguages()
    
    init {
        // Set default languages based on system locale
        viewModelScope.launch {
            languages.collect { languageList ->
                if (languageList.isNotEmpty() && _sourceLanguage.value == null && _targetLanguage.value == null) {
                    // Get system language
                    val systemLang = Locale.getDefault().language
                    
                    // Find system language in our language list, default to English if not found
                    val sysLang = languageList.find { it.code == systemLang } ?: languageList.find { it.code == "en" }
                    
                    // Set source language to system language (or English)
                    sysLang?.let { setSourceLanguage(it) }
                    
                    // Set target language to something other than the source language
                    val targetLang = languageList.find { it.code != _sourceLanguage.value?.code && it.isFavorite }
                        ?: languageList.find { it.code != _sourceLanguage.value?.code }
                    
                    targetLang?.let { setTargetLanguage(it) }
                }
            }
        }
        
        viewModelScope.launch {
            speechRecognitionService.recognitionState.collect { state ->
                when (state) {
                    is RecognitionState.Result -> {
                        _sourceText.value = state.text
                        _isListening.value = false
                        translate()
                    }
                    is RecognitionState.Error -> {
                        _uiState.value = UiState.Error(state.message)
                        _isListening.value = false
                    }
                    is RecognitionState.Speaking -> {
                        _isListening.value = true
                    }
                    is RecognitionState.Idle -> {
                        _isListening.value = false
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
                        _isSpeaking.value = false
                    }
                    is TTSState.Speaking -> {
                        _isSpeaking.value = true
                    }
                    is TTSState.Ready, is TTSState.Idle -> {
                        _isSpeaking.value = false
                    }
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
                            
                            // Save to history
                            saveTranslationToHistory(text, translatedText, source.code, target.code)
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
    
    private fun saveTranslationToHistory(sourceText: String, translatedText: String, sourceLanguage: String, targetLanguage: String) {
        viewModelScope.launch {
            val history = com.minions.speakswap.data.TranslationHistory(
                sourceText = sourceText,
                translatedText = translatedText,
                sourceLanguage = sourceLanguage,
                targetLanguage = targetLanguage
            )
            (getApplication() as SpeakSwapApplication).database.historyDao().insert(history)
        }
    }
    
    fun startListening() {
        val language = _sourceLanguage.value?.code ?: return
        speechRecognitionService.startListening(language)
        _isListening.value = true
    }
    
    fun stopListening() {
        speechRecognitionService.stopListening()
        _isListening.value = false
    }
    
    fun speakTranslation() {
        val text = _translatedText.value
        val language = _targetLanguage.value?.code ?: return
        textToSpeechService.speak(text, language)
        _isSpeaking.value = true
    }
    
    fun stopSpeaking() {
        textToSpeechService.stop()
        _isSpeaking.value = false
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