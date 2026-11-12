# Rebuild all 16 DM story levels with the current converter into work\<out> (default out_all6). Logs in work\<out>\_logs.
# The funeral (M07F, Dead Men's CutScenes\M07\M07_A_Funeral between M07 and M08) is built first into the same tree
# (work\<out>\CutScenes\M07\, next to work\<out>\M07\...), so M07's SceneChanger points at it (port_level.py
# ANP_SKIP_FUNERAL=auto looks in the build's own output tree). It installs to <DD>\Scenes\CutScenes\M07\ (NOT under
# Scenes\Locations) and must go in together with M07. -NoFuneral: the old run (no M07F; M07 then ends straight into M08
# unless a converted funeral is already in the Dog Days folder).
param([string]$Out = 'out_all6', [switch]$NoFuneral)
$repo = 'C:\Users\warre\Desktop\A Newer Perspective'; Set-Location $repo
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
$env:ANP_OUT = "work\$Out"; $env:ANP_SET = 'CameraFogBegin=0.25'
$logs = "work\$Out\_logs"; New-Item -ItemType Directory -Force $logs | Out-Null
$levels = 'M01','M02','M03','M03B','M05','M06','M07','M08','M09','M09B','M11','M11B','M12','M13','M13B','M14'
if (-not $NoFuneral) { $levels = 'M01','M02','M03','M03B','M05','M06','M07F','M07','M08','M09','M09B','M11','M11B','M12','M13','M13B','M14' }
# -NoFuneral: a funeral left in this tree by an earlier run must not make M07 point at it (ANP_SKIP_FUNERAL=auto)
if ($NoFuneral) { Remove-Item -Recurse -Force "work\$Out\CutScenes\M07" -ErrorAction SilentlyContinue }
foreach ($L in $levels) {
    $t0 = Get-Date
    if ($L -eq 'M07F') {
        # stale copy from an earlier run must not make M07 point at it when this build fails
        Remove-Item -Recurse -Force "work\$Out\CutScenes\M07" -ErrorAction SilentlyContinue
        & $py tools\port_level.py M07F *> "$logs\$L.log"
        # a failed build can leave part of the scene behind: remove it, so M07 ends straight into M08
        if ($LASTEXITCODE -ne 0) { Remove-Item -Recurse -Force "work\$Out\CutScenes\M07" -ErrorAction SilentlyContinue }
    } else {
        $b = $L.Substring(0,3); $s = $L.Substring(3); if (-not $s) { $s = 'A' }
        & $py tools\port_level.py "${b}_$s" "$b$s" $L *> "$logs\$L.log"
    }
    "$L rc=$LASTEXITCODE $([int]((Get-Date) - $t0).TotalSeconds)s" | Tee-Object -Append "$logs\summary.txt"
}
if (-not $NoFuneral) {
    $sc = Select-String -Path "$logs\M07.log" -Pattern 'SceneChanger node' | ForEach-Object { $_.Line.Trim() }
    "M07 chain: $sc" | Tee-Object -Append "$logs\summary.txt"
}
'DONE' | Tee-Object -Append "$logs\summary.txt"
