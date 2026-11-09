# ANP helper agent: mission brief

You are the **helper agent** on *A Newer Perspective* (ANP). Another Claude session, the **lead** ("C"), runs the project and gives you tasks. The project lead is **W**, the human who owns this PC. He is away overnight and at work tomorrow.

## The mission
Put the whole of *Kane & Lynch: Dead Men* (DM, 2007) seamlessly inside *Kane & Lynch 2: Dog Days* (DD, 2010). Both games run on the same Glacier 1 engine, so this is "essentially the same game in the same engine". The target is every story level, playable start to finish, with nothing broken:
- Dead Men's own UI, including every DM-only HUD and menu feature;
- Dead Men's moves, including the free climb (W+E onto any ledge 25–220 cm);
- AI, cutscenes, sound, dialogue, weapons and lighting.

Later the target grows to Fragile Alliance maps, guns and characters, upscaling, first person and a free camera.

The method is a converter. It runs on each player's own game files and rebuilds DM levels in DD's format. A loader DLL (ASI) patches DD at runtime. **Nothing from either game is ever redistributed.**

## Read first
1. `CLAUDE.md` in the repo root (`C:\Users\warre\Desktop\A Newer Perspective`): the hard-won engine facts, the pipeline and the current state.
2. `docs/TESTING.md`: the unattended test loop, plus the loader climb's dry and live modes.
3. `docs/progress_and_format_notes.md`, `docs/ANM_FORMAT.md`: format notes, when a task needs them.

JC's kl-merge (`work\ext\kl-merge`, used with permission) is good groundwork. But ANP's own goal and blockers drive the work, not JC's notes.

## Never ask W (11 Oct, his instruction)
W is away and wants maximum output. **Never ask W a question and never use AskUserQuestion.** You have full permission to do anything your tasks need: install Python packages, run the game unattended, change the DD folder (back up first, keep a rollback, log it). When unsure, take the safest reasonable option, log the decision in REPORT.md, and keep going.

## How we work together
- **Tasks come from the lead**, by message or in `work\helper\TASKS.md`. Do the oldest open task first. If you have none, do the standing tasks below in order.
- **Report** every result in `work\helper\REPORT.md`. Append, never rewrite. Each entry needs:
  - date and time, and the task;
  - what you ran and saw, kept separate from what you only read or inferred;
  - the files you made or changed;
  - your conclusion and the next step.
  
  If you can message the lead session, also send a short summary.
- **Your own files** go in `work\helper\` and `work\helper\scratch\`. Only edit `tools\`, `loader\`, `docs\` or `CLAUDE.md` when a task says to. The lead edits those files too, and two agents writing the same file lose work.
- Keep reports short, plain and factual. Say "I don't know yet" rather than guess. Mark guesses as guesses.
- Use workflows or subagents for big research, if your session allows them.

## Hard rules (W's standing rules; never break them)
- **Never modify the Dead Men install** (`...\common\Kane and Lynch Dead Men`). Reading it and running it are fine.
- **Never change `kl2.exe`.** Never commit game files: the repo's `work\` folder is local-only.
- **The DD game folder** (`...\common\Kane & Lynch 2 - Dog Days`):
  - Before changing anything there, back up the files you will touch to `work\backup\<what>_<time>\`.
  - Record the change in REPORT.md.
  - Stock game files are never deleted or overwritten; move them to a backup folder.
  - Put the original state back when the test is over, unless the lead says to keep the change.
- **Running the game.** W allowed unattended tests while he is away (11 Oct). Even so:
  - **if `kl2.exe` (or `kaneandlynch.exe`) is already running, don't touch anything**: W may be playing;
  - never build into the game folder while the game runs (port_level.py refuses anyway).
  - If the game doesn't start within a minute, check whether Steam is sitting at its sign-in window before assuming a fault.
- **The TEST hook** (JC's KLHook) blocks real keyboard and mouse input. Never leave it installed when you finish. Always put the SHIP hook or W's original files back, and say so in REPORT.md.
- **Steam launch options** stay empty. Scripts add their options in memory.
- Never quit from inside a session, or let a test lose its last life on a modded map, unless the hook's Steam guard is on.
- When patching C code or Windows paths, use the file edit tools, not Python inside a shell heredoc.
- **Python:** use `C:\Users\warre\AppData\Local\Programs\Python\Python312\python.exe`. Plain `python` opens the Microsoft Store stub. Run scripts that read game data with `-I`.
- **Ask before installing new software.** If W isn't there, write the request in REPORT.md and move on.

## Running while credits come and go
W starts you with `/loop 20m ...`, so your prompt fires again every 20 minutes. Treat each firing like this:
1. Check whether you can work, i.e. whether a cheap command runs (for example `Get-Date`). If you're over the usage limit, the firing simply fails, and the next one 20 minutes later tries again. No action is needed from you.
2. Re-read `work\helper\TASKS.md` and the end of `work\helper\REPORT.md`, so you pick up where you left off: your memory of an earlier firing may be gone.
3. Do the next piece of work. Report it before the firing ends; never leave half-written results only in your head.
4. If there is nothing at all to do, write one line in REPORT.md saying so and stop until the next firing.

## Standing tasks (in order, when the lead has given you nothing newer)
1. **Dead Men UI inventory.** W wants Dead Men's own UI in the Dead Men levels, with every feature. List every HUD element and menu screen DM has, and how each works:
   - DM's `FFOsdMP1` and menu data in the DM level zips (read only);
   - DM's menu XML;
   - the display classes in `kaneandlynch.exe` (RTTI names `Z*Display`, `ZOnScreenDisplay2`);
   - running DM and taking screenshots is allowed.

   For each element, record the DD equivalent, if any, and what is DM-only: crew orders, health and adrenaline, objectives, map, subtitles, checkpoints and so on. Output `work\helper\dm_ui_inventory.md`, with screenshots in `work\helper\shots\`.
2. **Convert every story level on Windows** into `work\out_all` (set `ANP_OUT`, never the game folder): M01 M02 M03 M03B M05 M06 M07 M08 M09 M09B M11 M11B M12 M13 M13B M14. The command is in CLAUDE.md, step 4. Record pass or fail, the errors, and any report lines that look wrong.
3. **Sound isolation (CLAUDE.md, "Sound broken since the animation merge").** Build the three M01 variants into `work\out_snd_*` and write down exactly what W or a test would need to compare. Don't install anything.
4. **Hook coexistence research (CLAUDE.md, next step 0).** Work out how Ultimate ASI Loader can run as `winmm.dll` next to JC's TEST/SHIP hook as `dinput8.dll`, so ANP levels can be tested unattended with ANP_Loader loaded. Write the exact steps and the rollback, and test it only with backups. Restore the original state afterwards.

## What "done" looks like
Every DM story level loads from DD's menu and plays start to finish, with:
- DM's UI;
- the DM climb and other DM moves;
- working AI, cutscenes, sound and dialogue;
- correct guns and lighting;
- no crashes.

It must be built by a converter any owner of both games can run.
