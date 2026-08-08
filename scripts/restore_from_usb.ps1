<#
    새 PC방 자리에 앉아서 제일 먼저 실행 — 백업한 환경을 되살린다.

    사용법:
        powershell -ExecutionPolicy Bypass -File restore_from_usb.ps1 -UsbDrive E:

    Miniconda 를 다시 설치할 필요가 없다.
    conda 환경은 자체 python.exe 를 포함한 자립형이라, 디렉터리만 제자리에 있으면 된다.

    ⚠️ 복원 경로는 반드시 백업 때와 동일해야 한다 (D:\ic\env).
       conda 환경 내부에 절대경로가 박혀 있어서 경로가 바뀌면 깨진다.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$UsbDrive,

    [string]$EnvPath = 'D:\ic\env'
)

$ErrorActionPreference = 'Stop'

$src = Join-Path $UsbDrive 'isaac-simready-backup'
if (-not (Test-Path $src)) { throw "백업 폴더를 찾을 수 없다: $src" }

if (Test-Path (Join-Path $src 'BACKUP_INFO.txt')) {
    Write-Host "--- 백업 정보 ---"
    Get-Content (Join-Path $src 'BACKUP_INFO.txt')
    Write-Host "-----------------`n"
}

# --- 0. 이 PC가 쓸 만한지 먼저 확인 ---------------------------------------
Write-Host "[0/4] 하드웨어 확인"
$gpu = (nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader) 2>$null
if (-not $gpu) { throw "nvidia-smi 실패 — NVIDIA GPU/드라이버가 없다. 다른 자리로 옮길 것." }
Write-Host "      GPU: $gpu"
Write-Host "      (참고: Isaac Sim 5.1 최소 사양은 RTX 4080/16GB, 드라이버 580.88+)"

$envParent = Split-Path $EnvPath -Parent
$drive = (Split-Path $EnvPath -Qualifier).TrimEnd(':')
$freeGB = [math]::Round((Get-PSDrive $drive).Free / 1GB, 1)
Write-Host "      ${drive}: 여유 ${freeGB}GB"
if ($freeGB -lt 20) { throw "${drive}: 공간 부족 (20GB 이상 필요)" }

# --- 1. conda 환경 복원 ---------------------------------------------------
New-Item -ItemType Directory -Force $envParent | Out-Null
Write-Host "[1/4] conda 환경 복원 중 -> $EnvPath"
$sw = [Diagnostics.Stopwatch]::StartNew()
tar -xf (Join-Path $src 'isaac_env.tar') -C $envParent
$sw.Stop()
Write-Host ("      완료 ({0:N1}분)" -f $sw.Elapsed.TotalMinutes)

# --- 2. 셰이더 캐시 복원 (첫 실행 단축) -----------------------------------
$ovTar = Join-Path $src 'ov_cache.tar'
if (Test-Path $ovTar) {
    Write-Host "[2/4] Omniverse 캐시 복원"
    tar -xf $ovTar -C $env:LOCALAPPDATA
} else {
    Write-Host "[2/4] 캐시 백업 없음 — 첫 실행이 느릴 수 있다 (정상)"
}

# --- 3. 임시 디렉터리 준비 ------------------------------------------------
# pip 이 %TEMP%(C:) 를 쓰다 시스템 드라이브를 소진하는 문제를 미리 차단한다.
Write-Host "[3/4] 임시 디렉터리 준비"
New-Item -ItemType Directory -Force (Join-Path $envParent 'tmp') | Out-Null

# --- 4. 검증 --------------------------------------------------------------
Write-Host "[4/4] 검증"
$py = Join-Path $EnvPath 'python.exe'
if (-not (Test-Path $py)) { throw "python.exe 가 없다 — 복원 실패: $py" }

& $py -c "import torch; print('      torch    :', torch.__version__); print('      cuda     :', torch.cuda.is_available()); print('      device   :', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A')"

Write-Host ""
Write-Host "복원 완료. 이제 이렇게 쓰면 된다:"
Write-Host ""
Write-Host "    `$env:TEMP='$envParent\tmp'; `$env:TMP='$envParent\tmp'"
Write-Host "    `$env:OMNI_KIT_ACCEPT_EULA='YES'"
Write-Host "    & '$py' -u scripts\p1_drive_tuning.py --sweep"
Write-Host ""
Write-Host "코드는 git clone 으로 받는다:"
Write-Host "    git clone https://github.com/grim132435-boop/Isaac-simready-validation.git"
