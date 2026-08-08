<#
    PC방을 떠나기 전에 실행 — 오늘 만든 환경을 USB로 백업한다.

    사용법:
        powershell -ExecutionPolicy Bypass -File scripts\backup_to_usb.ps1 -UsbDrive E:

    백업 대상
      - D:\ic\env        conda 환경 (Python 3.11 + Isaac Sim 5.1 + torch cu128)  ~15GB
      - %LOCALAPPDATA%\ov  Omniverse 셰이더 캐시 — 다음 첫 실행을 빠르게 한다   ~0.4GB

    pip 캐시(D:\ic\pipcache)는 백업하지 않는다. env 를 그대로 복원하므로 불필요하다.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$UsbDrive,

    [string]$EnvPath = 'D:\ic\env'
)

$ErrorActionPreference = 'Stop'

if (-not (Test-Path $UsbDrive)) { throw "USB 드라이브를 찾을 수 없다: $UsbDrive" }
if (-not (Test-Path $EnvPath))  { throw "conda 환경을 찾을 수 없다: $EnvPath" }

$dest = Join-Path $UsbDrive 'isaac-simready-backup'
New-Item -ItemType Directory -Force $dest | Out-Null

# --- 여유 공간 확인 -------------------------------------------------------
$needBytes = (Get-ChildItem $EnvPath -Recurse -File -ErrorAction SilentlyContinue |
              Measure-Object Length -Sum).Sum
$needGB = [math]::Round($needBytes / 1GB, 2)
$freeGB = [math]::Round((Get-PSDrive $UsbDrive.TrimEnd(':')).Free / 1GB, 2)

Write-Host "환경 크기: ${needGB}GB / USB 여유: ${freeGB}GB"
if ($freeGB -lt ($needGB + 1)) {
    throw "USB 공간이 부족하다. 최소 $([math]::Round($needGB + 1, 2))GB 필요."
}

# --- conda 환경 아카이브 --------------------------------------------------
# 무압축 tar 를 쓰는 이유 — Isaac Sim 파일 대부분이 이미 압축된 바이너리라
# 압축률이 거의 없고 시간만 몇 배로 든다. 작은 파일 수만 개를 개별 복사하는 것보다
# 단일 아카이브 전송이 USB에서 훨씬 빠르다.
$envTar = Join-Path $dest 'isaac_env.tar'
Write-Host "[1/3] conda 환경 아카이브 중 -> $envTar"
$sw = [Diagnostics.Stopwatch]::StartNew()
tar -cf $envTar -C (Split-Path $EnvPath -Parent) (Split-Path $EnvPath -Leaf)
$sw.Stop()
Write-Host ("      완료 ({0:N1}분)" -f $sw.Elapsed.TotalMinutes)

# --- 셰이더 캐시 ----------------------------------------------------------
$ovCache = Join-Path $env:LOCALAPPDATA 'ov'
if (Test-Path $ovCache) {
    $ovTar = Join-Path $dest 'ov_cache.tar'
    Write-Host "[2/3] Omniverse 캐시 아카이브 중 -> $ovTar"
    tar -cf $ovTar -C $env:LOCALAPPDATA 'ov'
} else {
    Write-Host "[2/3] Omniverse 캐시 없음 — 건너뜀"
}

# --- 복원 스크립트 동봉 ---------------------------------------------------
Write-Host "[3/3] 복원 스크립트 복사"
$here = Split-Path $PSCommandPath -Parent
Copy-Item (Join-Path $here 'restore_from_usb.ps1') $dest -Force

@"
백업 시각 : $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
환경 경로 : $EnvPath   <-- 복원도 반드시 이 경로로 (절대경로가 박혀 있음)
환경 크기 : ${needGB}GB
Isaac Sim : 5.1.0 / Python 3.11 / torch 2.7.0+cu128
"@ | Out-File (Join-Path $dest 'BACKUP_INFO.txt') -Encoding utf8

Write-Host ""
Write-Host "백업 완료 -> $dest"
Write-Host "다음에 올 때: restore_from_usb.ps1 을 실행하면 된다."
