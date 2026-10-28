# AnyDesk: run this PC from her PC, with Claude left running (prep 2026-10-28)

Goal: from her PC (Thursday evening on), see and drive this PC (the owner's, where the game, VS Code and the Claude
chats run), so the Claude sessions keep working here and the owner can check on them or type a prompt.

## Already checked on this PC (10-28 11:50)
- Power plan "High performance": sleep and hibernate are already Never (AC and DC). Nothing to change.
- AnyDesk is NOT installed yet. Not installed by Claude on purpose: unattended access needs a password only the owner
  should choose and know.
- Windows task "KLMerge Resume" (every 2 h until 11-04) and the Claude Desktop routine (every 4 h) keep the work going
  even when nobody is connected.

## This PC (do once, ~5 min; can be done now or from her place if someone is home to click)
1. Download AnyDesk from https://anydesk.com/en/downloads/windows (official site only) and run it.
2. Click "Install AnyDesk on this device"; tick "Start AnyDesk with Windows". Finish.
3. Settings > Security > unlock > "Unattended Access": enable it and set a long password (write it down somewhere safe,
   not in this repo). Keep "Allow control of keyboard and mouse" on.
4. Note this PC's 9- or 10-digit AnyDesk address (main window, "This Desk").
5. Windows: Settings > Accounts > Sign-in options: if the PC reboots for updates it must reach the desktop for the
   Claude chats; either keep it signed in (do not log off, only lock) or pause Windows Update for a week
   (Settings > Windows Update > Pause updates for 7 days). Pausing is the simpler choice this week.
6. Leave VS Code with the Claude chats open, Steam signed in (a Steam sign-in window blocks live game runs), monitor may
   be off (runs then use 640x480; that is expected).

## Her PC (Thursday)
1. Install AnyDesk the same way (a plain run without install is also fine for occasional use).
2. Enter this PC's AnyDesk address, connect, type the unattended password. Tick "Log in automatically from now on"
   only if her PC is private.
3. To talk to Claude: switch to the VS Code window and type into the chat, or use the Claude app on her PC / phone
   (status page: https://claude.ai/artifact/Pp48g1cQgREDE3AsHPqxTa).

## While connected (important)
- Your mouse and keyboard over AnyDesk count as "owner input" for the test benches: a live bench aborts with
  "owner input" and reruns later. If you only want to look, use AnyDesk's view-only toggle (toolbar, "Allow input" off).
- Do not close the game window while a bench runs (title shows Kane & Lynch 2); the bench result line lands in
  `C:\kl_build_1024\...\*_run.txt`.
- Closing the AnyDesk window does not stop anything on this PC.

## Security
- Only the owner knows the unattended password. Never paste it into a Claude chat or the repo.
- In AnyDesk Settings > Security you can restrict access to her AnyDesk ID only ("Access control list").
