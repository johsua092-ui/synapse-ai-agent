plugins {
    id("com.android.application")
    // The Flutter Gradle Plugin must be applied after the Android and Kotlin Gradle plugins.
    id("dev.flutter.flutter-gradle-plugin")
}

// Kredensial penandatangan dibaca dari android/key.properties
// (file itu TIDAK di-commit — lihat .gitignore)
val kpFile = rootProject.file("key.properties")
val kp = mutableMapOf<String, String>()
if (kpFile.exists()) {
    kpFile.readLines().forEach { baris ->
        val i = baris.indexOf('=')
        if (i > 0) kp[baris.substring(0, i).trim()] = baris.substring(i + 1).trim()
    }
}

android {
    namespace = "com.nousresearch.synapse_mobile"
    compileSdk = 36
    ndkVersion = flutter.ndkVersion

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    defaultConfig {
        // TODO: Specify your own unique Application ID (https://developer.android.com/studio/build/application-id.html).
        applicationId = "com.nousresearch.synapse_mobile"
        // You can update the following values to match your application needs.
        // For more information, see: https://flutter.dev/to/review-gradle-config.
        minSdk = flutter.minSdkVersion
        targetSdk = 36
        // Uses the version code from pubspec.yaml. When using split APKs, 1000 * ABI_VERSION
        // is added automatically by Flutter. (https://developer.android.com/studio/build/configure-apk-splits#configure-APK-versions)
        // You can force using the value of versionCode by specifying the `-P force-version-code-ignoring-abi=true`
        // flag during build.
        versionCode = 2100
        versionName = "0.6.0"
    }

    signingConfigs {
        create("release") {
            keyAlias = kp["keyAlias"] ?: "synapse"
            keyPassword = kp["keyPassword"] ?: ""
            storeFile = file(kp["storeFile"] ?: "../synapse-release.jks")
            storePassword = kp["storePassword"] ?: ""
        }
    }

    buildTypes {
        release {
            // Ditandatangani dengan keystore resmi Synapse (bukan debug).
            signingConfig = signingConfigs.getByName("release")
            isMinifyEnabled = false
            isShrinkResources = false
        }
    }
}

kotlin {
    compilerOptions {
        jvmTarget = org.jetbrains.kotlin.gradle.dsl.JvmTarget.JVM_17
    }
}

flutter {
    source = "../.."
}
