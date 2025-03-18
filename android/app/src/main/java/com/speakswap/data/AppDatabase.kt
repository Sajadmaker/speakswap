package com.speakswap

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.sqlite.db.SupportSQLiteDatabase
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.launch

@Database(entities = [Language::class, TranslationHistory::class], version = 1, exportSchema = false)
abstract class AppDatabase : RoomDatabase() {
    
    abstract fun languageDao(): LanguageDao
    abstract fun historyDao(): HistoryDao
    
    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null
        
        fun getDatabase(context: Context, scope: CoroutineScope): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "speakswap_database"
                )
                .addCallback(AppDatabaseCallback(scope))
                .build()
                
                INSTANCE = instance
                instance
            }
        }
    }
    
    private class AppDatabaseCallback(
        private val scope: CoroutineScope
    ) : RoomDatabase.Callback() {
        
        override fun onCreate(db: SupportSQLiteDatabase) {
            super.onCreate(db)
            INSTANCE?.let { database ->
                scope.launch {
                    // Populate the database with default languages
                    val languageDao = database.languageDao()
                    populateDefaultLanguages(languageDao)
                }
            }
        }
        
        // Prepopulate the database with common languages
        private suspend fun populateDefaultLanguages(languageDao: LanguageDao) {
            val defaultLanguages = listOf(
                Language("en", "English", true, true),
                Language("es", "Spanish", true, true),
                Language("fr", "French", true, true),
                Language("de", "German", true, true),
                Language("zh", "Chinese", true, true),
                Language("ja", "Japanese", true, true),
                Language("ru", "Russian", true, true),
                Language("ar", "Arabic", true, true),
                Language("hi", "Hindi", true, true),
                Language("pt", "Portuguese", true, true)
            )
            
            for (language in defaultLanguages) {
                languageDao.insert(language)
            }
        }
    }
} 