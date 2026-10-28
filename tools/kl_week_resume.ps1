# Scheduled resume for the owner's away week (2026-10-28 ..): starts a headless Claude Code session that continues
# re/week_plan_1028.md when no other session is active (e.g. after the usage limit resets).
# Run by the Windows task "KLMerge Resume" (every 2 h). Safe to run by hand: it exits at once if a session is live.
param([int]$FreshMin = 40, [int]$MaxHours = 4)

$proj   = Join-Path $env:USERPROFILE '.claude\projects\c--kl-merge-kl-merge'
$logDir = 'G:\SteamLibrary\steamapps\common\Kane and Lynch Dead Men\KL_PortTools\week_resume'
New-Item -ItemType Directory -Force $logDir | Out-Null
$stamp  = Get-Date -Format 'yyyyMMdd_HHmm'
$log    = Join-Path $logDir "resume_$stamp.log"
$lock   = Join-Path $logDir 'resume.lock'

function Note([string]$s) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $s" | Out-File -Append -Encoding utf8 (Join-Path $logDir 'resume_index.log') }

# A previous resume still running?
if (Test-Path $lock) {
    $old = Get-Content $lock -ErrorAction SilentlyContinue
    if ($old -and (Get-Process -Id $old -ErrorAction SilentlyContinue)) { Note "skip: resume pid $old still running"; exit 0 }
}
# Any live session (this chat, peers, a resume) writes its transcript; a fresh one means work is going on.
$fresh = Get-ChildItem $proj -Filter *.jsonl -Recurse -ErrorAction SilentlyContinue |
         Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-$FreshMin) }
if ($fresh) { Note "skip: $($fresh.Count) transcript(s) written in the last $FreshMin min"; exit 0 }

$prompt = @'
Scheduled resume (owner away, full access, never ask; see memory full-access-week-1028). Work in the worktree C:\kl-merge\wt\round-1027
(git pull --rebase origin rtp-schemas first). Read re/week_plan_1028.md and the top of re/open_work_log.md, use ListAgents to see which
peer sessions are live and message them before taking a claimed track. Take the most valuable open item, do it fully (build, verify,
idle-gated live bench when the owner is idle 5 min, fix, commit + push rtp-schemas), update the plan file, CLAUDE.md Open work and
re/open_work_log.md, then the next item. Stop after about 3 hours of work with everything committed and the notes current.
'@

$claude = (Get-Command claude -ErrorAction SilentlyContinue).Source
if (-not $claude) { Note 'fail: claude CLI not on PATH'; exit 1 }
Note "start: log $log"
$p = Start-Process -FilePath $claude -ArgumentList @('-p', ('"' + $prompt.Replace('"', "'") + '"'), '--permission-mode', 'auto') `
     -WorkingDirectory 'C:\kl-merge\kl-merge' -RedirectStandardOutput $log -RedirectStandardError "$log.err" -PassThru -WindowStyle Hidden
$p.Id | Out-File -Encoding ascii $lock
if (-not $p.WaitForExit($MaxHours * 3600 * 1000)) { Stop-Process -Id $p.Id -Force; Note "killed after $MaxHours h: pid $($p.Id)" }
else { Note "done: exit $($p.ExitCode)" }
Remove-Item $lock -ErrorAction SilentlyContinue
