@echo off
rem KLMerge.bat - starts the KL Merge launcher window (KLMergeLauncher.ps1) without touching the
rem machine's PowerShell execution policy. Run "KLMerge Setup.bat" first (it fetches the package).
rem -STA is needed for WPF and for the folder picker dialog.
rem
rem WINDOWS DEFENDER (2026-11-09): a .bat that runs powershell with "-WindowStyle Hidden" plus
rem "-ExecutionPolicy Bypass" matches a heuristic (Trojan:Win32/Ceprolad.A was raised on a helper
rem .bat of the owner's with exactly that line). So the console is started MINIMIZED (start /min),
rem not hidden: it sits in the taskbar while the launcher window is open, and nothing here hides
rem anything. Everything that runs is plain text in this folder (this file, KLMergeLauncher.ps1).
cd /d "%~dp0"
start "KL Merge" /min powershell -NoProfile -ExecutionPolicy Bypass -STA -File "%~dp0KLMergeLauncher.ps1" %*
