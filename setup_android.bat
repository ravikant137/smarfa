@echo off
echo ========================================
echo  Android Studio Setup for React Native
echo ========================================
echo.

echo IMPORTANT: This script will help you set up Android development.
echo You need to manually download and install Android Studio first.
echo.

echo Step 1: Download Android Studio
echo -------------------------------
echo 1. Go to: https://developer.android.com/studio
echo 2. Download the Windows version
echo 3. Run the installer and complete setup
echo 4. Open Android Studio and install SDK components
echo.

pause

echo.
echo Step 2: Verify Android SDK installation
echo ----------------------------------------

set /p ANDROID_HOME="Enter Android SDK location (usually C:\Users\%USERNAME%\AppData\Local\Android\Sdk): "
if "%ANDROID_HOME%"=="" set ANDROID_HOME=C:\Users\%USERNAME%\AppData\Local\Android\Sdk

if exist "%ANDROID_HOME%" (
    echo Android SDK found at: %ANDROID_HOME%
) else (
    echo Android SDK not found at: %ANDROID_HOME%
    echo Please check the path and try again.
    pause
    exit /b 1
)

echo.
echo Step 3: Setting environment variables...
setx ANDROID_HOME "%ANDROID_HOME%" /M

echo Adding Android tools to PATH...
for /f "tokens=*" %%i in ('powershell -command "[Environment]::GetEnvironmentVariable('PATH', 'Machine')"') do set CURRENT_PATH=%%i
setx PATH "%CURRENT_PATH%;%ANDROID_HOME%\platform-tools;%ANDROID_HOME%\emulator;%ANDROID_HOME%\tools;%ANDROID_HOME%\tools\bin" /M

echo.
echo Step 4: Create Android Virtual Device
echo -------------------------------------
echo 1. Open Android Studio
echo 2. Go to Tools ^> Device Manager
echo 3. Click "Create device"
echo 4. Select a device (e.g., Pixel 6)
echo 5. Select system image (API 33 or higher)
echo 6. Complete the setup
echo.

echo Setup complete! Restart your command prompt and try:
echo cd mobile-app
echo npx expo start --android
echo.

pause