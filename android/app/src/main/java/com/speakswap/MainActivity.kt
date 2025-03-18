package com.speakswap

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.speakswap.ui.theme.SpeakSwapTheme

class MainActivity : ComponentActivity() {
    
    private val viewModel: MainViewModel by viewModels()
    
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            // Permission granted, proceed with speech recognition
        }
    }
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        setContent {
            SpeakSwapTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    MainScreen(
                        viewModel = viewModel,
                        onRequestPermission = { checkAndRequestPermission() }
                    )
                }
            }
        }
    }
    
    private fun checkAndRequestPermission() {
        when {
            ContextCompat.checkSelfPermission(
                this,
                Manifest.permission.RECORD_AUDIO
            ) == PackageManager.PERMISSION_GRANTED -> {
                // Permission already granted
            }
            else -> {
                requestPermissionLauncher.launch(Manifest.permission.RECORD_AUDIO)
            }
        }
    }
}

@Composable
fun MainScreen(
    viewModel: MainViewModel,
    onRequestPermission: () -> Unit
) {
    val context = LocalContext.current
    val uiState by viewModel.uiState.collectAsState()
    val sourceText by viewModel.sourceText.collectAsState()
    val translatedText by viewModel.translatedText.collectAsState()
    val sourceLanguage by viewModel.sourceLanguage.collectAsState()
    val targetLanguage by viewModel.targetLanguage.collectAsState()
    val languages by viewModel.languages.collectAsState(initial = emptyList())
    
    Column(
        modifier = Modifier
            .fillMaxSize()
            .padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Language Selection
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            LanguageDropdown(
                languages = languages,
                selectedLanguage = sourceLanguage,
                onLanguageSelected = viewModel::setSourceLanguage,
                label = "From"
            )
            
            LanguageDropdown(
                languages = languages,
                selectedLanguage = targetLanguage,
                onLanguageSelected = viewModel::setTargetLanguage,
                label = "To"
            )
        }
        
        // Source Text
        OutlinedTextField(
            value = sourceText,
            onValueChange = viewModel::setSourceText,
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            label = { Text("Enter text") },
            placeholder = { Text("Type or speak...") }
        )
        
        // Translation Status
        when (uiState) {
            is UiState.Loading -> {
                CircularProgressIndicator(
                    modifier = Modifier.align(Alignment.CenterHorizontally)
                )
            }
            is UiState.Error -> {
                Text(
                    text = (uiState as UiState.Error).message,
                    color = MaterialTheme.colorScheme.error,
                    modifier = Modifier.align(Alignment.CenterHorizontally)
                )
            }
            else -> {}
        }
        
        // Translated Text
        OutlinedTextField(
            value = translatedText,
            onValueChange = { },
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            label = { Text("Translation") },
            readOnly = true
        )
        
        // Action Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            Button(
                onClick = onRequestPermission,
                modifier = Modifier.weight(1f).padding(end = 8.dp)
            ) {
                Text("Speak")
            }
            
            Button(
                onClick = { /* Implement text-to-speech */ },
                modifier = Modifier.weight(1f).padding(start = 8.dp)
            ) {
                Text("Listen")
            }
        }
    }
}

@Composable
fun LanguageDropdown(
    languages: List<Language>,
    selectedLanguage: Language?,
    onLanguageSelected: (Language) -> Unit,
    label: String
) {
    var expanded by remember { mutableStateOf(false) }
    
    ExposedDropdownMenuBox(
        expanded = expanded,
        onExpandedChange = { expanded = it }
    ) {
        OutlinedTextField(
            value = selectedLanguage?.name ?: "Select $label",
            onValueChange = { },
            readOnly = true,
            label = { Text(label) },
            trailingIcon = { ExposedDropdownMenuDefaults.TrailingIcon(expanded = expanded) },
            modifier = Modifier
                .fillMaxWidth(0.48f)
                .menuAnchor()
        )
        
        ExposedDropdownMenu(
            expanded = expanded,
            onDismissRequest = { expanded = false }
        ) {
            languages.forEach { language ->
                DropdownMenuItem(
                    text = { Text(language.name) },
                    onClick = {
                        onLanguageSelected(language)
                        expanded = false
                    }
                )
            }
        }
    }
} 