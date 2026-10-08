D="/mnt/user-data/uploads/Kane and Lynch Dead Men/KL_PortTools/build/dbg/latest.mdmp"
P="/mnt/user-data/uploads/Kane and Lynch Dead Men/KL_PortTools/build/dbg/$1"
cd /home/claude/dbg
python3 dump.py "$D" 2>&1 | sed -n '1,2p;/<==/p;/^stack/,$p' | head -14
EIP=$(python3 dump.py "$D" 2>/dev/null | head -1 | grep -o "at 0x[0-9a-f]*" | cut -c4-)
python3 rtti.py $EIP
python3 buf.py "$D" | tail -1 | cut -c1-200
POS=$(python3 buf.py "$D" | tail -1 | cut -d' ' -f1)
python3 locate.py "$P" /tmp/streambuf2.bin $POS
