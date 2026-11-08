package com.orbdock.app

import android.os.Bundle
import android.provider.Settings
import android.os.Build
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.runtime.setValue
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.unit.dp
import kotlinx.coroutines.launch
import java.util.UUID

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val client = OrbDockClient()
        val androidId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID)
            ?: UUID.randomUUID().toString()

        setContent {
            MaterialTheme {
                OrbDockScreen(
                    client = client,
                    deviceId = androidId,
                    deviceName = Build.MODEL ?: "Android device"
                )
            }
        }
    }
}

@Composable
private fun OrbDockScreen(
    client: OrbDockClient,
    deviceId: String,
    deviceName: String
) {
    val scope = rememberCoroutineScope()
    var hosts by remember { mutableStateOf(emptyList<DiscoveredHost>()) }
    var selectedHost by remember { mutableStateOf<DiscoveredHost?>(null) }
    var pin by remember { mutableStateOf("") }
    var manualAddress by remember { mutableStateOf("") }
    var status by remember { mutableStateOf("Ready to discover your Windows PC.") }
    var scanning by remember { mutableStateOf(false) }

    Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
        Column(
            modifier = Modifier.fillMaxSize().padding(22.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            Text(
                text = "ORB DOCK",
                style = MaterialTheme.typography.headlineMedium,
                fontWeight = FontWeight.Bold
            )
            Text(
                text = "WINDOWS COMPANION",
                style = MaterialTheme.typography.labelMedium,
                color = MaterialTheme.colorScheme.primary
            )
            Card(
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(20.dp),
                colors = CardDefaults.cardColors(
                    containerColor = MaterialTheme.colorScheme.surfaceVariant
                )
            ) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Connection status", fontWeight = FontWeight.SemiBold)
                    Spacer(Modifier.height(8.dp))
                    Text(status, style = MaterialTheme.typography.bodyMedium)
                }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(10.dp)) {
                Button(
                    onClick = {
                        scope.launch {
                            scanning = true
                            status = "Searching for ORB DOCK hosts on this Wi-Fi…"
                            hosts = client.discover()
                            selectedHost = hosts.firstOrNull()
                            status = if (hosts.isEmpty()) {
                                "No PC found. Check that the Windows host is running and both devices use the same private Wi-Fi."
                            } else {
                                "Found ${hosts.size} PC(s). Select the laptop below."
                            }
                            scanning = false
                        }
                    },
                    enabled = !scanning
                ) {
                    Text(if (scanning) "Searching…" else "Find my PC")
                }
                Button(
                    onClick = { client.disconnect(); status = "Disconnected." }
                ) {
                    Text("Disconnect")
                }
            }

            Text("DISCOVERED DEVICES", style = MaterialTheme.typography.labelLarge)
            if (hosts.isEmpty()) {
                Text(
                    "Your Windows laptop will appear here when the ORB DOCK host is running.",
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.onSurfaceVariant
                )
            } else {
                LazyColumn(
                    modifier = Modifier.weight(1f, fill = false),
                    verticalArrangement = Arrangement.spacedBy(8.dp)
                ) {
                    items(hosts) { host ->
                        Card(
                            modifier = Modifier.fillMaxWidth().clickable { selectedHost = host },
                            colors = CardDefaults.cardColors(
                                containerColor = if (selectedHost == host)
                                    MaterialTheme.colorScheme.primaryContainer
                                else MaterialTheme.colorScheme.surfaceVariant
                            )
                        ) {
                            Column(modifier = Modifier.padding(14.dp)) {
                                Text(host.name, fontWeight = FontWeight.SemiBold)
                                Text(
                                    "${host.address}:${host.websocketPort}",
                                    style = MaterialTheme.typography.bodySmall
                                )
                            }
                        }
                    }
                }
            }

            OutlinedTextField(
                value = pin,
                onValueChange = { pin = it.filter(Char::isDigit).take(6) },
                modifier = Modifier.fillMaxWidth(),
                label = { Text("Windows pairing code") },
                placeholder = { Text("6 digits") },
                keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.NumberPassword),
                singleLine = true
            )
            Button(
                onClick = {
                    val host = selectedHost
                    if (host == null) {
                        status = "Find and select your Windows PC first."
                    } else if (pin.length != 6) {
                        status = "Enter the six-digit code shown in the Windows terminal."
                    } else {
                        status = "Connecting to ${host.name}…"
                        client.connect(host, pin, deviceId, deviceName) { status = it }
                    }
                },
                modifier = Modifier.fillMaxWidth(),
                enabled = pin.length == 6 && selectedHost != null
            ) {
                Text("Connect")
            }

            Text(
                "Phase 1 preview · Local network only",
                style = MaterialTheme.typography.labelSmall,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
