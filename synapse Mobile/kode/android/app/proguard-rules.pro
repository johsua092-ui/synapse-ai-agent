# ============================================================
# ProGuard/R8 keep rules — AMAN untuk Synapse Mobile
# Dibuat hati-hati: semua yang dipakai refleksi/native DIPERTAHANKAN
# ============================================================

# ---- Flutter ----
-keep class io.flutter.** { *; }
-keep class io.flutter.plugins.** { *; }
-dontwarn io.flutter.**

# ---- Kotlin ----
-keep class kotlin.** { *; }
-keep class kotlinx.** { *; }
-dontwarn kotlin.**
-dontwarn kotlinx.**

# ---- AndroidX / Compose ----
-keep class androidx.** { *; }
-dontwarn androidx.**

# ---- Kotlin Serialization / Reflect ----
-keepattributes *Annotation*, InnerClasses, Signature, EnclosingMethod
-keepclassmembers class * {
    @androidx.annotation.Keep *;
}

# ---- Plugin Synapse Mobile (WAJIB, dipakai MethodChannel) ----
# MainActivity + TaskService dipanggil dari native/Flutter lewat nama kelas
-keep class com.nousresearch.synapse_mobile.** { *; }
-keepclassmembers class com.nousresearch.synapse_mobile.** { *; }

# ---- Plugin Flutter (semua pakai refleksi) ----
-keep class com.baseflow.** { *; }
-keep class com.tekartik.** { *; }
-keep class com.flutter.** { *; }
-keep class dev.fluttercommunity.** { *; }
-keep class com.google.android.** { *; }
-keep class com.llfbandit.** { *; }
-keep class net.gotev.** { *; }
-keep class xyz.luan.** { *; }
-keep class com.it_nomads.** { *; }
-keep class com.csdcorp.** { *; }

# ---- WebView (Live2D) ----
-keep class android.webkit.** { *; }
-keepclassmembers class * extends android.webkit.WebViewClient { *; }
-keepclassmembers class * extends android.webkit.WebChromeClient { *; }

# ---- JS Interface (kalau ada) ----
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

# ---- TTS / Speech ----
-keep class android.speech.** { *; }
-keep class com.google.android.tts.** { *; }

# ---- Gson/JSON (kalau dipakai plugin) ----
-keep class com.google.gson.** { *; }
-keepclassmembers class * {
    @com.google.gson.annotations.SerializedName <fields>;
}

# ---- Jangan hapus kelas yang dipakai enum/parcelable ----
-keepclassmembers enum * {
    public static **[] values();
    public static ** valueOf(java.lang.String);
}
-keep class * implements android.os.Parcelable {
    public static final android.os.Parcelable$Creator *;
}

# ---- Abaikan warning pustaka opsional ----
-dontwarn org.jetbrains.annotations.**
-dontwarn javax.annotation.**
-dontwarn org.conscrypt.**
-dontwarn org.bouncycastle.**
-dontwarn org.openjsse.**
-dontwarn com.google.errorprone.annotations.**
-dontwarn java.lang.invoke.**
-dontwarn kotlin.**
