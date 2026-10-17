# Gun sounds from the owner's recordings (2026-10-16/17)

Scripts that built the Dead Men maps' gun banks installed on the owner's PC (no audio is in git).
- `make_ref.py`: cuts the owner's reference recordings (KL_PortTools/build/snd5/ref) into shot clips.
- `make_v6.py`: the current set: MP5 / P90 (MP7) / M4 from his recordings, TMP = the game's original, USP = Dead Men's own Shot_Usp.
- `build_long.py`: writes the banks with clips at their NATURAL length (longer records appended to the .WAV, the .SND wave
  seconds updated inside the zip) - the stock-length fit cut the tails off.
- `make_snake.py`: an earlier set from Snake's Authentic Gun Sounds (itch.io, free, credit not needed).
Owner's choices: clean recordings, full tails, no distortion; each clip must START on the bang (in auto fire only the first
~70 ms of a clip is heard). MP5 now = his SP5A3 single (sp5_a) from its own start, three pitches (1.00 / 1.02 / 0.98).
Paths in the scripts are the VM's (~/mnt/...). Backups on his game: *.before-sndN beside each map's files (N = 2..11).
