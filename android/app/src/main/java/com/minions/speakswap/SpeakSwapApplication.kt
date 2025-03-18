package com.minions.speakswap

import android.app.Application
import com.google.mlkit.common.model.DownloadConditions
import com.google.mlkit.nl.translate.TranslateLanguage
import com.google.mlkit.nl.translate.Translation
import com.google.mlkit.nl.translate.TranslatorOptions
import com.minions.speakswap.data.AppDatabase
import com.minions.speakswap.data.LanguageRepository
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.launch

class SpeakSwapApplication : Application() {
    
    // Application-level coroutine scope
    val applicationScope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    
    // Lazy initialization of the database
    val database by lazy { AppDatabase.getDatabase(this, applicationScope) }
    
    // Lazy initialization of the repository
    val repository by lazy { LanguageRepository(database.languageDao()) }
    
    override fun onCreate() {
        super.onCreate()
        
        // Pre-download some common language models
        applicationScope.launch {
            preloadCommonLanguageModels()
        }
    }
    
    private fun preloadCommonLanguageModels() {
        val commonLanguages = listOf(
            TranslateLanguage.ENGLISH,
            TranslateLanguage.SPANISH,
            TranslateLanguage.FRENCH,
            TranslateLanguage.GERMAN,
            TranslateLanguage.CHINESE
        )
        
        val downloadConditions = DownloadConditions.Builder()
            .requireWifi()
            .build()
        
        for (sourceLang in commonLanguages) {
            for (targetLang in commonLanguages) {
                if (sourceLang != targetLang) {
                    val options = TranslatorOptions.Builder()
                        .setSourceLanguage(sourceLang)
                        .setTargetLanguage(targetLang)
                        .build()
                        
                    val translator = Translation.getClient(options)
                    translator.downloadModelIfNeeded(downloadConditions)
                        .addOnSuccessListener {
                            // Model downloaded successfully
                        }
                        .addOnFailureListener {
                            // Model download failed
                        }
                }
            }
        }
    }
} 