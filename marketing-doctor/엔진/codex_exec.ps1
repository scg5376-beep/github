# codex exec 를 클로드 도구 세션의 자식이 아니라 분리된 프로세스로 띄운다 (2026-09-11 확인: MCP 가 끊겨도 이 길은 된다).
# 사용: powershell -File codex_exec.ps1 -PromptFile 프롬프트.md -WorkDir 산출폴더 [-Model gpt-5.6-luna] [-TimeoutSec 900]
param([string]$PromptFile, [string]$WorkDir, [string]$Model = "gpt-5.6-luna", [int]$TimeoutSec = 900, [string]$ExtraArgs = "")
$log = Join-Path $WorkDir "codex_log.txt"; $last = Join-Path $WorkDir "codex_last.md"
$prompt = Get-Content $PromptFile -Raw -Encoding UTF8
$tmp = Join-Path $env:TEMP ("codex_prompt_" + [guid]::NewGuid().ToString("N") + ".txt"); Set-Content -Path $tmp -Value $prompt -Encoding UTF8
$args = "/c type `"$tmp`" | codex exec --skip-git-repo-check -m $Model -s workspace-write -C `"$WorkDir`" --add-dir `"$env:USERPROFILE\.codex\generated_images`" -o `"$last`" $ExtraArgs - > `"$log`" 2>&1"
$p = Start-Process -FilePath "cmd.exe" -ArgumentList $args -WindowStyle Hidden -PassThru
if (-not $p.WaitForExit($TimeoutSec * 1000)) { $p.Kill(); "TIMEOUT" } else { "EXIT " + $p.ExitCode }
Get-Content $last -ErrorAction SilentlyContinue
