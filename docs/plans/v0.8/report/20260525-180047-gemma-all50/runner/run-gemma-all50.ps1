$ErrorActionPreference = 'Continue'
Set-Location 'D:\work\codegopher'
$env:OPENAI_API_KEY = 'dummy-key'
& 'D:\work\codegopher\.venv\Scripts\python.exe' -m codegopher.devtools.benchmark `
  --suite 'D:\work\codegopher\docs\plans\v0.8\report\20260525-180047-gemma-all50\runner\secure-code-hunt-all50-suite.toml' `
  --output-dir 'D:\work\codegopher\docs\plans\v0.8\report\20260525-180047-gemma-all50' `
  --cgopher 'D:\work\codegopher\.venv\Scripts\cgopher.exe' `
  --model 'google/gemma-4-26B-A4B-it:deepinfra' `
  --base-url 'http://192.168.96.5:8080/v1' `
  --api-family chat_completions `
  --api-key-env OPENAI_API_KEY `
  --api-key-value dummy-key `
  --replay-reasoning-content `
  --sanitize-source-hints `
  --timeout-seconds 900 `
  --retries 1 `
  --temp-root 'C:\Users\shamit\AppData\Local\Temp\codegopher-v08-chain-20260525-180047-gemma-all50' `
  --previous-report 'D:\work\codegopher\docs\plans\v0.8\report\20260524-234855-all50\REPORT.md' `
  1> 'D:\work\codegopher\docs\plans\v0.8\report\20260525-180047-gemma-all50\runner\benchmark.out.log' 2> 'D:\work\codegopher\docs\plans\v0.8\report\20260525-180047-gemma-all50\runner\benchmark.err.log'
$LASTEXITCODE | Set-Content -Path 'D:\work\codegopher\docs\plans\v0.8\report\20260525-180047-gemma-all50\runner\exit-code.txt' -Encoding UTF8
