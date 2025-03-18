package com.minions.speakswap

import android.Manifest
import android.content.pm.PackageManager
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.viewModels
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.History
import androidx.compose.material.icons.filled.Translate
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import androidx.navigation.compose.rememberNavController
import com.minions.speakswap.data.Language
import com.minions.speakswap.ui.HistoryScreen
import com.minions.speakswap.ui.HistoryViewModel
import com.minions.speakswap.ui.MainViewModel
import com.minions.speakswap.ui.UiState
import com.minions.speakswap.ui.theme.SpeakSwapTheme

class MainActivity : ComponentActivity() {
    
    private val mainViewModel: MainViewModel by viewModels()
    private val historyViewModel: HistoryViewModel by viewModels()
    
    private val requestPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { isGranted ->
        if (isGranted) {
            mainViewModel.startListening()
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
                    val navController = rememberNavController()
                    
                    Scaffold(
                        bottomBar = {
                            NavigationBar {
                                NavigationBarItem(
                                    selected = navController.currentBackStackEntry?.destination?.route == "main",
                                    onClick = { navController.navigate("main") },
                                    icon = { Icon(Icons.Filled.Translate, contentDescription = "Translate") },
                                    label = { Text("Translate") }
                                )
                                NavigationBarItem(
                                    selected = navController.currentBackStackEntry?.destination?.route == "history",
                                    onClick = { navController.navigate("history") },
                                    icon = { Icon(Icons.Filled.History, contentDescription = "History") },
                                    label = { Text("History") }
                                )
                            }
                        }
                    ) { padding ->
                        NavHost(
                            navController = navController,
                            startDestination = "main",
                            modifier = Modifier.padding(padding)
                        ) {
                            composable("main") {
                                MainScreen(
                                    viewModel = mainViewModel,
                                    onRequestPermission = { checkAndRequestPermission() }
                                )
                            }
                            composable("history") {
                                HistoryScreen(viewModel = historyViewModel)
                            }
                        }
                    }
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
                mainViewModel.startListening()
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
    val isListening by viewModel.isListening.collectAsState()
    val isSpeaking by viewModel.isSpeaking.collectAsState()
    
    LaunchedEffect(uiState) {
        when (uiState) {
            is UiState.Error -> {
                // Handle error state
            }
            else -> {}
        }
    }
    
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
                label = stringResource(R.string.from_language)
            )
            
            LanguageDropdown(
                languages = languages,
                selectedLanguage = targetLanguage,
                onLanguageSelected = viewModel::setTargetLanguage,
                label = stringResource(R.string.to_language)
            )
        }
        
        // Source Text
        OutlinedTextField(
            value = sourceText,
            onValueChange = viewModel::setSourceText,
            modifier = Modifier
                .fillMaxWidth()
                .weight(1f),
            label = { Text(stringResource(R.string.enter_text)) },
            placeholder = { Text(stringResource(R.string.type_or_speak)) }
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
            label = { Text(stringResource(R.string.translation)) },
            readOnly = true
        )
        
        // Action Buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            Button(
                onClick = {
                    if (isListening) {
                        viewModel.stopListening()
                    } else {
                        onRequestPermission()
                    }
                },
                modifier = Modifier
                    .weight(1f)
                    .padding(end = 8.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isListening) 
                        MaterialTheme.colorScheme.error 
                    else 
                        MaterialTheme.colorScheme.primary
                )
            ) {
                Text(
                    if (isListening) 
                        stringResource(R.string.stop) 
                    else 
                        stringResource(R.string.speak)
                )
            }
            
            Button(
                onClick = {
                    if (isSpeaking) {
                        viewModel.stopSpeaking()
                    } else {
                        viewModel.speakTranslation()
                    }
                },
                modifier = Modifier
                    .weight(1f)
                    .padding(start = 8.dp),
                colors = ButtonDefaults.buttonColors(
                    containerColor = if (isSpeaking) 
                        MaterialTheme.colorScheme.error 
                    else 
                        MaterialTheme.colorScheme.primary
                )
            ) {
                Text(
                    if (isSpeaking) 
                        stringResource(R.string.stop) 
                    else 
                        stringResource(R.string.listen)
                )
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
            value = selectedLanguage?.name ?: stringResource(R.string.select_language),
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