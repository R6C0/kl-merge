@echo off
rem Tests klnr.exe, the 64-bit helper that runs OpenDLSS-NR's network, on this PC WITHOUT starting the game
rem (about a minute; the game and Steam are not touched). Everything is logged to KLNR\klnr.log.
rem   1. can this GPU / driver run the network at all (--info)
rem   2. a frame's round trip without a model (must come back unchanged)
rem   3. the test pattern (right half grey)
rem   4. the full network with synthetic zero weights: its real cost per frame at 1080p and 1440p (no NVIDIA data)
rem   5. a 32-bit stand-in for the game moving frames through the bridge
cd /d "%~dp0"
echo == 1. GPU check
KLNR\klnr.exe --info
echo == 2. round trip without a model, 1920x1080
KLNR\klnr.exe --selftest --model none --size 1920x1080 --frames 60 --out KLNR\selftest_none.ppm
echo == 3. test pattern
KLNR\klnr.exe --selftest --model none --size 1280x720 --frames 5 --test --out KLNR\selftest_test.ppm
echo == 4. network cost with synthetic zero weights, 1920x1080 and 2560x1440
KLNR\klnr.exe --selftest --model zero --size 1920x1080 --frames 60 --out KLNR\selftest_zero.ppm
KLNR\klnr.exe --selftest --model zero --size 2560x1440 --frames 40 --out KLNR\selftest_zero_1440.ppm
echo == 5. 32-bit stand-in game through the bridge
KLNR\klnr_harness32.exe --model none --size 1280x720 --frames 30 --test
echo.
echo Done. Results: KLNR\klnr.log
if /i not "%~1"=="nopause" pause
