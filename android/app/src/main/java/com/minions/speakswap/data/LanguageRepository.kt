package com.minions.speakswap.data

import kotlinx.coroutines.flow.Flow

class LanguageRepository(private val languageDao: LanguageDao) {
    
    fun getAllLanguages(): Flow<List<Language>> = languageDao.getAllLanguages()
    
    fun getFavoriteLanguages(): Flow<List<Language>> = languageDao.getFavoriteLanguages()
    
    suspend fun insert(language: Language) = languageDao.insert(language)
    
    suspend fun update(language: Language) = languageDao.update(language)
    
    suspend fun delete(language: Language) = languageDao.delete(language)
    
    suspend fun getLanguageByCode(code: String): Language? = languageDao.getLanguageByCode(code)
    
    suspend fun toggleFavorite(language: Language) {
        languageDao.update(language.copy(isFavorite = !language.isFavorite))
    }
    
    suspend fun toggleInstalled(language: Language) {
        languageDao.update(language.copy(isInstalled = !language.isInstalled))
    }
} 