# PC방 환경 재구축 가이드

> **전제** — 이 PC방은 **C:와 D: 모두 초기화된다.** 매번 처음부터다.
> 자리도 매번 다를 수 있어 GPU 확인부터 시작한다.
>
> 목표는 "설치를 빠르게"가 아니라 **"설치를 건너뛰기"** 다.

---

## 채택한 방식 — 매번 처음부터 설치 (경로 B)

**USB 백업은 쓰지 않기로 했다.**

| 경로 | 소요 | 채택 |
|---|---|---|
| **B. 처음부터 설치** | 약 25~35분 (**조작은 5분, 나머지는 대기**) | ✅ **기본** |
| A. USB 복원 | 약 5~10분 | 보류 (스크립트는 남겨둠) |

**근거** — 25~35분 중 실제로 손이 가는 건 5분이고 나머지는 다운로드 대기다.
그 시간에 [학습 커리큘럼](학습커리큘럼_Isaac_Sim_기초부터_면접까지.md) STEP 0을 읽으면
실질 손실이 거의 없다. USB 분실·손상·경로 불일치 리스크를 안 지는 편이 낫다.

> **세션 시작 요령 — 설치를 먼저 걸어놓고 공부한다.**
> B-4(Isaac Sim 설치)가 제일 오래 걸리므로, 그걸 실행한 직후부터 개념 학습을 시작한다.

**코드·문서·측정 원자료는 GitHub에 있다.** 용량이 작아 clone이 몇 초면 끝난다.
```
git clone https://github.com/grim132435-boop/Isaac-simready-validation.git
```

> ### ⚠️ 이 문서는 아직 "위에서 아래로" 실행된 적이 없다
> 각 단계는 실제로 통과한 명령이지만, 문서는 작업이 끝난 뒤 정리한 것이다.
> **다음 세션이 이 문서의 첫 통합 테스트다.**
> 막히는 지점이 나오면 그 자리에서 문서를 고치고 커밋해라. 그래야 진짜 검증된 문서가 된다.

USB 복원 경로가 필요해지면 아래 「부록: USB 복원」을 본다.

---

## 부록: USB 복원 (보류 — 필요해지면)

> 매 세션 재설치가 번거로워지면 이 방식으로 전환한다. 스크립트는 준비돼 있다.

### 사전 준비 (한 번만) — USB 만들기

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

### B-0. 확인 — 어느 드라이브에 깔지부터 정한다

```powershell
nvidia-smi                                                     # GPU·드라이버
Get-PSDrive -PSProvider FileSystem | Select-Object Name,`
  @{n='FreeGB';e={[math]::Round($_.Free/1GB,1)}}               # 전체 드라이브 여유
```

**설치 드라이브 선택 기준 — 여유 60GB 이상인 드라이브 중 C:가 아닌 것.**
(설치본 15GB + 다운로드/임시 25GB + 여유)

D:가 없거나 좁은 자리를 만날 수 있다. 그럴 땐 아래 변수 하나만 바꾸고
**이후 모든 명령에서 `D:\ic` 를 `$IC` 로 읽으면 된다.**

```powershell
# ★ 자리마다 이 한 줄만 조정한다
$IC = 'D:\ic'          # D:가 없으면 'E:\ic' 등으로 변경

New-Item -ItemType Directory -Force $IC | Out-Null
"test" | Out-File "$IC\wtest.txt"; Get-Content "$IC\wtest.txt"   # 쓰기 권한 테스트
```

> **C:에는 깔지 마라.** 시스템 드라이브가 여유 60GB를 넘더라도, pip 임시 공간과
> 설치본이 같은 드라이브를 두고 경쟁하면 실패 확률이 올라간다.
> 정말 C: 뿐이라면 여유가 **80GB 이상**일 때만 시도한다.
>
> **경로는 짧게 유지한다.** Windows 260자 제한 때문이다.
> `E:\ic` 는 되지만 `E:\내문서\프로젝트\isaac\env` 같은 건 피한다.

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

### B-10. (선택) Isaac Lab 2.3.x 설치

RL 학습·태스크 실습이 필요할 때만. **공식 문서(pip 설치 경로) 기준으로 절차·버전을 검증했다:**
https://isaac-sim.github.io/IsaacLab/main/source/setup/installation/pip_installation.html

**전제 확인 (공식 문서 대조 결과)**
- Isaac Sim 5.X → Python **3.11** 필수. 지금 `D:\ic\env`는 3.11.15 → 일치.
- 공식 Windows(x86_64) 탭 pip 커맨드: `pip install -U torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128` — **torchaudio는 포함 안 함.**
  B-5에서 설치한 torchaudio는 이 단계에서 다시 제거된다 (아래 참고 ④). 공식 절차와 일치하는 정상 동작이니 놀라지 말 것.
- `isaaclab.bat --install`은 기본으로 **전체 RL 프레임워크**(`rl_games`, `rsl_rl`, `sb3`, `skrl`, `robomimic`)를 설치한다. 특정 프레임워크만 원하면
  `isaaclab.bat --install rl_games` 처럼 이름을 넘긴다.

**우리 방식(conda activate 안 씀)과의 차이 — 공식 문서는 `conda activate env_isaaclab` 후 `isaaclab.bat -i`를 실행하는 걸 전제로 한다.**
`conda activate`가 `%CONDA_PREFIX%`를 자동으로 잡아주기 때문이다. §0의 원칙대로 activate 없이 가려면 그 값을 직접 세팅해야 한다.

```powershell
$env:TEMP='D:\ic\tmp'; $env:TMP='D:\ic\tmp'
$env:CONDA_PREFIX='D:\ic\env'
$env:OMNI_KIT_ACCEPT_EULA='YES'
$env:PATH = "D:\ic\Git\bin;D:\ic\Git\cmd;$env:PATH"   # 같은 세션에서 방금 git을 깔았다면 필수 (아래 ② 참고)

git clone https://github.com/isaac-sim/IsaacLab.git D:\ic\IsaacLab
& 'D:\ic\Git\bin\git.exe' -C D:\ic\IsaacLab fetch --depth 1 origin tag v2.3.2
& 'D:\ic\Git\bin\git.exe' -C D:\ic\IsaacLab checkout v2.3.2   # Isaac Sim 5.1 전용 최신 2.3.x. v2.3.3 이상이 나왔으면 그쪽을 우선 확인

# ① 아래 known issue 픽스를 --install보다 먼저 실행 (순서 중요)
& 'D:\ic\env\python.exe' -m pip install flatdict==4.0.0 --cache-dir D:\ic\pipcache

Set-Location D:\ic\IsaacLab
& .\isaaclab.bat --install
```

**known issue ① — `flatdict==4.0.1` 빌드 실패로 `isaaclab` 코어 모듈이 조용히 설치 안 됨**
공식 GitHub에 이미 보고·수정된 버그다: [issue #4577](https://github.com/isaac-sim/IsaacLab/issues/4577) (증상: [#4576](https://github.com/isaac-sim/IsaacLab/issues/4576) `ModuleNotFoundError: No module named 'isaaclab'`).
원인은 최신 setuptools(81+)가 `pkg_resources`를 제거했는데 `flatdict`의 레거시 `setup.py`가 그걸 요구해서 빌드가 깨지는 것.
[PR #4581](https://github.com/isaac-sim/IsaacLab/pull/4581)에서 `flatdict`를 pkg_resources를 안 쓰는 **4.0.0**으로 되돌려 고쳤는데, 이 커밋이 `main`엔 있지만
**v2.3.2 태그엔 아직 없다** (다음 2.3.x 릴리즈에 포함될 예정). 그래서 위처럼 `--install` 전에 `flatdict==4.0.0`을 먼저 깔아 선점해야 한다.
(대안: `pip install "setuptools<81"` 로 `pkg_resources`를 살리고 `pip install flatdict==4.0.1 --no-build-isolation` — 둘 다 동작 확인함.)
설치 후 반드시 `python -c "import isaaclab"` 로 실제로 들어갔는지 확인할 것. `pip`가 "Failed to build 'flatdict'"를 찍고도 다음 확장 설치로 그냥 넘어가버려서
전체 로그는 성공처럼 보일 수 있다.

**known issue ② — 같은 세션에서 방금 설치한 git이 `isaaclab.bat`의 하위 프로세스 PATH에 안 잡힘**
`isaaclab_rl[all]`이 `rl_games`를 `git+https://...`로 설치하는데, git을 처음 깐 그 프로세스에서 바로 이어서 실행하면
`ERROR: Cannot find command 'git'`이 난다. 레지스트리 User PATH는 갱신됐어도, 이미 떠 있는 셸/프로세스는 옛 PATH를 물고 있기 때문
(새 창을 열어야 반영됨). 새 PowerShell 창을 열거나, 위 스크립트처럼 `$env:PATH`에 `D:\ic\Git\bin`을 그 세션에서 직접 추가해서 우회한다.

**known issue ③ (무해, 참고용) — `isaaclab.bat`가 이미 맞는 torch를 못 알아보고 매번 재설치를 시도함**
`--install` 실행 초반에 `The filename, directory name, or volume label syntax is incorrect.` 가 찍히고 `[INFO] Found PyTorch version .` (버전 공백)이
나오는데, 이건 `pip show torch` 버전 파싱이 깨져서 항상 "버전 불일치"로 판정하고 torch/torchvision을 캐시에서 재설치(다운로드는 아니고 캐시 재사용,
단 첫 설치 직후라 캐시가 없으면 3GB대 재다운로드)하는 배치 스크립트 버그다. 결과 자체는 스크립트 끝에서 다시 맞춰지므로 (`ensure_cuda_torch`가
`--install` 안에서 최대 2번 더 호출됨) 최종 상태는 정상이 된다. 넘어가도 된다 — 단 `--install`이 끝나면 **반드시 B-6 커맨드로 최종 버전을 재확인**할 것.

**④ — Isaac Lab 설치 후 torchaudio가 사라져 있는 게 정상이다**
B-5에서 깐 `torchaudio==2.7.0`은 `isaaclab.bat`의 `ensure_cuda_torch`가 `pip uninstall torch torchvision torchaudio`는 하면서
재설치는 `torch`/`torchvision`만 하기 때문에 없어진다. 공식 pip 설치 커맨드도 애초에 torchaudio를 설치하지 않으므로 (Isaac Lab이 오디오를 안 씀)
이건 버그가 아니라 의도된 동작이다. `isaacsim-core requires torchaudio==2.7.0, which is not installed` 경고는 무시해도 된다.

**최종 검증**
```powershell
& 'D:\ic\env\python.exe' -c "import torch; print(torch.__version__, torch.cuda.is_available())"
# 기대: 2.7.0+cu128 True

& 'D:\ic\env\python.exe' -c "import isaaclab; print('OK')"
& 'D:\ic\env\python.exe' -c "import rsl_rl, skrl, stable_baselines3, rl_games; print('frameworks OK')"
```
`isaaclab_tasks` 등 USD(`pxr`)를 쓰는 모듈은 `python -c "import ..."`로 단독 실행하면 `ModuleNotFoundError: No module named 'pxr'`가 난다 —
이건 정상이다. `pxr`은 Isaac Sim Kit이 뜰 때(`SimulationApp` 생성 시점)만 `sys.path`에 잡히므로, `isaaclab.bat -p 스크립트.py` 로 실행하거나
Kit을 먼저 띄우는 스크립트 안에서만 import가 된다.

---

## 버전 고정 (바꾸지 말 것)

| 항목 | 값 | 이유 |
|---|---|---|
| Isaac Sim | **5.1.0** | 핀 안 하면 6.0이 깔림 |
| Python | **3.11** | Isaac Sim 5.X 요구. **6.0은 3.12** — 문서 볼 때 혼동 주의 |
| PyTorch | **2.7.0 + cu128** | Blackwell(sm_120) 지원. 드라이버 570.86+ 필요 |
| torchvision | **0.22.0** | torch 2.7과 짝 고정 |
| Isaac Lab | 2.3.x (필요 시) — 설치는 B-10 참고 | 2.3은 5.1 전용. **6.0과 비호환**. v2.3.2엔 flatdict 버그 있음 (B-10 known issue ①) |

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
| `isaaclab.bat --install` 후 `ModuleNotFoundError: No module named 'isaaclab'` | `flatdict==4.0.1` 빌드가 `pkg_resources` 없어서 조용히 실패 (setuptools 81+). 기보고된 버그: [#4577](https://github.com/isaac-sim/IsaacLab/issues/4577), 수정 [#4581](https://github.com/isaac-sim/IsaacLab/pull/4581) — v2.3.2엔 미포함 | `--install` 전에 `pip install flatdict==4.0.0` 선점 (B-10 참고) |
| `rl_games` 설치 중 `Cannot find command 'git'` | 같은 세션에서 방금 깐 git이 하위 pip 프로세스 PATH에 반영 안 됨 | 새 PowerShell 창을 열거나 `$env:PATH`에 `D:\ic\Git\bin` 그 세션에서 직접 추가 |
| `isaaclab.bat --install` 시작하자마자 `The filename, directory name, or volume label syntax is incorrect.` | `pip show torch` 버전 파싱 버그로 항상 재설치 판정 (무해, self-heal) | 무시하고 진행, 끝나면 B-6으로 최종 torch 버전만 재확인 |

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
