@echo off
echo ========================================
echo Setting up PATH for Development Tools
echo ========================================
echo.

REM Get current user PATH
setx PATH "%PATH%;C:\Program Files\Git\cmd;C:\Program Files\Docker\Docker\resources\bin;C:\Program Files\Nodejs;C:\Program Files\Rust\bin;C:\Program Files\Go\bin;C:\Program Files\dotnet;C:\Program Files\Java\jdk-*\bin;C:\Program Files\Apache\Maven\bin;C:\Program Files\Gradle\bin;C:\Users\zqmco\scoop\shims;C:\ProgramData\chocolatey\bin" /M

echo.
echo PATH updated successfully!
echo.
echo NOTE: You may need to restart your terminal or computer for changes to take effect.
echo.
pause