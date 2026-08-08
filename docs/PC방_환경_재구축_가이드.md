# PC방 환경 재구축 가이드

> **전제** — 이 PC방은 **C:와 D: 모두 초기화된다.** 매번 처음부터다.
> 자리도 매번 다를 수 있어 GPU 확인부터 시작한다.
>
> 목표는 "설치를 빠르게"가 아니라 **"설치를 건너뛰기"** 다.

---

## 두 가지 경로

| 경로 | 소요 | 언제 |
|---|---|---|
| **A. USB 복원** | **약 5~10분** | USB에 백업이 있을 때 (기본) |
| **B. 처음부터 설치** | 약 25~35분 | USB가 없거나 깨졌을 때 |

USB 복원이 빠른 이유 — 25GB 다운로드와 의존성 해결이 통째로 사라지고,
14.8GB를 로컬 디스크로 푸는 작업만 남는다. 셰이더 캐시도 같이 복원되어 첫 실행도 빠르다.

---

## 사전 준비 (한 번만) — USB 만들기

### 필요한 것
- **USB 3.0 이상, 32GB 이상** (실측: env 14.81GB + 캐시 0.38GB ≈ 15.2GB)
  - USB 2.0(~30MB/s)이면 복원에 9분 이상 걸린다. 3.0(~150MB/s)이면 2분 안쪽.

### 떠나기 전에 실행
```powershell
cd C:\Users\Administrator\Desktop\ndotlight-simready
powershell -ExecutionPolicy Bypass -File scripts\backup_to_usb.ps1 -UsbDrive E:
```

USB에 이런 구조가 만들어진다.
```
E:\isaac-simready-backup\
├── isaac_env.tar        conda 환경 전체 (~14.8GB)
├── ov_cache.tar         Omniverse 셰이더 캐시 (~0.4GB)
├── restore_from_usb.ps1 복원 스크립트
└── BACKUP_INFO.txt      백업 시각·경로·버전
```

> **왜 Miniconda를 백업하지 않나** — 복원에 필요 없다.
> conda 환경은 자체 `python.exe` 를 포함한 자립형이라 디렉터리만 제자리에 있으면 동작한다.
> 이번 세션 전체를 `conda activate` 없이 `D:\ic\env\python.exe` 직접 호출로 돌려서 확인했다.

> **왜 무압축 tar 인가** — Isaac Sim 파일 대부분이 이미 압축된 바이너리라 압축률이 거의 없다.
> 압축하면 시간만 몇 배로 든다. 반면 파일 수만 개를 개별 복사하는 것보다
> 단일 아카이브 전송이 USB에서 훨씬 빠르다.

---

## 경로 A — USB 복원 (기본)

### A-1. 자리 확인 (제일 먼저)
```powershell
nvidia-smi
```
- **GPU 모델·VRAM 확인.** Isaac Sim 5.1 최소는 RTX 4080/16GB.
  RTX 5070(12GB)은 최소 미달이지만 **가벼운 씬은 실측상 문제없이 동작했다.**
- **드라이버 580.88 이상** 확인 (cu128 요구는 570.86 이상)
- GPU가 다르면 → 그래도 진행. torch cu128은 Blackwell/Ada/Ampere 모두 커버한다.
  단 **VRAM이 8GB 미만이면 다른 자리로 옮기는 게 낫다.**

### A-2. 복원
```powershell
powershell -ExecutionPolicy Bypass -File E:\isaac-simready-backup\restore_from_usb.ps1 -UsbDrive E:
```

스크립트가 알아서 한다.
1. GPU·디스크 여유 확인
2. `D:\ic\env` 로 환경 복원 ← **경로가 반드시 같아야 한다** (아래 주의 참조)
3. 셰이더 캐시 복원
4. `D:\ic\tmp` 생성 (pip이 C:를 소진하는 문제 차단)
5. `torch.cuda.is_available()` 검증

### A-3. 코드 받기
```powershell
git clone https://github.com/grim132435-boop/Isaac-simready-validation.git
cd Isaac-simready-validation
```
git이 없으면 GitHub에서 ZIP 다운로드해도 된다.

### A-4. 실행
```powershell
$env:TEMP='D:\ic\tmp'; $env:TMP='D:\ic\tmp'
$env:OMNI_KIT_ACCEPT_EULA='YES'
& 'D:\ic\env\python.exe' -u scripts\smoke_test.py    # 검증
& 'D:\ic\env\python.exe' -u scripts\p1_drive_tuning.py --sweep
```

> ### ⚠️ 경로를 바꾸지 말 것
> conda 환경 내부에 `D:\ic\env` 절대경로가 박혀 있다.
> 다른 경로로 풀면 깨진다. D: 드라이브가 없는 자리라면 그때는 경로를 바꿔야 하는데,
> 그 경우 **경로 A를 포기하고 경로 B(처음부터 설치)로 간다.**

---

## 경로 B — 처음부터 설치

USB가 없거나, D: 드라이브가 없어 경로를 바꿔야 할 때.

### B-0. 확인
```powershell
nvidia-smi                                    # GPU·드라이버
Get-PSDrive C,D | Select-Object Name,Free     # 여유 공간 (설치 대상 50GB+)
New-Item -ItemType Directory -Force D:\ic     # 쓰기 권한 테스트
```

### B-1. Miniconda (관리자 권한 불필요)
```powershell
$ProgressPreference = 'SilentlyContinue'
Invoke-WebRequest -Uri 'https://repo.anaconda.com/miniconda/Miniconda3-latest-Windows-x86_64.exe' `
                  -OutFile 'D:\ic\miniconda.exe' -UseBasicParsing

Start-Process -FilePath 'D:\ic\miniconda.exe' `
  -ArgumentList '/InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /S /D=D:\ic\miniconda3' -Wait
```
`/InstallationType=JustMe` 가 관리자 권한 프롬프트를 회피하는 핵심.
`/D=경로` 는 **반드시 맨 마지막, 따옴표 없이** (NSIS 규칙).

### B-2. Python 3.11 환경
```powershell
& 'D:\ic\miniconda3\Scripts\conda.exe' create -p D:\ic\env python=3.11 -y --override-channels -c conda-forge
```
`--override-channels -c conda-forge` 로 Anaconda ToS 게이트를 우회한다.
(defaults 채널은 ToS 동의가 필요하고 일정 규모 조직 상용 이용 시 유료 라이선스 대상)

### B-3. 임시 디렉터리를 데이터 드라이브로 ★
```powershell
New-Item -ItemType Directory -Force D:\ic\tmp | Out-Null
$env:TEMP = 'D:\ic\tmp'
$env:TMP  = 'D:\ic\tmp'
```
**이걸 빠뜨리면 C:가 소진되며 설치가 실패한다.** pip은 `--cache-dir` 와 무관하게
`%TEMP%`(기본 C:)에 wheel을 푼다. `isaacsim-extscache-kit` 하나가 3.4GB다.

### B-4. Isaac Sim (약 10분)
```powershell
& 'D:\ic\env\python.exe' -m pip install --upgrade pip
& 'D:\ic\env\python.exe' -m pip install "isaacsim[all,extscache]==5.1.0" `
    --extra-index-url https://pypi.nvidia.com --cache-dir D:\ic\pipcache
```

### B-5. PyTorch를 CUDA 빌드로 교체 ★
```powershell
& 'D:\ic\env\python.exe' -m pip uninstall -y torch torchvision torchaudio
& 'D:\ic\env\python.exe' -m pip install --index-url https://download.pytorch.org/whl/cu128 `
    torch==2.7.0 torchvision==0.22.0 torchaudio==2.7.0 --cache-dir D:\ic\pipcache
```
**Isaac Sim이 의존성으로 `torch 2.7.0+cpu` 를 끌고 온다.** 버전 숫자는 맞는데 CUDA가 없다.
에러가 안 나서 놓치기 쉽다. 반드시 교체하고 검증할 것.

### B-6. 검증
```powershell
& 'D:\ic\env\python.exe' -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```
기대: `2.7.0+cu128 True NVIDIA GeForce RTX 5070`

`+cpu` 나 `False` 가 나오면 B-5를 다시 한다.

### B-7. EULA
```powershell
$env:OMNI_KIT_ACCEPT_EULA = 'YES'
```
Isaac Sim 첫 실행 시 EULA 동의를 대화형으로 묻는다. 비대화형 환경에서는 이 변수로 대신한다.
(약관 내용은 [여기](https://docs.omniverse.nvidia.com/platform/latest/common/NVIDIA_Omniverse_License_Agreement.html))

### B-8. 스모크 테스트
```powershell
& 'D:\ic\env\python.exe' -u scripts\smoke_test.py
```
기대: `[smoke] cube z: 1.0000 -> 0.1000` / `PhysX stepping OK`
첫 실행은 셰이더 컴파일로 수 분 걸린다. **멈춘 게 아니다.**

### B-9. 떠나기 전 백업 만들기
```powershell
powershell -ExecutionPolicy Bypass -File scripts\backup_to_usb.ps1 -UsbDrive E:
```

---

## 버전 고정 (바꾸지 말 것)

| 항목 | 값 | 이유 |
|---|---|---|
| Isaac Sim | **5.1.0** | 핀 안 하면 6.0이 깔림 |
| Python | **3.11** | Isaac Sim 5.X 요구. **6.0은 3.12** — 문서 볼 때 혼동 주의 |
| PyTorch | **2.7.0 + cu128** | Blackwell(sm_120) 지원. 드라이버 570.86+ 필요 |
| torchvision | **0.22.0** | torch 2.7과 짝 고정 |
| Isaac Lab | 2.3.x (필요 시) | 2.3은 5.1 전용. **6.0과 비호환** |

**Isaac Sim 6.0.x를 쓰지 않는 이유** — "Early Developer Release"이고, 지원 Isaac Lab이
3.0.0 Beta 2뿐이며, 의존성 충돌([#6200](https://github.com/isaac-sim/IsaacLab/issues/6200))이
보고돼 있고, PyTorch 기반 Core API가 Warp 기반으로 deprecated 되는 코어 재설계 중이다.

---

## 자주 막히는 지점

| 증상 | 원인 | 해결 |
|---|---|---|
| `No space left on device` (디스크는 남았는데) | pip이 `%TEMP%`(C:)에 압축 해제 | B-3의 TEMP 설정 |
| `cuda avail: False`, 에러는 없음 | torch가 `+cpu` 빌드 | B-5 재실행 |
| `CondaToSNonInteractiveError` | Anaconda 채널 ToS | `--override-channels -c conda-forge` |
| `Do you accept the EULA?` 에서 멈춤 | 비대화형 환경 | `OMNI_KIT_ACCEPT_EULA=YES` |
| Miniconda 설치 시 관리자 권한 요구 | AllUsers 설치 | `/InstallationType=JustMe` |
| 첫 실행이 몇 분째 무응답 | 셰이더 컴파일 | 정상. 기다린다 (캐시 복원하면 회피) |
| 경로 관련 파일 없음 에러 | Windows 260자 경로 제한 | 짧은 경로 사용 (`D:\ic\env`). long path 활성화는 admin 필요 |
| 스크립트가 조용히 종료, traceback 없음 | `simulation_app.close()` 가 프로세스를 즉시 종료 | 예외를 직접 `print` 하고 `flush` 후 close |
| `print` 출력이 안 보임 | 파이프 리다이렉트 시 stdout 버퍼링 | `python -u` |

상세 분석은 `so-arm101-simtoreal/_logs/` 의 다음 문서들 참조.
- `2026-08-08_isaac-sim이-torch-cpu빌드로-덮어씀.md`
- `2026-08-08_비대화형-설치에서-동의게이트-3종.md`
- `2026-08-08_windows-pip-TEMP가-시스템드라이브로-간다.md`

---

## 이 환경의 한계 (알고 쓸 것)

- **VRAM 12GB < 공식 최소 16GB** — 로봇 1대 수준 씬은 실측상 문제없다.
  무거운 멀티카메라 렌더링·Cosmos 추론은 이 PC에서 포기한다.
- **매 세션 초기화** — 결과물은 반드시 GitHub에 푸시하고 환경은 USB에 백업한다.
  중간에 1시간마다 커밋하는 습관을 들인다.
- **장시간 학습 불가** — 자리를 뜨면 날아간다. RL 학습 같은 건 AWS로 가야 한다.
  이 PC방은 **씬 구축·검증·디버깅** 용도로만 쓴다.
