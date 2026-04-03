@echo off
echo Checking Android development setup...
echo.

echo 1. Checking Java...
java -version
if %errorlevel% neq 0 (
    echo ERROR: Java not found. Please install JDK 11 or higher.
    pause
    exit /b 1
)

echo.
echo 2. Checking Android SDK...
if "%ANDROID_HOME%"=="" (
    echo WARNING: ANDROID_HOME not set
) else (
    echo ANDROID_HOME: %ANDROID_HOME%
    if exist "%ANDROID_HOME%" (
        echo Android SDK found ✓
    ) else (
        echo ERROR: Android SDK not found at %ANDROID_HOME%
    )
)

echo.
echo 3. Checking ADB...
adb version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: ADB not found in PATH
) else (
    echo ADB found ✓
)

echo.
echo 4. Checking Android emulator...
emulator -version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: Android emulator not found in PATH
) else (
    echo Android emulator found ✓
)

echo.
echo If any components are missing, run setup_android.bat
echo.

pause