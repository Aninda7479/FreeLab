import os
import subprocess

workspace_dir = r"d:\Project\FreeLab\ScreenTime"
freelab_dir = r"d:\Project\FreeLab"
android_dir = os.path.join(workspace_dir, "AndroidApp")

# 1. Android Scaffolding
settings_gradle = """
pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "ScreenTimeSync"
include ':app'
"""

app_build_gradle = """
plugins {
    id 'com.android.application'
    id 'org.jetbrains.kotlin.android'
}

android {
    namespace 'com.screentime.tracker'
    compileSdk 34

    defaultConfig {
        applicationId "com.screentime.tracker"
        minSdk 26
        targetSdk 34
        versionCode 1
        versionName "1.0"
    }

    buildTypes {
        release {
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
        }
    }
    compileOptions {
        sourceCompatibility JavaVersion.VERSION_17
        targetCompatibility JavaVersion.VERSION_17
    }
    kotlinOptions {
        jvmTarget = '17'
    }
}

dependencies {
    implementation 'androidx.core:core-ktx:1.12.0'
    implementation 'androidx.appcompat:appcompat:1.6.1'
    implementation 'com.google.android.material:material:1.11.0'
    implementation 'androidx.constraintlayout:constraintlayout:2.1.4'
}
"""

main_activity = """
package com.screentime.tracker

import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        // Ensure NsdHelper or UsageTracker is started here if needed.
    }
}
"""

def write_f(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip())

write_f(os.path.join(android_dir, 'settings.gradle'), settings_gradle)
write_f(os.path.join(android_dir, 'app', 'build.gradle'), app_build_gradle)
write_f(os.path.join(android_dir, 'app', 'src', 'main', 'java', 'com', 'screentime', 'tracker', 'MainActivity.kt'), main_activity)

# Optional string/theme
write_f(os.path.join(android_dir, 'app', 'src', 'main', 'res', 'values', 'strings.xml'), '<resources><string name="app_name">ScreenTimeSync</string></resources>')
write_f(os.path.join(android_dir, 'app', 'src', 'main', 'res', 'values', 'themes.xml'), '<resources><style name="Theme.ScreenTimeSync" parent="Theme.MaterialComponents.DayNight.NoActionBar"></style></resources>')

# 2. GitHub Actions YAML
workflow_yaml = """
name: Build Android APK

on:
  push:
    branches: [ main, master ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: set up JDK 17
      uses: actions/setup-java@v3
      with:
        java-version: '17'
        distribution: 'temurin'
        
    - name: Build with Gradle
      working-directory: ./ScreenTime/AndroidApp
      run: gradle assembleDebug
      
    - name: Upload APK
      uses: actions/upload-artifact@v4
      with:
        name: app-debug
        path: ScreenTime/AndroidApp/app/build/outputs/apk/debug/app-debug.apk
"""

write_f(os.path.join(freelab_dir, '.github', 'workflows', 'build-android.yml'), workflow_yaml)

print("Scaffolding complete.")
