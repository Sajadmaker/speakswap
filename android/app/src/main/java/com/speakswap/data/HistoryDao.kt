package com.speakswap

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface HistoryDao {
    @Query("SELECT * FROM translation_history ORDER BY timestamp DESC")
    fun getAllHistory(): Flow<List<TranslationHistory>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(history: TranslationHistory)

    @Delete
    suspend fun delete(history: TranslationHistory)

    @Query("DELETE FROM translation_history")
    suspend fun deleteAll()

    @Query("SELECT * FROM translation_history WHERE sourceLanguage = :sourceLang AND targetLanguage = :targetLang ORDER BY timestamp DESC")
    fun getHistoryByLanguages(sourceLang: String, targetLang: String): Flow<List<TranslationHistory>>
} 