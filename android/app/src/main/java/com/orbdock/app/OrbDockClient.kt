package com.orbdock.app

import android.os.Handler
import android.os.Looper
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response
import okhttp3.WebSocket
import okhttp3.WebSocketListener
import org.json.JSONObject
import java.net.DatagramPacket
import java.net.DatagramSocket
import java.net.InetAddress
import java.net.SocketTimeoutException
import java.nio.charset.StandardCharsets
import java.util.UUID
import java.util.concurrent.TimeUnit
import javax.crypto.Mac
import javax.crypto.SecretKeyFactory
import javax.crypto.spec.PBEKeySpec
import javax.crypto.spec.SecretKeySpec

data class DiscoveredHost(
    val address: String,
    val name: String,
    val websocketPort: Int
)

class OrbDockClient {
    private val mainHandler = Handler(Looper.getMainLooper())
    private val http = OkHttpClient.Builder()
        .readTimeout(0, TimeUnit.MILLISECONDS)
        .build()

    private var socket: WebSocket? = null
    private var heartbeatTask: Runnable? = null

    suspend fun discover(): List<DiscoveredHost> = withContext(Dispatchers.IO) {
        val found = linkedMapOf<String, DiscoveredHost>()
        DatagramSocket().use { datagram ->
            datagram.broadcast = true
            datagram.soTimeout = 1200
            val request = "ORB_DOCK_DISCOVER_V1".toByteArray(StandardCharsets.UTF_8)
            val broadcast = DatagramPacket(
                request,
                request.size,
                InetAddress.getByName("255.255.255.255"),
                8766
            )
            datagram.send(broadcast)

            val buffer = ByteArray(2048)
            while (true) {
                try {
                    val response = DatagramPacket(buffer, buffer.size)
                    datagram.receive(response)
                    val json = JSONObject(
                        String(response.data, 0, response.length, StandardCharsets.UTF_8)
                    )
                    if (json.optString("type") == "orb_dock.discovery.response" &&
                        json.optInt("protocol_version") == 1
                    ) {
                        val address = response.address.hostAddress ?: continue
                        val host = DiscoveredHost(
                            address = address,
                            name = json.optString("name", "Windows PC"),
                            websocketPort = json.optInt("websocket_port", 8765)
                        )
                        found[address] = host
                    }
                } catch (_: SocketTimeoutException) {
                    break
                } catch (_: Exception) {
                    // Ignore malformed LAN discovery responses.
                }
            }
        }
        found.values.toList()
    }

    fun connect(
        host: DiscoveredHost,
        pin: String,
        deviceId: String,
        deviceName: String,
        onStatus: (String) -> Unit
    ) {
        disconnect()
        val request = Request.Builder()
            .url("ws://${host.address}:${host.websocketPort}")
            .build()

        socket = http.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(webSocket: WebSocket, response: Response) {
                emit(onStatus, "Connected to host. Waiting for pairing challenge…")
            }

            override fun onMessage(webSocket: WebSocket, text: String) {
                try {
                    val message = JSONObject(text)
                    when (message.optString("type")) {
                        "pair.challenge" -> {
                            val nonce = message.getJSONObject("payload").getString("nonce")
                            val proof = createProof(pin, nonce, deviceId, deviceName)
                            val payload = JSONObject()
                                .put("device_id", deviceId)
                                .put("device_name", deviceName)
                                .put("proof", proof)
                            webSocket.send(makeMessage("pair.request", payload).toString())
                            emit(onStatus, "Pairing request sent…")
                        }
                        "connection.ready" -> {
                            emit(onStatus, "Paired and connected to ${host.name}.")
                            startHeartbeat(webSocket)
                        }
                        "connection.pong" -> emit(onStatus, "Connected to ${host.name}.")
                        "error" -> {
                            val payload = message.optJSONObject("payload")
                            emit(onStatus, "Connection error: ${payload?.optString("message") ?: "Unknown error"}")
                        }
                    }
                } catch (error: Exception) {
                    emit(onStatus, "Invalid response from Windows host: ${error.message}")
                }
            }

            override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                stopHeartbeat()
                emit(onStatus, "Connection failed: ${t.message ?: "network error"}")
            }

            override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                stopHeartbeat()
                emit(onStatus, "Disconnected: $reason")
            }
        })
    }

    fun disconnect() {
        stopHeartbeat()
        socket?.close(1000, "User disconnected")
        socket = null
    }

    private fun startHeartbeat(webSocket: WebSocket) {
        stopHeartbeat()
        val task = object : Runnable {
            override fun run() {
                val payload = JSONObject().put("sent_at", System.currentTimeMillis())
                webSocket.send(makeMessage("connection.ping", payload).toString())
                mainHandler.postDelayed(this, 15_000)
            }
        }
        heartbeatTask = task
        mainHandler.postDelayed(task, 15_000)
    }

    private fun stopHeartbeat() {
        heartbeatTask?.let(mainHandler::removeCallbacks)
        heartbeatTask = null
    }

    private fun emit(callback: (String) -> Unit, value: String) {
        mainHandler.post { callback(value) }
    }

    private fun makeMessage(type: String, payload: JSONObject): JSONObject =
        JSONObject()
            .put("version", 1)
            .put("type", type)
            .put("request_id", UUID.randomUUID().toString())
            .put("payload", payload)

    private fun createProof(pin: String, nonce: String, deviceId: String, deviceName: String): String {
        require(pin.length == 6 && pin.all(Char::isDigit)) { "Enter the six-digit pairing code." }

        val salt = "ORB-DOCK-PAIRING-V1".toByteArray(StandardCharsets.UTF_8)
        val spec = PBEKeySpec(pin.toCharArray(), salt, 300_000, 256)
        val key = try {
            SecretKeyFactory.getInstance("PBKDF2WithHmacSHA256")
                .generateSecret(spec).encoded
        } finally {
            spec.clearPassword()
        }

        val mac = Mac.getInstance("HmacSHA256")
        mac.init(SecretKeySpec(key, "HmacSHA256"))
        val message = "$nonce:$deviceId:$deviceName".toByteArray(StandardCharsets.UTF_8)
        return mac.doFinal(message).joinToString("") { "%02x".format(it) }
    }
}
