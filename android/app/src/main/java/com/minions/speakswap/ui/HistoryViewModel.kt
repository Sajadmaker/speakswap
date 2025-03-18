package com.minions.speakswap.ui

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.minions.speakswap.SpeakSwapApplication
import com.minions.speakswap.data.TranslationHistory
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch

class HistoryViewModel(application: Application) : AndroidViewModel(application) {
    private val historyDao = (application as SpeakSwapApplication).database.historyDao()
    
    val historyItems = historyDao.getAllHistory()
    
    private val _selectedHistoryItem = MutableStateFlow<TranslationHistory?>(null)
    val selectedHistoryItem: StateFlow<TranslationHistory?> = _selectedHistoryItem.asStateFlow()
    
    fun selectHistoryItem(history: TranslationHistory) {
        _selectedHistoryItem.value = history
    }
    
    fun clearHistory() {
        viewModelScope.launch {
            historyDao.deleteAll()
        }
    }
    
    fun getHistoryByLanguages(sourceLang: String, targetLang: String) = 
        historyDao.getHistoryByLanguages(sourceLang, targetLang)
} 