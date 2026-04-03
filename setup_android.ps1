@echo off
echo Setting up Android Studio for React Native development...
echo.

echo Step 1: Downloading Android Studio...
echo Please download Android Studio from: https://developer.android.com/studio
echo Choose the Windows version and run the installer.
echo.
echo After installation, please run this script again to continue setup.
pause

echo.
echo Step 2: Setting up Android SDK...
echo After Android Studio installation, open it and complete the setup wizard.
echo Make sure to install Android SDK, Android SDK Platform, and Android Virtual Device.
echo.
echo Step 3: Setting environment variables...
echo We need to add Android SDK to PATH.
echo.

set /p ANDROID_HOME="Enter Android SDK location (usually C:\Users\%USERNAME%\AppData\Local\Android\Sdk): "
if "%ANDROID_HOME%"=="" set ANDROID_HOME=C:\Users\%USERNAME%\AppData\Local\Android\Sdk

echo Setting ANDROID_HOME to %ANDROID_HOME%
setx ANDROID_HOME "%ANDROID_HOME%" /M

echo Adding Android tools to PATH...
set "PATH=%PATH%;%ANDROID_HOME%\platform-tools;%ANDROID_HOME%\tools;%ANDROID_HOME%\tools\bin"
setx PATH "%PATH%;%ANDROID_HOME%\platform-tools;%ANDROID_HOME%\tools;%ANDROID_HOME%\tools\bin" /M

echo.
echo Step 4: Creating Android Virtual Device (AVD)...
echo Open Android Studio ^> AVD Manager ^> Create Virtual Device
echo Select a device (e.g., Pixel 6) and API level 33 or higher.
echo.

echo Setup complete! You can now run the app on Android emulator.
echo Use: npx expo start --android
pause