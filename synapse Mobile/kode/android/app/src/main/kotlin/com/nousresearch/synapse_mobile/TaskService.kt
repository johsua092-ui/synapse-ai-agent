package com.nousresearch.synapse_mobile

import android.app.*
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.os.Build
import android.os.IBinder
import androidx.core.app.NotificationCompat
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import kotlin.concurrent.thread

/**
 * TaskService — Foreground Service untuk memantau tugas Synapse di LATAR BELAKANG.
 *
 * Alur:
 *   1. App kirim tugas -> POST /v1/runs -> dapat run_id
 *   2. App panggil service ini lewat MethodChannel ("startWatch")
 *   3. Service tampilkan notifikasi FASE 1 (sedang bekerja, ongoing)
 *   4. Service polling GET /v1/runs/{id} tiap 3 detik
 *   5. Selesai -> notifikasi FASE 2 (hasil) / Gagal -> FASE 3
 *   6. Service berhenti (stopSelf)
 *
 * Kenapa Foreground Service?
 *   Proses biasa dibunuh Android saat app di-swipe. Foreground service dijamin
 *   hidup + wajib tampilkan notifikasi (persis yang kita butuhkan).
 */
class TaskService : Service() {

    companion object {
        const val EXTRA_RUN_ID = "run_id"
        const val EXTRA_BASE = "base_url"
        const val EXTRA_KEY = "api_key"
        const val EXTRA_JUDUL = "judul"

        const val CH_PROGRESS = "synapse_progress"
        const val CH_DONE = "synapse_done"
        const val CH_ERROR = "synapse_error"

        const val ID_PROGRESS = 1001
        const val ID_HASIL_BASE = 2000

        const val INTERVAL_MS = 3000L
        const val MAKS_MS = 10 * 60 * 1000L   // 10 menit
    }

    private var berjalan = false

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onCreate() {
        super.onCreate()
        buatChannel()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        val runId = intent?.getStringExtra(EXTRA_RUN_ID) ?: return START_NOT_STICKY
        val base = intent.getStringExtra(EXTRA_BASE) ?: "http://127.0.0.1:8642"
        val key = intent.getStringExtra(EXTRA_KEY) ?: ""
        val judul = intent.getStringExtra(EXTRA_JUDUL) ?: "Tugas Synapse"

        // === FASE 1: notifikasi "sedang bekerja" (ongoing) ===
        startForeground(ID_PROGRESS, notifProgress(judul))

        if (!berjalan) {
            berjalan = true
            thread { pantau(runId, base, key, judul) }
        }
        return START_NOT_STICKY
    }

    /** Polling status tugas sampai selesai / gagal / timeout. */
    private fun pantau(runId: String, base: String, key: String, judul: String) {
        val mulai = System.currentTimeMillis()
        var hasilAkhir: String? = null
        var gagal: String? = null

        while (System.currentTimeMillis() - mulai < MAKS_MS) {
            try {
                val url = URL("${base.trimEnd('/')}/v1/runs/$runId")
                val c = (url.openConnection() as HttpURLConnection).apply {
                    requestMethod = "GET"
                    setRequestProperty("Authorization", "Bearer $key")
                    connectTimeout = 8000
                    readTimeout = 15000
                }
                android.util.Log.d("TaskService", "poll $runId -> HTTP ${c.responseCode}")
                if (c.responseCode == 200) {
                    val body = c.inputStream.bufferedReader().readText()
                    val j = JSONObject(body)
                    val status = j.optString("status", "")
                    if (status == "completed") {
                        hasilAkhir = j.optString("output", "(tanpa hasil)")
                        break
                    }
                    if (status == "failed" || status == "error" || status == "cancelled") {
                        gagal = j.optString("error", "Tugas gagal.")
                        break
                    }
                } else if (c.responseCode == 404) {
                    gagal = "Tugas tidak ditemukan di server."
                    break
                }
                c.disconnect()
            } catch (e: Exception) {
                android.util.Log.w("TaskService", "poll gagal: ${e.message}")
            }
            Thread.sleep(INTERVAL_MS)
        }

        if (hasilAkhir == null && gagal == null) gagal = "Waktu habis (lebih dari 10 menit)."

        // === FASE 2 / 3 ===
        val idNotif = ID_HASIL_BASE + (System.currentTimeMillis() % 500).toInt()
        val n = if (hasilAkhir != null) notifSelesai(judul, hasilAkhir!!)
                else notifGagal(judul, gagal!!)
        (getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager)
            .notify(idNotif, n)

        berjalan = false
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    // ==================== NOTIFIKASI ====================

    private fun buatChannel() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.O) return
        val nm = getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager

        nm.createNotificationChannel(NotificationChannel(
            CH_PROGRESS, "Synapse — sedang bekerja",
            NotificationManager.IMPORTANCE_LOW).apply {
            description = "Menampilkan tugas yang sedang berjalan"
            setShowBadge(false)
        })

        nm.createNotificationChannel(NotificationChannel(
            CH_DONE, "Synapse — selesai",
            NotificationManager.IMPORTANCE_DEFAULT).apply {
            description = "Pemberitahuan tugas yang sudah selesai"
        })

        nm.createNotificationChannel(NotificationChannel(
            CH_ERROR, "Synapse — gagal",
            NotificationManager.IMPORTANCE_HIGH).apply {
            description = "Pemberitahuan tugas yang gagal"
        })
    }

    /** FASE 1 — sedang bekerja (ongoing, tidak bisa di-swipe). */
    private fun notifProgress(judul: String): Notification {
        val buka = PendingIntent.getActivity(
            this, 0, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

        return NotificationCompat.Builder(this, CH_PROGRESS)
            .setSmallIcon(R.drawable.ic_stat_synapse)
            .setContentTitle("Synapse sedang bekerja")
            .setContentText(judul)
            .setColor(0xFFDCB363.toInt())
            .setProgress(0, 0, true)          // progress tak tentu
            .setOngoing(true)                 // tidak bisa di-swipe
            .setOnlyAlertOnce(true)
            .setContentIntent(buka)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build()
    }

    /** FASE 2 — selesai (ada hasil, bisa dibuka/di-copy). */
    private fun notifSelesai(judul: String, hasil: String): Notification {
        val potong = if (hasil.length > 500) hasil.substring(0, 500) + "..." else hasil

        val buka = PendingIntent.getActivity(
            this, 1, Intent(this, MainActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP
            }, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

        return NotificationCompat.Builder(this, CH_DONE)
            .setSmallIcon(R.drawable.ic_stat_synapse)
            .setContentTitle("Synapse selesai")
            .setContentText(judul)
            .setStyle(NotificationCompat.BigTextStyle().bigText(potong))
            .setColor(0xFF2E7D32.toInt())
            .setAutoCancel(true)
            .setContentIntent(buka)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .addAction(0, "Buka", buka)
            .build()
    }

    /** FASE 3 — gagal. */
    private fun notifGagal(judul: String, pesan: String): Notification {
        val buka = PendingIntent.getActivity(
            this, 2, Intent(this, MainActivity::class.java),
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)

        return NotificationCompat.Builder(this, CH_ERROR)
            .setSmallIcon(R.drawable.ic_stat_synapse)
            .setContentTitle("Synapse gagal")
            .setContentText(pesan)
            .setStyle(NotificationCompat.BigTextStyle().bigText("$judul\n\n$pesan"))
            .setColor(0xFFC62828.toInt())
            .setAutoCancel(true)
            .setContentIntent(buka)
            .setPriority(NotificationCompat.PRIORITY_HIGH)
            .build()
    }
}
