package com.minions.speakswap.data

import androidx.room.Entity
import androidx.room.PrimaryKey

@Entity(tableName = "languages")
data class Language(
    @PrimaryKey
    val code: String,
    val name: String,
    val isInstalled: Boolean = false,
    val isFavorite: Boolean = false
) 