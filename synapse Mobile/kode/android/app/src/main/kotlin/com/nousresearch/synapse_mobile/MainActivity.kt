package com.nousresearch.synapse_mobile

import android.content.Intent
import android.os.Build
import androidx.core.app.NotificationManagerCompat
import io.flutter.embedding.android.FlutterActivity
import io.flutter.embedding.engine.FlutterEngine
import io.flutter.plugin.common.MethodChannel

/**
 * MainActivity — menyediakan jembatan (MethodChannel) antara Flutter dan
 * TaskService (foreground service untuk notifikasi latar belakang).
 *
 * Channel: "synapse/task"
 *   - mulaiPantau(runId, baseUrl, apiKey, judul)  -> jalankan service
 *   - hentikan()                                  -> hentikan service
 *   - izinNotifikasi()                            -> cek izin notifikasi
 */
class MainActivity : FlutterActivity() {

    private val CHANNEL = "synapse/task"

    override fun configureFlutterEngine(flutterEngine: FlutterEngine) {
        super.configureFlutterEngine(flutterEngine)

        MethodChannel(flutterEngine.dartExecutor.binaryMessenger, CHANNEL)
            .setMethodCallHandler { call, result ->
                when (call.method) {
                    "mulaiPantau" -> {
                        try {
                            val runId = call.argument<String>("runId") ?: ""
                            val base = call.argument<String>("baseUrl") ?: ""
                            val key = call.argument<String>("apiKey") ?: ""
                            val judul = call.argument<String>("judul") ?: "Tugas Synapse"

                            val i = Intent(this, TaskService::class.java).apply {
                                putExtra(TaskService.EXTRA_RUN_ID, runId)
                                putExtra(TaskService.EXTRA_BASE, base)
                                putExtra(TaskService.EXTRA_KEY, key)
                                putExtra(TaskService.EXTRA_JUDUL, judul)
                            }
                            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
                                startForegroundService(i)
                            } else {
                                startService(i)
                            }
                            result.success(true)
                        } catch (e: Exception) {
                            result.error("GAGAL", e.message, null)
                        }
                    }

                    "hentikan" -> {
                        try {
                            stopService(Intent(this, TaskService::class.java))
                            result.success(true)
                        } catch (e: Exception) {
                            result.error("GAGAL", e.message, null)
                        }
                    }

                    "izinNotifikasi" -> {
                        val ok = NotificationManagerCompat.from(this).areNotificationsEnabled()
                        result.success(ok)
                    }

                    else -> result.notImplemented()
                }
            }
    }
}
