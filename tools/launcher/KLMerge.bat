@echo off
rem KLMerge.bat - starts the KL Merge launcher window (KLMergeLauncher.ps1) without touching the
rem machine's PowerShell execution policy. Run "KLMerge Setup.bat" first (it fetches the package).
rem -STA is needed for WPF and for the folder picker dialog.
cd /d "%~dp0"
start "" powershell -NoProfile -ExecutionPolicy Bypass -STA -WindowStyle Hidden -File "%~dp0KLMergeLauncher.ps1" %*
