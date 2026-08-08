# 여기서부터 이어서 — 다음 세션 시작 문서

> **PC방에 도착하면 이 파일부터 엽니다.**
> 마지막 세션: **2026-08-08**

```
git clone https://github.com/grim132435-boop/Isaac-simready-validation.git
cd Isaac-simready-validation
```

---

## 0. 도착하자마자 (순서대로)

환경은 **초기화돼서 없습니다.** 다시 설치해야 합니다. 다만 설치는 대부분 대기 시간이라,
**먼저 걸어놓고 공부하는 순서**로 갑니다.

| # | 할 일 | 시간 | 비고 |
|---|---|---|---|
| 1 | `nvidia-smi` 로 자리 확인 | 1분 | GPU·VRAM·드라이버 |
| 2 | [설치 가이드](docs/PC방_환경_재구축_가이드.md) **경로 B** 를 위에서부터 | 5분 조작 | B-4에서 다운로드 시작되면 손 뗌 |
| 3 | **설치 도는 동안** 아래 §2 복습 | 25분 | 대기 시간 활용 |
| 4 | 설치 완료 후 §3 실습 | 나머지 | |
| 5 | 떠나기 전 `git push` | 3분 | |

> ### 설치 문서는 오늘 처음 실행됐고, 오류가 나왔습니다
> 문서를 **"정답"이 아니라 "1차 초안"** 으로 다뤄 주세요.
> 막히는 지점이 나오면 그 자리에서 고치고 커밋하시면 됩니다. 그래야 문서가 진짜가 됩니다.
> 오늘 이미 두 건 잡았습니다 (§4 참조).

---

## 1. 현재 상태

### 완료된 것

**환경 (검증됨, 단 초기화로 소실)**
- Isaac Sim 5.1.0 + Python 3.11.15 + torch 2.7.0+cu128
- RTX 5070 (sm_120 Blackwell) 에서 PhysX 스텝·CUDA 연산 모두 확인
- 스모크 테스트 통과 (`cube z: 1.0000 → 0.1000`)

**P1 측정 — 실측 완료, 원자료 저장됨**

| 실험 | 파일 | 결과 |
|---|---|---|
| 게인 스윕 | [results/p1_sweep.csv](results/p1_sweep.csv) | 중력 처짐 **0.0741° → 0.0021° (97% 감소)** |
| 주파수 스캔 | [results/p1_freqscan.csv](results/p1_freqscan.csv) | 오차 ∝ 주파수 → **고정 지연 τ ≈ 26ms** |
| payload 스캔 | [results/p1_payload.csv](results/p1_payload.csv) | 정적 처짐만 5.4배, **동적 오차는 0.09% 불변** |

**문서 4종**

| 문서 | 용도 |
|---|---|
| [핵심개념_정리.md](docs/핵심개념_정리.md) | USD/PhysX/Kit 용어 지도. **먼저 읽을 것** |
| [학습커리큘럼](docs/학습커리큘럼_Isaac_Sim_기초부터_면접까지.md) | STEP 0~8. 예측→실행→자가진단 |
| [GUI 실습 가이드](docs/GUI_실습_URDF임포트_게인튜닝_중력보상.md) | 클릭 순서 레퍼런스 |
| [PC방 환경 재구축](docs/PC방_환경_재구축_가이드.md) | 설치 |

> 개념 문서 웹 버전 (렌더링 걱정 없음, 폰에서도 열림):
> https://claude.ai/code/artifact/663a729f-7c68-4406-bed4-c39d2ae7aa6c

**막힘 로그 3건** — `so-arm101-simtoreal/_logs/` 에 있습니다.
torch CPU 빌드 덮어쓰기 / 비대화형 동의 게이트 / Windows pip TEMP.

### 진행 중이던 것

GUI로 `cobotta_pro_900` 임포트까지 완료. collider 시각화로 확인하던 중이었습니다.

---

## 2. 설치 대기 중 복습할 것

### 아직 못 푼 문제 — 이게 제일 중요합니다

퀴즈 12문항 중 **4·5번이 유일한 실질 약점**으로 진단됐습니다. 답은 설명을 들었지만
**직접 도출한 적이 없습니다.**

> **4.** 중력 처짐(정적)은 게인으로 97% 줄었는데, 궤적 추종오차(동적)는 게인을 1000배 올려도
> 안 줄었다. 물리적으로 왜 그런가?
>
> **5.** 그게 "지연 때문"임을 어떤 실험으로 증명하나?

설치 도는 동안 **답을 종이에 써 보시면** 좋겠습니다. 막히면 [README 결과 절](README.md)에
전체 설명이 있습니다.

### 개념 확인
[핵심개념_정리.md](docs/핵심개념_정리.md) 에서 특히:
- **Type(하나) vs API(여러 개)** — `.Apply()` 구조. 엔닷라이트 사업의 핵심
- **Drive Type: Acceleration vs Force** — 관성 정규화 여부
- **제조사 게인을 왜 안 쓰는가** — 물리 파라미터 vs 모델링 선택

---

## 3. 설치 완료 후 — 다음 실습

### 우선순위 1 — GUI 실습 (STEP 1~5)

내가 대신 못 하는 영역이고, 실무 면접에서 라이브로 요구될 수 있는 부분입니다.

- [ ] **STEP 1** 큐브 물리 실험 — RigidBody만 있고 Collider 없으면 바닥을 통과할까?
- [ ] **STEP 2** URDF 임포트. 경로는 아래 §5
- [ ] **STEP 3** Property 패널에서 **Drive > Stiffness 실제 값 확인**
      → Natural Frequency 25 / ζ 0.005 가 어떤 Kp로 변환됐는지.
      **관절마다 값이 다를 것** — 그게 `Kp = m·ωn²` 의 m 때문입니다
- [ ] **STEP 4** 게인 극단값 4조합. 특히 stiffness 10만 / damping 10 조합
- [ ] **STEP 5** Disable Gravity 켜고 **로봇 위에 큐브 올려보기**
      → 물체 무게를 느끼는지 직접 확인 (6번 퀴즈 검증 실험)

### 우선순위 1.5 — ωn 비교 실험 (근거가 새로 생김)

임포터 기본값은 **ωn=25**인데, NVIDIA 공식 매니퓰레이터 튜토리얼은 UR10e에 **ωn=300**을
쓰라고 지시한다. `Kp = m·ωn²` 이므로 **144배** 차이다.

| 조합 | 예상 | 실측 |
|---|---|---|
| ωn=25, ζ=0.005 (임포터 기본) | 처짐 큼 | [ ] |
| **ωn=300, ζ=0.005 (NVIDIA 권장)** | 처짐 작음, 진동은? | [ ] |
| ωn=300, ζ=1.0 | 처짐 작고 진동 없음, 대신 느림 | [ ] |

**핵심 질문 — NVIDIA는 왜 ζ를 올리지 않고 ωn만 올릴까?**
직접 보고 답을 만들면 *"기본값을 그대로 쓰셨나요?"* 에 대한 답이 된다.

### 우선순위 2 — 아직 아무도 안 한 실험 ★

`PHYSICS_DT` 를 `1/120` → `1/240` 으로 바꾸고 지연 τ 를 다시 측정합니다.

**먼저 예측하고 실행하세요:**
- (a) τ 가 26ms → 13ms 반토막 → 지연은 **고정 스텝 수** (솔버 파이프라인)
- (b) τ 가 26ms 그대로 → 지연은 **고정 실시간** (다른 원인)

각 경우가 무엇을 의미하는지 적고 나서 돌리시면 됩니다.
**제가 안 해본 실험이라, 하시면 정혁님 발견입니다.**

### 우선순위 3 — 마무리 못 한 것
- [ ] 주파수 스캔 4번째 점(1.0 Hz) 미기록 — `--freq-scan` 재실행하면 됩니다
      (현재 3점. **"4점"이라고 말하면 안 됩니다**)
- [ ] Notion 포트폴리오 페이지 — **발견을 직접 설명할 수 있게 된 다음에** 쓰는 게 맞습니다

---

## 4. 오늘 발견된 문서 오류 (같은 패턴을 예상하세요)

| # | 무엇 | 어떻게 발견 |
|---|---|---|
| 1 | STEP 2의 `get_extension_path_from_name()` 명령 — Kit 커널 부팅 실패 | 실행해보려다 |
| 2 | "Convex Hull이 그리퍼 사이를 메운다" — **틀림.** Hull은 링크별 적용 | collider 시각화로 확인 |

둘 다 **문서를 읽기만 했으면 안 나왔을 오류**입니다. 실행하고 눈으로 봐서 나왔습니다.
내일도 같은 자세로 가시면 됩니다 — **문서와 화면이 다르면 화면이 맞습니다.**

---

## 5. 자주 쓰는 것

### 환경 변수 (매 PowerShell 창마다)
```powershell
$env:TEMP='D:\ic\tmp'; $env:TMP='D:\ic\tmp'
$env:OMNI_KIT_ACCEPT_EULA='YES'
```

### GUI 실행
```powershell
D:\ic\env\Scripts\isaacsim.exe
```

### 스크립트 실행
```powershell
& 'D:\ic\env\python.exe' -u scripts\smoke_test.py
& 'D:\ic\env\python.exe' -u scripts\p1_drive_tuning.py --sweep
& 'D:\ic\env\python.exe' -u scripts\p1_drive_tuning.py --freq-scan
& 'D:\ic\env\python.exe' -u scripts\p1_drive_tuning.py --payload-scan
```
`-u` 는 필수입니다. 없으면 출력이 버퍼링돼서 안 보입니다.

### 동봉 로봇 URDF 경로
```
D:\ic\env\Lib\site-packages\isaacsim\exts\isaacsim.asset.importer.urdf\data\urdf\robots\
  ├ ur10               협동로봇 (P1에서 사용)
  ├ cobotta_pro_900    협동로봇 + 그리퍼 (오늘 임포트한 것)
  ├ franka_description 논문·예제 표준
  ├ carter / kaya      모바일 (Fix Base 끄는 경우)
  └ cartpole           관절 1개 최소 예제
```
경로가 바뀌었으면 (Isaac Sim 안 띄우고):
```powershell
Get-ChildItem D:\ic\env -Recurse -Filter ur10.urdf | Select-Object -ExpandProperty FullName
```

### 주의
- **GUI와 스크립트를 동시에 돌리지 마세요.** Isaac Sim 인스턴스가 둘 뜨면 VRAM 12GB에 부담입니다
- 첫 실행은 셰이더 컴파일로 수 분 걸립니다. 멈춘 게 아닙니다

---

## 6. 면접 관련

**엔닷라이트 Robot Application Engineer — Alignment Call 준비 중**
전형: 서류 → **Alignment Call** → 실무면접 → C-Level → 입사합의

가장 강한 카드는 **10번 퀴즈의 답**입니다. 기사에서 대표가
*"가상-현실 일치도 80%가 충분한가 95%인가 기준이 없다"* 고 한 지점에 대해,
오늘 측정이 **"단일 %가 아니라 원인별로 분해해서 보고해야 한다"** 는 구체적 답을 줍니다.

- 정적 오차 → 게인·payload 모델링에 반응
- 동적 오차 → 지연에만 반응, **게인으로는 원리적으로 못 줄임**

압박 질문 대비는 [학습커리큘럼 STEP 8](docs/학습커리큘럼_Isaac_Sim_기초부터_면접까지.md) 에 있습니다.
특히 이 둘이 위험합니다:
- *"이거 튜토리얼 따라한 거 아닌가요?"*
- *"저희는 로봇이 아니라 에셋을 만듭니다. 이 경험이 왜 관련 있죠?"*
