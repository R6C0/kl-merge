@echo off
rem Tests klnr.exe, the 64-bit helper that runs OpenDLSS-NR's network, on this PC WITHOUT starting the game
rem (about a minute; the game and Steam are not touched). Everything is logged to KLNR\selftest.log (new each run),
rem and the verdicts (RESULT lines) are shown at the end.
rem   1. can this GPU / driver run the network at all (--info)
rem   2. a frame's round trip without a model (must come back unchanged)
rem   3. the test pattern (right half grey)
rem   4. the full network with synthetic zero weights: its real cost per frame at 1080p and 1440p (no NVIDIA data)
rem   5. a 32-bit stand-in for the game moving frames through the bridge
cd /d "%~dp0"
if exist KLNR\selftest.log del KLNR\selftest.log
set "LOG=--log KLNR\selftest.log"
echo == 1. GPU check
KLNR\klnr.exe --info %LOG%
echo == 2. round trip without a model, 1920x1080
KLNR\klnr.exe --selftest --model none --size 1920x1080 --frames 60 --out KLNR\selftest_none.ppm %LOG%
echo == 3. test pattern
KLNR\klnr.exe --selftest --model none --size 1280x720 --frames 5 --test --out KLNR\selftest_test.ppm %LOG%
echo == 4. network cost with synthetic zero weights, 1920x1080 and 2560x1440
KLNR\klnr.exe --selftest --model zero --size 1920x1080 --frames 60 --out KLNR\selftest_zero.ppm %LOG%
KLNR\klnr.exe --selftest --model zero --size 2560x1440 --frames 40 --out KLNR\selftest_zero_1440.ppm %LOG%
echo == 5. 32-bit stand-in game through the bridge
KLNR\klnr_harness32.exe --model none --size 1280x720 --frames 30 --test > KLNR\selftest_harness32.txt 2>&1
type KLNR\selftest_harness32.txt
echo.
echo ================ results ================
findstr /c:"RESULT " KLNR\selftest.log
findstr /b /c:"PASS" /c:"FAIL" KLNR\selftest_harness32.txt
echo Full log: KLNR\selftest.log
if /i not "%~1"=="nopause" pause
