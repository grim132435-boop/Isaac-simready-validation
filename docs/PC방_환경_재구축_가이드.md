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
cd C:\Users\Administrator\Desktop\n2p\20_Projects\Isaac-simready-validation
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
$env:PIP_CACHE_DIR='D:\ic\pipcache'                   # ★ 이거 빠뜨리면 torch 3.3GB를 새로 받는다 (아래 ③ 참고)
$env:CONDA_PREFIX='D:\ic\env'
$env:OMNI_KIT_ACCEPT_EULA='YES'
$env:PATH = "D:\ic\Git\bin;D:\ic\Git\cmd;$env:PATH"   # 같은 세션에서 방금 git을 깔았다면 필수 (아래 ② 참고)

git clone https://github.com/isaac-sim/IsaacLab.git D:\ic\IsaacLab
& 'D:\ic\Git\bin\git.exe' -C D:\ic\IsaacLab fetch --depth 1 origin tag v2.3.2
& 'D:\ic\Git\bin\git.exe' -C D:\ic\IsaacLab checkout v2.3.2   # Isaac Sim 5.1 전용 최신 2.3.x. v2.3.3 이상이 나왔으면 그쪽을 우선 확인

# ① flatdict 선점 — 이것만으로는 부족하다. 아래 known issue ① 을 반드시 읽을 것
& 'D:\ic\env\python.exe' -m pip install "setuptools<81" --cache-dir D:\ic\pipcache
& 'D:\ic\env\python.exe' -m pip install flatdict==4.0.1 --no-build-isolation --cache-dir D:\ic\pipcache

Set-Location D:\ic\IsaacLab
& .\isaaclab.bat --install

# ② --install 이 끝나면 코어가 실제로 들어갔는지 반드시 확인한다 (조용히 실패한다)
& 'D:\ic\env\python.exe' -c "import isaaclab; print('OK')"
# 실패하면 코어만 따로 재설치
& 'D:\ic\env\python.exe' -m pip install -e D:\ic\IsaacLab\source\isaaclab --no-build-isolation --cache-dir D:\ic\pipcache
```

**known issue ① — `flatdict==4.0.1` 빌드 실패로 `isaaclab` 코어 모듈이 조용히 설치 안 됨**
공식 GitHub에 이미 보고·수정된 버그다: [issue #4577](https://github.com/isaac-sim/IsaacLab/issues/4577) (증상: [#4576](https://github.com/isaac-sim/IsaacLab/issues/4576) `ModuleNotFoundError: No module named 'isaaclab'`).
원인은 최신 setuptools(81+)가 `pkg_resources`를 제거했는데 `flatdict`의 레거시 `setup.py`가 그걸 요구해서 빌드가 깨지는 것.
[PR #4581](https://github.com/isaac-sim/IsaacLab/pull/4581)에서 `flatdict`를 pkg_resources를 안 쓰는 **4.0.0**으로 되돌려 고쳤는데, 이 커밋이 `main`엔 있지만
**v2.3.2 태그엔 아직 없다** (다음 2.3.x 릴리즈에 포함될 예정).

> ### ⚠️ `flatdict==4.0.0` 선점은 v2.3.2에서 통하지 않는다 — 2026-08-16 재실측으로 확정
>
> 이 항목은 문서 이력에서 두 번 뒤집혔다. `c11b8b9`가 "선점만으론 안 통함"을 넣었고,
> `a733148`이 "선점하면 됨"으로 되돌렸다. **2026-08-16에 깨끗한 환경에서 다시 돌려
> `c11b8b9`가 맞는 것으로 판정했다.** 로그 증거는 이렇다.
>
> ```
>   2: Requirement already satisfied: flatdict==4.0.0 ...   ← 선점은 되어 있었다
>  78: Collecting flatdict==4.0.1 (from isaaclab==0.54.2)   ← 그런데 4.0.1을 다시 요구
> 115:       ModuleNotFoundError: No module named 'pkg_resources'
> 119: ERROR: Failed to build 'flatdict' when getting requirements to build wheel
> 733: ModuleNotFoundError: No module named 'isaaclab'      ← 코어가 안 들어감
> ```
>
> 이유는 `source/isaaclab/setup.py`가 `flatdict==4.0.1`을 **exact pin** 으로 박아둔 것.
> pip은 이미 깔린 4.0.0을 "요구사항 불충족"으로 보고 4.0.1을 새로 빌드하려다 그대로 실패한다.
> **선점한 4.0.0은 아무 역할을 못 한다.**
>
> 그리고 `--install` 은 이 실패를 삼키고 다음 확장 설치로 넘어간다. `isaaclab_assets`,
> `isaaclab_tasks`, `isaaclab_rl` 은 정상 설치되므로 **로그 전체는 성공처럼 보이는데
> 코어만 쏙 빠져 있다.**
>
> **실제로 통하는 절차 — `setuptools<81` 로 `pkg_resources` 를 살린다.**
> ```powershell
> & 'D:\ic\env\python.exe' -m pip install "setuptools<81" --cache-dir D:\ic\pipcache
> & 'D:\ic\env\python.exe' -m pip install flatdict==4.0.1 --no-build-isolation --cache-dir D:\ic\pipcache
> ```
> `--install` 이 이미 실패를 삼키고 지나간 뒤라면 코어만 따로 재설치한다.
> ```powershell
> & 'D:\ic\env\python.exe' -m pip install -e D:\ic\IsaacLab\source\isaaclab --no-build-isolation --cache-dir D:\ic\pipcache
> ```
> 2026-08-16 실측 최종 상태: `isaaclab 0.54.2`, `flatdict 4.0.1`, `setuptools 80.10.2`.
>
> 재설치 과정에서 `fastapi 0.115.7 requires starlette<0.46.0`,
> `stable-baselines3 2.9.0 requires torch>=2.8` 같은 pip 경고가 뜰 수 있는데
> `import` 가 되면 무시해도 된다 (실측 확인).

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

> **2026-08-16 실측 — 이건 "무해"가 아니라 3.3GB 재다운로드였다. 그리고 회피할 수 있다.**
> `isaaclab.bat` 는 하위 pip 에 `--cache-dir` 을 물려주지 않는다. 그래서 B-5에서 `--cache-dir D:\ic\pipcache`
> 로 잘 받아둔 cu128 휠이 있어도 **pip 기본 캐시(`%LOCALAPPDATA%\pip\Cache`, C: 드라이브)** 를 보고
> "없다" 판정 후 3.3GB를 새로 내려받는다. 이 날 실제로 그렇게 시작하는 것을 보고 중단했다.
>
> **`PIP_CACHE_DIR` 환경변수를 쓰면 해결된다.** `--cache-dir` 과 달리 환경변수는 하위 프로세스로 전파되므로
> `isaaclab.bat` 안의 pip 도 같은 캐시를 본다. 위 스크립트에 이미 넣어두었다.
> ```powershell
> $env:PIP_CACHE_DIR = 'D:\ic\pipcache'
> ```
> 덤으로, C: 여유가 빠듯한 자리에서 pip 캐시가 시스템 드라이브를 먹는 것도 같이 막힌다.

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

### B-10-1. LeRobot 환경 (ACT 학습용) — **Python 3.12 별도 env**

Isaac Sim 안에서 만든 시연 데이터로 ACT를 학습하려면 LeRobot이 필요하다.
**Isaac Sim의 `D:\ic\env`에 같이 넣을 수 없다.**

> ### ⚠️ Python 버전이 갈린다 — 2026-08-16 실측
> `lerobot` 은 **0.5.0부터 `Requires-Python >=3.12`** 로 올라갔다. Isaac Sim 5.1은 3.11 고정이다.
> 3.11 env에 설치를 시도하면 pip이 0.6.1을 후보에서 아예 빼고 이렇게 끝난다.
> ```
> ERROR: Ignored the following versions that require a different python version:
>        0.5.0 Requires-Python >=3.12; 0.6.0 ...; 0.6.1 Requires-Python >=3.12
> ERROR: Could not find a version that satisfies the requirement lerobot==0.6.1
>        (from versions: 0.1.0, 0.3.2, 0.3.3, 0.4.0, 0.4.1, 0.4.2, 0.4.3, 0.4.4)
> ```
> **에러를 안 읽으면 "0.4.4까지밖에 없나 보다"로 오해하기 쉽다.** 첫 줄이 진짜 이유다.
> 이 버전 충돌은 「부록: SimReady Foundation」이 3.12 별도 env를 파는 것과 같은 성격이다.

```powershell
$env:TEMP='D:\ic\tmp'; $env:TMP='D:\ic\tmp'
$env:PIP_CACHE_DIR='D:\ic\pipcache'

& 'D:\ic\miniconda3\Scripts\conda.exe' create -p D:\ic\lerobot-env python=3.12 -y --override-channels -c conda-forge

& 'D:\ic\lerobot-env\python.exe' -m pip install --upgrade pip

# ★ extras 를 반드시 붙인다. 맨 lerobot 만 깔면 데이터셋 API 가 안 들어온다 (아래 참고)
& 'D:\ic\lerobot-env\python.exe' -m pip install "lerobot[dataset,training,dataset-viz]==0.6.1"

# ★ torch를 cu128로 교체 — 여기서도 필요하다 (B-5와 같은 이유)
& 'D:\ic\lerobot-env\python.exe' -m pip install --index-url https://download.pytorch.org/whl/cu128 `
    torch==2.7.0 torchvision==0.22.0
```

> ### ⚠️ `pip install lerobot` 만으로는 데이터셋을 못 만든다 — 2026-08-16 실측
> 0.6.1은 기능이 extras로 잘게 쪼개져 있다. 기본 설치엔 `datasets` 의존성이 빠져 있어서
> **ACT 정책은 임포트되는데 데이터셋 API만 안 된다.** 그래서 "설치는 됐다"고 착각하기 쉽다.
> ```
> >>> from lerobot.datasets.lerobot_dataset import LeRobotDataset
> ImportError: 'datasets' is required but not installed.
>              Install it with: pip install 'lerobot[dataset]'
> ```
> 우리 목적(시뮬에서 시연 생성 → ACT 학습)에 필요한 것은 셋이다.
>
> | extra | 주는 것 | 왜 필요한가 |
> |---|---|---|
> | `dataset` | `LeRobotDataset.create/add_frame/save_episode` | 시연을 파일로 남기는 쪽 **과** 학습 시 읽는 쪽 양쪽 |
> | `training` | `lerobot-train` | ACT 학습 |
> | `dataset-viz` | `lerobot-dataset-viz` | 만든 데이터셋이 실물과 같은 모양인지 검수 (ACT 문서 5-4 절차) |
>
> 실물 모터용 extras(`feetech` 등)는 로봇이 PC방에 없으므로 넣지 않는다.
> 전체 목록은 `python -c "from importlib.metadata import metadata; print(sorted(set(metadata('lerobot').get_all('Provides-Extra'))))"` 로 볼 수 있다.
>
> **extras 설치가 torch를 기본 휠로 덮을 수 있으니, 설치 후 cu128인지 반드시 재확인한다.**

**torch 교체를 빠뜨리지 말 것.** RTX 5070은 Blackwell(sm_120)이고 PyPI 기본 휠은 그걸 커버하지 않는다.
학습은 도는데 CPU로 돌아 12배 느려지는 식으로 조용히 망가진다.
Python 3.12용 휠(cp312)은 3.11용과 다른 파일이라 **캐시가 있어도 3.3GB를 새로 받는다** — 정상이다.

**검증**
```powershell
& 'D:\ic\lerobot-env\python.exe' -c "import torch; print(torch.__version__, torch.cuda.is_available())"
& 'D:\ic\lerobot-env\python.exe' -c "from lerobot.datasets.lerobot_dataset import LeRobotDataset; print('OK')"
& 'D:\ic\lerobot-env\python.exe' -c "from lerobot.policies.act.modeling_act import ACTPolicy; print('OK')"
```

> **학습 중에는 Isaac Sim을 같이 돌리지 마라.** VRAM 12GB를 나눠 쓰게 된다.
> 그리고 `lerobot-train` 이 중복 실행되지 않았는지 반드시 확인한다 —
> 2026-08-15에 같은 학습이 두 개 돌아 12배 느려진 적이 있다.
> ```powershell
> Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'lerobot-train' } |
>     Select-Object ProcessId, CommandLine
> ```

---

## B-11. GitHub 자동 커밋·푸시 ★ (세션 시작 직후 실행)

> **왜 이 단계가 생겼나 — 2026-08-16 실측.**
> 이 날 세션을 시작해 보니 `so-arm101-work/`(코드 1,885줄, 진단 스크립트 9종)가
> **어느 git repo에도 추적되지 않은 상태**로 바탕화면에 놓여 있었다. 그 자리에서 PC가
> 초기화됐으면 전부 사라졌다. 원인은 게으름이 아니라 **커밋이 수동이었다는 것**이다.
> 손으로 하는 일은 바쁠 때 제일 먼저 밀린다.
>
> 이 문서의 §「이 환경의 한계」에 *"결과물은 반드시 GitHub에 푸시"* 라고 적혀 있었는데도
> 그렇게 되지 않았다. **규칙을 적어두는 것으로는 부족하고 자동화해야 한다**는 게 이 단계의 근거다.

### B-11-1. 무엇이 자동화되나

Claude Code의 **Stop 훅**을 쓴다. Claude가 한 턴의 작업을 마칠 때마다 훅이 실행되어
등록된 repo 전부를 `add` → `commit` → `push` 한다. 사람이 개입할 일이 없다.

```
Claude 작업 종료
      ↓
Stop 훅 발화
      ↓
autocommit.ps1  →  repo 1  add/commit/push
                   repo 2  add/commit/push
                   repo 3  add/commit/push
      ↓
"autocommit: so-arm101-work +3" 메시지 표시
```

스크립트 두 개가 `so-arm101-simtoreal` repo의 `scripts/` 에 들어 있다.

| 파일 | 역할 | 실행 시점 |
|---|---|---|
| `setup_autocommit.ps1` | 인증·훅을 세팅한다 | **세션마다 1회** |
| `autocommit.ps1` | 실제 add/commit/push | 훅이 자동 호출 |

### B-11-2. 부트스트랩 (인증이 아직 없는 상태)

문서 repo가 private이라 clone 자체에 인증이 필요하다. 여기서만 PAT를 손으로 넣는다.

```powershell
$env:PATH = "C:\Program Files\Git\cmd;$env:PATH"   # git이 PATH에 없다
cd C:\Users\Administrator\Desktop\n2p\20_Projects

# 문서 repo
git clone https://github.com/grim132435-boop/so-arm101-simtoreal.git SO-ARM101_SimToReal
# Username: grim132435-boop
# Password: <PAT 붙여넣기>   ← 비밀번호가 아니라 토큰이다

# 코드 repo (문서 repo 안쪽에 들어간다 — .gitignore 로 제외돼 있어 충돌하지 않는다)
git clone https://github.com/grim132435-boop/so-arm101-work.git SO-ARM101_SimToReal\so-arm101-work

# 측정 원자료 repo
git clone https://github.com/grim132435-boop/Isaac-simready-validation.git
```

**정션을 반드시 만들어라.** 코드가 `D:\ic\so-arm101-work\src` 를 **절대경로로 박아 쓴다**
(스크립트 11개 전부). 사본을 하나 더 두면 둘이 갈라지므로, 작업본은 하나로 두고
이름만 이어준다. 디렉터리 정션은 관리자 권한이 필요 없다.

```powershell
New-Item -ItemType Junction -Path 'D:\ic\so-arm101-work' `
         -Target 'C:\Users\Administrator\Desktop\n2p\20_Projects\SO-ARM101_SimToReal\so-arm101-work'

# 확인
Test-Path 'D:\ic\so-arm101-work\src\so101_pickplace\__init__.py'   # True 여야 한다
```

그리고 로봇 cfg 패키지를 `D:\ic\env` 에 등록한다. `isaac_so_arm101` 은
`isaaclab==2.3.0` 을 핀하고 있어서 **`--no-deps` 없이 깔면 2.3.2를 2.3.0으로 끌어내린다.**

```powershell
& 'D:\ic\env\python.exe' -m pip install -e D:\ic\repos\isaac_so_arm101 --no-deps
```

PAT는 https://github.com/settings/tokens → **Generate new token (classic)** → `repo` 스코프.
**PC방이므로 만료를 짧게(7일) 잡는 편이 안전하다.**

### B-11-3. 세팅 (1회)

```powershell
cd C:\Users\Administrator\Desktop\n2p\20_Projects\SO-ARM101_SimToReal
powershell -ExecutionPolicy Bypass -File scripts\setup_autocommit.ps1
```

PAT를 한 번 더 물어본다(붙여넣으면 됨). 스크립트가 하는 일은 네 가지다.

1. **`user.name` / `user.email` 설정** — 없으면 `commit` 자체가 거부된다.
   PC방 초기화 후 이게 비어 있는 것을 실측으로 확인했다.
2. **인증 저장** — `credential.helper` 를 `store --file=D:\ic\.git-credentials` 로 교체.
   시스템 gitconfig의 `manager`(GCM)를 `--replace-all` 로 덮는다. 안 그러면 helper가
   누적되어 GCM이 먼저 잡고 **대화형 창을 띄워 자동화가 거기서 멈춘다.**
3. **Stop 훅 등록** — `%USERPROFILE%\.claude\settings.json` 에 `hooks.Stop` 만 병합한다.
   `model` 같은 기존 키는 건드리지 않는다.
4. **즉시 시험 실행** — 훅을 기다리지 않고 그 자리에서 한 번 돌려 결과를 보여준다.

> **이미 Claude Code가 떠 있었다면 `/hooks` 를 한 번 열어라.** 설정 파일 감시자가
> 변경을 다시 읽는다. 새로 띄우는 경우엔 필요 없다.

### B-11-4. 대상 repo 추가·변경

`scripts/autocommit.ps1` 상단의 배열 한 곳만 고치면 된다.

```powershell
$Repos = @(
    'C:\Users\Administrator\Desktop\n2p\20_Projects\SO-ARM101_SimToReal',
    'C:\Users\Administrator\Desktop\n2p\20_Projects\SO-ARM101_SimToReal\so-arm101-work',
    'C:\Users\Administrator\Desktop\n2p\20_Projects\Isaac-simready-validation'
)
```

### B-11-5. 설계상 정한 것 (바꾸기 전에 읽을 것)

| 결정 | 이유 |
|---|---|
| **훅은 절대 실패로 끝나지 않는다** (항상 `exit 0`) | 훅이 0이 아닌 코드로 죽으면 Claude 작업 흐름까지 끊긴다. 커밋 실패보다 그게 더 나쁘다. 모든 오류는 `.autocommit.log` 로만 남는다 |
| **push 실패해도 commit은 남긴다** | 네트워크·토큰 문제로 push가 막혀도 로컬 이력은 보존된다. 다음 성공 시 같이 올라간다 |
| **push 거부되면 `pull --rebase --autostash` 후 1회 재시도** | 다른 자리에서 먼저 푸시한 경우를 자동 복구한다. 2026-08-16 실측으로 이 경로가 실제 동작하는 것을 확인했다 |
| **병합/리베이스 중이면 건드리지 않는다** | `MERGE_HEAD` 등이 있으면 건너뛴다. 자동 커밋이 충돌 해결을 망치는 것을 막는다 |
| **커밋 메시지는 파일로 넘긴다** (`commit -F`) | `-m` 으로 한글을 넘기면 콘솔 코드페이지에서 깨진다 |

### B-11-6. 자주 막히는 지점

| 증상 | 원인 | 해결 |
|---|---|---|
| 훅은 도는데 `push 실패, 로컬 보관` | PAT 만료 또는 미설정 | `setup_autocommit.ps1` 재실행 |
| `Please tell me who you are` | `user.name`/`user.email` 없음 | 같음 (B-11-3의 1번) |
| 인증 창이 뜨고 자동화가 멈춤 | GCM이 helper 목록에 남아 있음 | `git config --global --replace-all credential.helper "store --file=D:/ic/.git-credentials"` |
| 훅이 아예 안 돎 | 세션 시작 후 설정을 바꿈 | `/hooks` 를 한 번 열거나 Claude Code 재시작 |
| `.ps1` 실행 시 `문자열에 종결자가 없습니다` | **PowerShell 5.1은 BOM 없는 UTF-8을 ANSI로 읽어 한글이 깨진다** | 파일을 **UTF-8 with BOM** 으로 저장. 아래 참고 |

한글 주석이 든 `.ps1` 을 새로 만들 때는 반드시 BOM을 넣는다. 2026-08-16에 이걸로 한 번 막혔다.

```powershell
$p = 'scripts\my.ps1'
$t = [System.IO.File]::ReadAllText($p, [System.Text.UTF8Encoding]::new($false))
[System.IO.File]::WriteAllText($p, $t, [System.Text.UTF8Encoding]::new($true))
```

### B-11-7. 알고 쓸 것 (한계)

- **`git add -A` 는 무차별이다.** 새로 생긴 파일을 전부 담는다. 큰 산출물(`.mp4`, 체크포인트,
  데이터셋)이 실수로 올라가지 않게 각 repo의 `.gitignore` 를 먼저 갖춰라. 지금
  `so-arm101-work/.gitignore` 는 `outputs/ videos/ *.mp4 *.hdf5` 를 막아둔 상태다.
- **PAT가 `D:\ic\.git-credentials` 에 평문으로 남는다.** PC방 초기화와 함께 지워지는 것을
  전제로 한 설계다. 초기화되지 않는 자리라면 세션 끝에 직접 지워라.
  ```powershell
  Remove-Item D:\ic\.git-credentials -Force
  ```
- **커밋 메시지가 `auto: N 개 파일 변경` 으로 기계적이다.** 의미 있는 단위로 남기고 싶으면
  중간에 직접 커밋하면 된다. 훅은 남은 변경만 쓸어 담는다.

---

## 버전 고정 (바꾸지 말 것)

| 항목 | 값 | 이유 |
|---|---|---|
| Isaac Sim | **5.1.0** | 핀 안 하면 6.0이 깔림 |
| Python | **3.11** (`D:\ic\env`) | Isaac Sim 5.X 요구. **6.0은 3.12** — 문서 볼 때 혼동 주의 |
| LeRobot | **0.6.1** (`D:\ic\lerobot-env`, **Python 3.12**) | 0.5.0부터 `Requires-Python >=3.12`. Isaac Sim(3.11)과 **같은 env에 못 넣는다** (B-10-1) |
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
| `isaaclab.bat --install` 후 `ModuleNotFoundError: No module named 'isaaclab'` | `flatdict==4.0.1` 빌드가 `pkg_resources` 없어서 조용히 실패 (setuptools 81+). 기보고된 버그: [#4577](https://github.com/isaac-sim/IsaacLab/issues/4577), 수정 [#4581](https://github.com/isaac-sim/IsaacLab/pull/4581) — v2.3.2엔 미포함. **`flatdict==4.0.0` 선점은 안 통한다** (setup.py가 4.0.1 exact pin, 2026-08-16 재실측) | `pip install "setuptools<81"` → `pip install flatdict==4.0.1 --no-build-isolation` → 필요 시 `pip install -e source\isaaclab --no-build-isolation` (B-10 known issue ① 참고) |
| `isaaclab.bat --install` 중 torch 3.3GB 재다운로드 | `isaaclab.bat`이 `--cache-dir`을 하위 pip에 안 물려줌 → 기본 캐시(C:)를 봄 | `$env:PIP_CACHE_DIR='D:\ic\pipcache'` (환경변수는 하위 프로세스로 전파됨) |
| 한글 주석 든 `.ps1`이 엉뚱한 줄에서 `문자열에 종결자가 없습니다` | PowerShell 5.1은 BOM 없는 UTF-8을 ANSI로 읽어 한글이 깨짐 | 파일을 **UTF-8 with BOM**으로 저장 (B-11-6 참고) |
| `RuntimeError: A camera was spawned without the --enable_cameras flag` | 헤드리스 실행 시 카메라는 기본으로 꺼져 있음 | 실행 인자에 `--enable_cameras` 추가. **종료 코드는 0으로 나오니 출력을 직접 볼 것** |
| `lerobot` 은 깔렸는데 `LeRobotDataset` 임포트 실패 | 0.6.1은 데이터셋이 별도 extra | `pip install "lerobot[dataset,training,dataset-viz]==0.6.1"` (B-10-1) |
| `pip install lerobot==0.6.1` 이 `No matching distribution` | env가 Python 3.11 — lerobot 0.5.0+는 3.12 요구 | 3.12로 별도 env (B-10-1). 에러 **첫 줄**의 `Ignored the following versions...` 가 진짜 이유 |
| `rl_games` 설치 중 `Cannot find command 'git'` | 같은 세션에서 방금 깐 git이 하위 pip 프로세스 PATH에 반영 안 됨 | 새 PowerShell 창을 열거나 `$env:PATH`에 `D:\ic\Git\bin` 그 세션에서 직접 추가 |
| `isaaclab.bat --install` 시작하자마자 `The filename, directory name, or volume label syntax is incorrect.` | `pip show torch` 버전 파싱 버그로 항상 재설치 판정 (무해, self-heal) | 무시하고 진행, 끝나면 B-6으로 최종 torch 버전만 재확인 |

상세 분석은 `so-arm101-simtoreal/_logs/` 의 다음 문서들 참조.
- `2026-08-08_isaac-sim이-torch-cpu빌드로-덮어씀.md`
- `2026-08-08_비대화형-설치에서-동의게이트-3종.md`
- `2026-08-08_windows-pip-TEMP가-시스템드라이브로-간다.md`

---

## 부록: NVIDIA SimReady Foundation (선택 — 엔닷라이트 SimReady 스펙 학습·검증용)

[nvidia/simready-foundation](https://github.com/nvidia/simready-foundation)은 NVIDIA가 공개한
**SimReady 자산 스펙의 공식 레퍼런스 구현체**다. `simready-validate` CLI로 USD 에셋을
Requirement → Capability → Feature → Profile 계층에 대해 실제로 검증할 수 있다.

**왜 완전히 별도 환경인가** — 이 도구는 **Python 3.12** 를 요구하는데, Isaac Sim 5.1은
**Python 3.11**로 고정돼 있다(위 「버전 고정」 표 참고). 같은 conda env에 섞으면 버전 충돌이 나므로
Isaac Sim용 `D:\ic\env`와는 완전히 분리된 `D:\ic\simready-env`를 새로 판다. 서로 참조하지 않으므로
설치·삭제 순서는 자유롭다 (Isaac Sim 설치 전/후 아무 때나 해도 됨).

### 부-1. Git 설치 (이 PC방엔 git이 아예 없는 상태로 시작한다)

winget도 없는 자리를 기준으로 한다. PortableGit(7z 자가압축)을 받아 압축만 푼다 — 설치 프로그램이
아니라 관리자 권한이 필요 없다. Git for Windows는 최신 릴리스에 git-lfs가 이미 번들돼 있다
(`Git\mingw64\bin\git-lfs.exe`), 그래서 lfs를 따로 받을 필요가 없다.

```powershell
$ProgressPreference = 'SilentlyContinue'
$rel   = Invoke-RestMethod -Uri 'https://api.github.com/repos/git-for-windows/git/releases/latest' -Headers @{ 'User-Agent' = 'pwsh' }
$asset = $rel.assets | Where-Object { $_.name -like 'PortableGit-*-64-bit.7z.exe' } | Select-Object -First 1
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile 'D:\ic\PortableGit.exe' -UseBasicParsing

Start-Process -FilePath 'D:\ic\PortableGit.exe' -ArgumentList '-o"D:\ic\Git"', '-y' -Wait
& 'D:\ic\Git\bin\git.exe' --version
```

**매 세션마다 PATH에 추가** (PowerShell 창을 새로 열 때마다, 또는 명령마다 필요):
```powershell
$env:PATH = "D:\ic\Git\bin;D:\ic\Git\cmd;D:\ic\Git\mingw64\bin;$env:PATH"
git lfs install     # 최초 1회 — 전역 git config에 LFS 필터를 등록한다
```

### 부-2. Python 3.12 환경 (기존 Miniconda 재사용)

B-1에서 이미 깐 Miniconda로 **두 번째 env**를 만든다. Miniconda 자체를 다시 받을 필요는 없다.

```powershell
& 'D:\ic\miniconda3\Scripts\conda.exe' create -p D:\ic\simready-env python=3.12 -y --override-channels -c conda-forge
```

### 부-3. 저장소 clone + LFS 자산 받기

`git clone`만으로는 USD·이미지 같은 LFS 추적 파일이 포인터만 받아진다. `git lfs pull`이 실제
바이너리(샘플 콘텐츠 포함 약 3.3GB)를 내려받는다 — 이 단계가 제일 오래 걸린다.

```powershell
$env:PATH = "D:\ic\Git\bin;D:\ic\Git\cmd;D:\ic\Git\mingw64\bin;$env:PATH"
New-Item -ItemType Directory -Force D:\ic\repos | Out-Null
git clone https://github.com/NVIDIA/simready-foundation.git D:\ic\repos\simready-foundation
Set-Location D:\ic\repos\simready-foundation
git lfs pull
```

### 부-4. 의존성 설치

```powershell
$env:TEMP='D:\ic\tmp'; $env:TMP='D:\ic\tmp'
& 'D:\ic\simready-env\python.exe' -m pip install --upgrade pip
& 'D:\ic\simready-env\python.exe' -m pip install -r D:\ic\repos\simready-foundation\requirements.txt --cache-dir D:\ic\pipcache
```

### 부-5. 검증

```powershell
& 'D:\ic\simready-env\Scripts\simready-validate.exe' --help
```

저장소 안의 `sample_content/`에 이미 샘플 에셋이 들어 있어서 다운로드 없이 바로 실제 검증을
돌려볼 수 있다. 그리퍼로 쥐는 물체(`coffee_cup_grasp_a01`)로 확인한 결과 — **2026-08-10 실측**:

```powershell
Set-Location D:\ic\repos\simready-foundation
& 'D:\ic\simready-env\Scripts\simready-validate.exe' --project-config sample_content\project_config.toml `
  --profile Prop-Robotics-Physx --version 1.0.0 `
  sample_content\common_assets\props_general\coffee_cup_grasp_a01\simready_physx_usd\sm_coffee_cup_grasp_a01_01.usd
```
```
Asset: sample_content\common_assets\props_general\coffee_cup_grasp_a01\simready_physx_usd\sm_coffee_cup_grasp_a01_01.usd
  [PASSED] Prop-Robotics-Physx v1.0.0
```

`--output result.json`을 붙이면 어떤 Feature(FET003_BASE_PHYSX, FET004_BASE_PHYSX 등)가
각각 통과했는지 구조화된 JSON으로 남길 수 있다 — 이 프로필 하나가 내부적으로 8개 Feature,
그 밑에 다시 수십 개 Requirement로 쪼개져 있다는 걸 로그에서 직접 확인할 수 있다.

### 참고 — 지금 실습과 바로 연결되는 샘플 에셋

저장소 안에 UR10과 Robotiq 2F-85 그리퍼 샘플이 이미 들어 있다. Isaac Sim에서 그리퍼 어셈블·
게인 튜닝을 연습한 결과물을, 여기서 공식 SimReady 프로필(`Robot-Body-Runnable` 등)로 검증해보는
흐름을 만들 수 있다.
```
D:\ic\repos\simready-foundation\sample_content\common_assets\robots_general\ur10\simready_isaac_usd\ur10.usd
D:\ic\repos\simready-foundation\sample_content\common_assets\robots_general\Robotiq\2F-85\simready_isaac_usd\Robotiq_2F_85.usda
```

---

## 이 환경의 한계 (알고 쓸 것)

- **VRAM 12GB < 공식 최소 16GB** — 로봇 1대 수준 씬은 실측상 문제없다.
  무거운 멀티카메라 렌더링·Cosmos 추론은 이 PC에서 포기한다.
- **매 세션 초기화** — 결과물은 반드시 GitHub에 푸시하고 환경은 USB에 백업한다.
  중간에 1시간마다 커밋하는 습관을 들인다.
- **장시간 학습 불가** — 자리를 뜨면 날아간다. RL 학습 같은 건 AWS로 가야 한다.
  이 PC방은 **씬 구축·검증·디버깅** 용도로만 쓴다.
