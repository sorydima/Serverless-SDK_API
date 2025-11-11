package com.rechain.synapsesdk

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier
import androidx.compose.ui.tooling.preview.Preview
import android.util.Log
import androidx.compose.runtime.*
import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch

class MainActivity : ComponentActivity(), ViewContainer {

    private lateinit var uiBridge: UIAdaptationBridge
    private val TAG = "MainActivity"

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        // Initialize UI adaptation bridge
        uiBridge = UIAdaptationBridge.getInstance(this)

        setContent {
            SynapseApp()
        }
    }

    @Composable
    fun SynapseApp() {
        val coroutineScope = rememberCoroutineScope()
        var currentScreen by remember { mutableStateOf("dashboard") }
        var adaptations by remember { mutableStateOf(listOf<UIAdaptation>()) }

        MaterialTheme {
            Surface(
                modifier = Modifier.fillMaxSize(),
                color = MaterialTheme.colorScheme.background
            ) {
                Column(modifier = Modifier.fillMaxSize()) {
                    // Screen selector for demo
                    Row(
                        modifier = Modifier
                            .fillMaxWidth()
                            .padding(16.dp),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        Button(onClick = {
                            currentScreen = "dashboard"
                            loadAdaptations("dashboard")
                        }) {
                            Text("Dashboard")
                        }
                        Button(onClick = {
                            currentScreen = "messaging"
                            loadAdaptations("messaging")
                        }) {
                            Text("Messaging")
                        }
                        Button(onClick = {
                            currentScreen = "settings"
                            loadAdaptations("settings")
                        }) {
                            Text("Settings")
                        }
                    }

                    // Adaptive UI content
                    AdaptiveContent(currentScreen, adaptations)

                    // Adaptation controls
                    Spacer(modifier = Modifier.weight(1f))
                    AdaptationControls(currentScreen, adaptations) { elementId, feedback ->
                        uiBridge.provideFeedback(elementId, feedback)
                        loadAdaptations(currentScreen) // Refresh adaptations
                    }
                }
            }
        }
    }

    private fun loadAdaptations(screenName: String) {
        // Load adaptations for current screen
        val newAdaptations = uiBridge.getAdaptations(screenName, "demo_user")
        adaptations = newAdaptations

        // Record screen view interaction
        uiBridge.recordInteraction(
            InteractionEvent(
                screenName = screenName,
                elementId = "screen_view",
                action = "view",
                position = Position.CENTER
            )
        )

        Log.d(TAG, "Loaded ${newAdaptations.size} adaptations for $screenName")
    }

    @Composable
    fun AdaptiveContent(screenName: String, adaptations: List<UIAdaptation>) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(
                text = "SynapseSDK Android - $screenName",
                style = MaterialTheme.typography.headlineMedium
            )

            Spacer(modifier = Modifier.height(16.dp))

            // Show adaptive elements based on screen
            when (screenName) {
                "dashboard" -> DashboardContent(adaptations)
                "messaging" -> MessagingContent(adaptations)
                "settings" -> SettingsContent(adaptations)
            }
        }
    }

    @Composable
    fun DashboardContent(adaptations: List<UIAdaptation>) {
        Column {
            // Quick actions (adaptable)
            val quickActionsVisible = adaptations.find { it.elementId == "dashboard_quick_actions" }?.action != UIAction.HIDE
            if (quickActionsVisible) {
                Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Quick Actions", style = MaterialTheme.typography.titleMedium)
                        Row(horizontalArrangement = Arrangement.SpaceEvenly, modifier = Modifier.fillMaxWidth()) {
                            Button(onClick = { recordInteraction("dashboard_quick_actions", "messages") }) { Text("Messages") }
                            Button(onClick = { recordInteraction("dashboard_quick_actions", "contacts") }) { Text("Contacts") }
                            Button(onClick = { recordInteraction("dashboard_quick_actions", "settings") }) { Text("Settings") }
                        }
                    }
                }
            }

            // Navigation (adaptable)
            val navigationVisible = adaptations.find { it.elementId == "dashboard_navigation" }?.action != UIAction.HIDE
            if (navigationVisible) {
                Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Navigation", style = MaterialTheme.typography.titleMedium)
                        // Navigation items would go here
                        Text("Navigation content adapted based on usage patterns")
                    }
                }
            }
        }
    }

    @Composable
    fun MessagingContent(adaptations: List<UIAdaptation>) {
        Column {
            // Input field (always visible but adaptable)
            Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Message Input", style = MaterialTheme.typography.titleMedium)
                    OutlinedTextField(
                        value = "",
                        onValueChange = {},
                        label = { Text("Type your message...") },
                        modifier = Modifier.fillMaxWidth()
                    )
                }
            }

            // Emoji picker (adaptable visibility)
            val emojiVisible = adaptations.find { it.elementId == "messaging_emoji_picker" }?.action != UIAction.HIDE
            if (emojiVisible) {
                Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Emoji Picker", style = MaterialTheme.typography.titleMedium)
                        Text("😀 😀 😀 😀 😀 (Adapted based on usage)")
                        Button(onClick = { recordInteraction("messaging_emoji_picker", "select") }) {
                            Text("Select Emoji")
                        }
                    }
                }
            }
        }
    }

    @Composable
    fun SettingsContent(adaptations: List<UIAdaptation>) {
        Column {
            // Accessibility settings (adaptable)
            val accessibilityVisible = adaptations.find { it.elementId == "settings_accessibility" }?.action != UIAction.HIDE
            if (accessibilityVisible) {
                Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Accessibility", style = MaterialTheme.typography.titleMedium)
                        Text("Font size, contrast, and other accessibility options")
                        Switch(checked = true, onCheckedChange = {})
                    }
                }
            }

            // Advanced settings (adaptable - often hidden)
            val advancedVisible = adaptations.find { it.elementId == "settings_advanced" }?.action != UIAction.HIDE
            if (advancedVisible) {
                Card(modifier = Modifier.fillMaxWidth().padding(8.dp)) {
                    Column(modifier = Modifier.padding(16.dp)) {
                        Text("Advanced Settings", style = MaterialTheme.typography.titleMedium)
                        Text("Developer options and advanced configurations")
                        Switch(checked = false, onCheckedChange = {})
                    }
                }
            }
        }
    }

    @Composable
    fun AdaptationControls(screenName: String, adaptations: List<UIAdaptation>, onFeedback: (String, Float) -> Unit) {
        Card(modifier = Modifier.fillMaxWidth().padding(16.dp)) {
            Column(modifier = Modifier.padding(16.dp)) {
                Text("UI Adaptation Controls", style = MaterialTheme.typography.titleMedium)

                adaptations.forEach { adaptation ->
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween
                    ) {
                        Text("${adaptation.elementId}: ${adaptation.action} (${adaptation.confidence})")
                        Row {
                            Button(onClick = { onFeedback(adaptation.elementId, 1.0f) }) { Text("👍") }
                            Button(onClick = { onFeedback(adaptation.elementId, 0.0f) }) { Text("👎") }
                        }
                    }
                }

                Text("Stats: ${uiBridge.getStats()}", style = MaterialTheme.typography.bodySmall)
            }
        }
    }

    private fun recordInteraction(elementId: String, action: String) {
        uiBridge.recordInteraction(
            InteractionEvent(
                screenName = currentScreen,
                elementId = elementId,
                action = action,
                position = Position.CENTER
            )
        )
    }

    // ViewContainer implementation
    override fun showElement(elementId: String, position: Position?) {
        Log.d(TAG, "Showing element: $elementId at $position")
        // In a real implementation, this would manipulate actual UI elements
    }

    override fun hideElement(elementId: String) {
        Log.d(TAG, "Hiding element: $elementId")
        // In a real implementation, this would manipulate actual UI elements
    }

    override fun moveElement(elementId: String, position: Position) {
        Log.d(TAG, "Moving element: $elementId to $position")
        // In a real implementation, this would manipulate actual UI elements
    }

    override fun resizeElement(elementId: String, size: Size) {
        Log.d(TAG, "Resizing element: $elementId to $size")
        // In a real implementation, this would manipulate actual UI elements
    }

    override fun onDestroy() {
        super.onDestroy()
        uiBridge.shutdown()
    }
}

@Composable
fun Greeting(name: String, modifier: Modifier = Modifier) {
    Text(
        text = "Hello $name!",
        modifier = modifier
    )
}

@Preview(showBackground = true)
@Composable
fun GreetingPreview() {
    MaterialTheme {
        Greeting("Android")
    }
}
