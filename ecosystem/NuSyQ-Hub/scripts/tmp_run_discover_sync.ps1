$python = "C:\\Users\\keath\\AppData\\Local\\Programs\\Python\\Python312\\python.exe"
$script = "C:\\Users\\keath\\Desktop\\Legacy\\NuSyQ-Hub\\scripts\\discover_and_sync_models.py"
$logOut = "C:\\Users\\keath\\Desktop\\Legacy\\NuSyQ-Hub\\logs\\discover_sync.out.log"
$logErr = "C:\\Users\\keath\\Desktop\\Legacy\\NuSyQ-Hub\\logs\\discover_sync.err.log"
Start-Process -FilePath $python -ArgumentList $script, '--discover','--query-apis','--sync','--apply','--verbose' -RedirectStandardOutput $logOut -RedirectStandardError $logErr -Wait
