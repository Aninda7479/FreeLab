import os

filepath = r"d:\Project\FreeLab\.github\workflows\build-android.yml"

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
        
    - name: Setup Gradle 8.4
      uses: gradle/actions/setup-gradle@v3
      with:
        gradle-version: '8.4'
        cache-disabled: true
        
    - name: Build with Gradle
      working-directory: ./ScreenTime/AndroidApp
      run: gradle assembleDebug
      
    - name: Upload APK
      uses: actions/upload-artifact@v4
      with:
        name: app-debug
        path: ScreenTime/AndroidApp/app/build/outputs/apk/debug/app-debug.apk
"""

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(workflow_yaml.strip())

print("Workflow updated for Gradle 8.4.")
