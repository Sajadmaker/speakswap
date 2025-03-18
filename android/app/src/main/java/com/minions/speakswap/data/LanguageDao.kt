package com.minions.speakswap.data

import androidx.room.*
import kotlinx.coroutines.flow.Flow

@Dao
interface LanguageDao {
    @Query("SELECT * FROM languages ORDER BY name ASC")
    fun getAllLanguages(): Flow<List<Language>>

    @Query("SELECT * FROM languages WHERE isFavorite = 1 ORDER BY name ASC")
    fun getFavoriteLanguages(): Flow<List<Language>>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(language: Language)

    @Update
    suspend fun update(language: Language)

    @Delete
    suspend fun delete(language: Language)

    @Query("SELECT * FROM languages WHERE code = :code")
    suspend fun getLanguageByCode(code: String): Language?
} 