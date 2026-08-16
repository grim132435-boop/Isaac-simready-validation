---
type: reference
project: Isaac-simready-validation
updated: 2026-08-16
tags: [isaac-sim, 레퍼런스, 도구]
---
# 레퍼런스 — Isaac Sim 도구(익스텐션) 카드

> 🌐 **통합 웹 매뉴얼** — https://claude.ai/code/artifact/52ad7d3c-f237-4329-809f-c058a6123a5b
> 용어(articulation, Layer, Drive 등) → [레퍼런스_IsaacSim_용어사전.md](레퍼런스_IsaacSim_용어사전.md)

**왜 따로 뺐나** — 익스텐션은 한 줄 정의로 부족하다. 그 자리에서 창을 열고 조작해야 하므로 「이게 뭔지」보다 **어디서 열고 · 어떤 필드가 뭘 하고 · 뭘 누르는지**가 필요하다.

| # | 도구 | 메뉴 경로 | 언제 |
|---|---|---|---|
> ### 에셋 어디 있나
> pip 설치본에는 **Nucleus가 없어서** Content 브라우저의 `omniverse://`가 비어 있다. 샘플 에셋은 `Isaac Sim Assets [Beta]` 탭 또는 로컬 다운로드로 쓴다.
> ```powershell
> powershell -ExecutionPolicy Bypass -File scripts\fetch_tutorial_assets.ps1
> # -> D:\ic\assets\vendor\Manipulator\
> ```
> 폴더 설계는 [용어 §3.3](레퍼런스_IsaacSim_용어사전.md#33-실험-프로젝트-폴더-구조).

| 1 | [Gain Tuner](#1-gain-tuner) | `Tools > Robotics > Asset Editors > Gain Tuner` | 드라이브 게인 튜닝 |
| 2 | [Robot Assembler](#2-robot-assembler) | `Tools > Robotics > Asset Editor > Robot Assembler` | 로봇 + 그리퍼 조립 |
| 3 | [Physics Inspector](#3-physics-inspector) | `Tools > Physics > Physics Inspector` | 관절 즉석 검증 |
| 4 | [Mesh Merge Tool](#4-mesh-merge-tool) | `Tools > Robotics > Asset Editors > Mesh Merge Tool` | 에셋 최적화 |
| 5 | [Lula Robot Description Editor](#5-lula-robot-description-editor) | `Tools > Robotics > Lula Robot Description Editor` | 모션 플래닝 설정 |
| 6 | [URDF Importer](#6-urdf-importer) | `File > Import` | URDF → USD |

---

# 1. Gain Tuner

articulation의 Stiffness/Damping을 조정하고 테스트 궤적을 돌려 추종 결과를 플롯으로 본다. 기본 활성화.

## 1.1 물리 모델

```
τ = Stiffness × (q − q_target) + Damping × (q̇ − q̇_target)

ωₙ = √(K_p / m)          ζ = K_d / (2·m·ωₙ)
```

`m` = 관절 등가 관성 → 관절마다 다름. 상세는 [용어 §2.11](레퍼런스_IsaacSim_용어사전.md#211-natural-frequency--damping-ratio).

## 1.2 드라이브 모드

| 모드 | 조건 | 대상 |
|---|---|---|
| Position | Stiffness > 0 | 관절 대부분 |
| Velocity | Stiffness = 0, Damping > 0 | 바퀴 · 컨베이어 |
| **None** | 둘 다 0 | 토크 제어 — 게인이 안 먹음 |
| Mimic | 다른 관절 종속 | 그리퍼 팔로워 |

## 1.3 파라미터화

Stiffness/Damping 직접 입력 ↔ ωₙ/ζ 중 선택. 자동 변환. **저장은 항상 Stiffness로.**

## 1.4 튜닝 절차 — 위치 드라이브

```
1. Damping = 0                    미분항 없이 시작
2. Stiffness만 ↑                  목표 근처 수렴 시작점 탐색
3. Stiffness ÷ 10                 여유를 둔다
4. Damping = Stiffness ÷ 10       baseline
5. 둘을 미세조정                   안정성 · 반응속도 · 오버슈트
6. 오버슈트 1% 이내 → 종료         초과 시 5로 반복
```

**산업용(제조사 PD 튜닝됨)**
- baseline stiffness **× 2**
- `Joint > Advanced > Maximum Joint Velocity`로 스펙 제한
- 시뮬 속도가 한계 내인지 보며 재조정

**속도 드라이브(바퀴)**
- Stiffness = 0 고정 → Damping만 ↑ → 목표 속도 수렴
- 예상 부하만큼 **+10%** 여유
- Max Joint Velocity / Max Force로 상한

## 1.5 Gains Testing

사인파 또는 계단(Step) 궤적.

| 파라미터 | 의미 |
|---|---|
| Sequence | 관절 테스트 순서 |
| Period | 파형 주기 |
| **Phase** | 위상 오프셋 → 아래 함정 |
| Amplitude | 진폭 |
| Step limits | 계단 입력 범위 |

> **⚠ 위상 함정 — 자체 경험.** 관절마다 다른 위상 → t=0에서 큰 계단 입력 → **초기 과도응답이 통계를 지배.**
> 위상 정렬 + 초기 구간 통계 제외 후 `track_max` **10.02° → 2.15°**.

## 1.6 결과 읽기

- 지령 vs 실제 추종 위치·속도 플롯
- 좌측 패널에서 관절 선택 (단일 / Ctrl 다중 / Shift 범위)
- **테스트가 끝나야 플롯이 나온다** — 도는 중엔 안 보임

## 1.7 저장

**Save Gains to Physics Layer** → 조인트가 정의된 `asset_physics.usd` 탐색.
[권장 에셋 구조](레퍼런스_IsaacSim_용어사전.md#32-권장-에셋-구조)를 안 따르면 저장 위치를 못 찾는다. 권한 문제 등이면 현재 스테이지에 로컬 오버라이드.

## 1.8 실전 기준

| 기준 | 값 |
|---|---|
| 목표 오버슈트 | **1% 이내** |
| 중력보상 내장 로봇 | Disable Gravity 켜고 순수 제어 응답만 |
| 튜닝 순서 | 관절을 **소그룹으로** 먼저. 6축 동시 튜닝 금지 |
| 최대속도 | 임포터 기본값은 비현실적 → 실제 스펙으로 낮춤 |

## 1.9 안 될 때

- **드롭다운이 비었다** → [Robot Schema](레퍼런스_IsaacSim_용어사전.md#31-robot-schema--isaacrobotapi) 확인
- [Issue #104](https://github.com/isaac-sim/IsaacSim/issues/104) 게인 튜닝 문제
- [Issue #186](https://github.com/isaac-sim/IsaacSim/issues/186) **Run Test 버튼 선택 불가**
- GUI가 안 먹으면 Property 직접 수정 또는 스크립트 우회 → **감점이 아니라 가점**
- 스크립트 버전: [scripts/p1_drive_tuning.py](../scripts/p1_drive_tuning.py)

**복귀** — [실습 §7](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#7-gain-tuner-절차--표준-튜닝-알고리즘-tutorial-11) · Tutorial 11
**원문** — [Gain Tuner Extension](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_robot_setup_gain_tuner.html)

---

# 2. Robot Assembler

두 USD 에셋을 **물리적으로 시뮬레이션되는 Fixed Joint**로 연결. 그리퍼를 팔에, 팔을 이동 베이스에.

## 2.1 UI 필드

| 필드 | 의미 |
|---|---|
| Select Base Robot | 붙임을 받는 쪽 (`/ur`) |
| Base Attach Point | 베이스 부착 링크 (`wrist_3_link`) |
| Select Attach Robot | 붙는 쪽 (`/ur/ee_link`) |
| Attach Point | 그리퍼 베이스 링크 |
| Assembly Namespace | 구성 이름표. 기본 `Gripper` |

부착점은 **Robot Link** 또는 **Reference Point** 중 선택. 위치 조정은 X/Y/Z 90° 회전 버튼 + 뷰포트 기즈모.

## 2.2 버튼 흐름

```
Begin Assembling Process → (자세 정렬) → Assemble and Simulate → End Simulation And Finish
                                          ↑ 물리를 실제로 돌려 접합부 확인
```

## 2.3 USD에 생기는 것

1. 설정 파일 `configuration/<robot>_<namespace>_<attach_robot>.usd`
2. 로봇 인터페이스 레이어에 **VariantSet 생성** → 그 로봇을 쓰는 모든 곳에서 부착물 선택 가능 ([Variant](레퍼런스_IsaacSim_용어사전.md#15-variant--variantset))
3. **붙는 쪽의 Articulation Root 제거**

## 2.4 주의

| 항목 | 내용 |
|---|---|
| **물리는 Play 중에만** | *"physics is only simulated while the timeline is playing"* — 정지 상태에선 접합이 동작하지 않음 |
| 시작 전 정렬 필수 | 어긋난 채 시작하면 불안정 |
| 정적 부착엔 불필요 | 로봇↔테이블 정도면 그냥 Fixed Joint |
| 조립 후 물리 튜닝 | 솔버 iteration 등 조정 필요 |

**복귀** — [실습 §3](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#3-robot-assembler로-두-articulation-합치기) · Tutorial 6
**원문** — [Robot Assembler](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/assemble_robots.html)

---

# 3. Physics Inspector

**Play 없이** 관절을 슬라이더로 직접 움직여 보는 검증 도구.

## 3.1 순서

1. Stage에서 대상 articulation 선택
2. **원형 화살표(refresh)** 클릭
3. 관절별 슬라이더로 목표 위치 변경

## 3.2 무엇을 잡나

| 확인 | 증상 해석 |
|---|---|
| 관절 축·방향 | 엉뚱한 방향으로 돌면 → 임포트 시 축 뒤집힘 |
| 관절 제한 | 슬라이더가 예상 범위를 벗어남 |
| 클로즈드루프 | 손가락 ragdoll 자유회전 = 드라이브 미설정 (이 단계선 정상) |
| 자기 충돌 | 손가락 관통 = self-collision 꺼짐 (초기엔 정상) |

## 3.3 ⚠ 쓰고 나면 반드시 창을 닫을 것

> *"Since the Physics Inspector partially initializes `omni.physx`, it is expected for general
> simulations to not behave properly. Such behaviour can be reversed by simply closing the
> Physics Inspector window/panel."*

열어둔 채 일반 시뮬을 돌리면 거동이 틀어진다. 모르면 **「게인을 바꿨는데 결과가 이상하다」의 원인을 못 찾는다.**

**복귀** — [실습 §4-4](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#4-4-physics-inspector로-즉석-검증) · Tutorial 7 / 10
**원문** — [Physics Inspector](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/physics/joint_inspector.html)

---

# 4. Mesh Merge Tool

한 강체에 흩어진 시각 메시 수십 개를 하나로 병합. CAD 임포트 직후 성능 개선의 첫 수단.

## 4.1 순서

1. 병합할 링크 Prim 선택 (예: `Jetbot/left_wheel`)
2. **Combine Materials** 체크
3. 재질 저장 위치를 `<로봇>/Looks`로 지정
4. **Merge**
5. 결과 메시(`/Merged/left_wheel`)의 **transform 클리어**
6. `Visuals` Scope로 이동 후 `/Merged` 삭제

## 4.2 왜 효과가 있나

렌더링 비용은 **메시 개수(draw call)** 에 비례하는 부분이 크다. 폴리곤 총량이 같아도 개수를 줄이면 가벼워진다. Jetbot 예제 **40 → 64 FPS**.

## 4.3 함께 쓰는 것

- [Instancing](레퍼런스_IsaacSim_용어사전.md#16-instanceable) — 동일 부품 메모리 공유
- **콜라이더 단순화** — 시각 메시보다 콜라이더가 성능 영향이 크다. 바퀴는 실린더/구로 근사

**복귀** — [실습 §8](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#8-에셋-최적화--로봇그리퍼를-가볍게-만들기-tutorial-12) · Tutorial 12
**원문** — [Merge Mesh Utility](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/ext_isaacsim_util_merge_mesh.html)

---

# 5. Lula Robot Description Editor

모션 플래너(RMPFlow / cuMotion / Lula IK)용 **로봇 기술 파일 + 충돌 구체** 생성.
`Window > Extensions`에서 "Lula" 활성화 필요.

## 5.1 ⚠ 사전 작업 — 안 하면 진행 불가

`visuals`·`collisions` Prim의 **Instantiable 해제**. Lula는 인스턴스화된 메시 미지원.

## 5.2 절차

```
1. PLAY 시작                  ← ★ 중간에 멈추면 처음부터
2. Selection Panel에서 articulation 선택
3. Set Joint Properties       팔 = Active Joint, 그리퍼 = Fixed Joint
4. Link Sphere Editor         링크별 충돌 구체 생성
5. Export To File             ur10e.yaml (+ 선택적 .xrdf)
6. 그 다음에야 정지
```

구체 생성도 내보내기도 Play 상태를 요구한다.

## 5.3 충돌 구체 파라미터

| 항목 | 값 예 |
|---|---|
| Select Mesh | `/collisions/upperarm/mesh` |
| Radius Offset | `0.03` |
| Number of Spheres | `8` |

생성 전 빨강 → **Generate Spheres** 후 청록.

**튜닝 기준**
- 링크를 감쌀 만큼 크되 솔버가 힘들 만큼 크면 안 됨
- 개수 ↑ = 정확도 ↑, 솔버 속도 ↓
- 보통 collision 메시 기준 (visual이 더 나은 근사면 예외)
- 긴 팔 링크는 양 끝에 생성 후 **Add Spheres**로 균등 분포
- 워터타이트 아닌 메시는 수동 추가

**복귀** — [실습 §5](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#5-요약-config-파일-생성--pickplace--tutorial-89) · Tutorial 8

---

# 6. URDF Importer

`File > Import` · 익스텐션 `isaacsim.asset.importer.urdf`. 연습용 로봇이 동봉돼 있어 별도 다운로드 불필요.

```
D:\ic\env\Lib\site-packages\isaacsim\exts\isaacsim.asset.importer.urdf\data\urdf\robots\
  ├ ur10               협동로봇 · P1에서 사용
  ├ cobotta_pro_900    팔+그리퍼 통합
  ├ franka_description 팔+그리퍼 통합 · 논문·예제 표준
  ├ carter / kaya      모바일 · Fix Base 끄는 경우
  └ cartpole           관절 1개 최소 예제
```

경로가 바뀌었으면 (Isaac Sim 안 띄우고):
```powershell
Get-ChildItem D:\ic\env -Recurse -Filter ur10.urdf | Select-Object -ExpandProperty FullName
```

## 6.1 주요 옵션

| 옵션 | 판단 기준 |
|---|---|
| Fix Base Link | 매니퓰레이터 ON · 모바일/휴머노이드 OFF |
| Joint Drive Type | **None(토크제어)이면 stiffness/damping이 0으로 들어감** |
| Natural Frequency / Damping Ratio | [용어 §2.11](레퍼런스_IsaacSim_용어사전.md#211-natural-frequency--damping-ratio) |
| Self Collision | 보통 OFF. 켜면 무겁고 오탐 |
| Density | URDF에 `<inertial>` 있으면 0으로 두고 URDF 값 사용 |
| Distance Scale | URDF는 m 단위. 스테이지도 m면 1 |
| Base Type | Fixed = world-to-root fixed joint 추가 / Mobile = 제거 |
| Robot Type | Manipulator로 두면 Gain Tuner가 자동 인식 |

**Colliders 탭**

| 옵션 | 판단 기준 |
|---|---|
| Collision From Visuals | URDF에 `<collision>` 없을 때만 |
| Convex Hull | 기본값. 빠르나 오목부가 메워짐 |
| Convex Decomposition | 그리퍼 손가락 등 오목 형상이 중요할 때 |
| Bounding Sphere / Cube | 가장 가벼움 |

## 6.2 이 경고는 정상

```
link ee_link has no body properties (mass, inertia, or collisions)
and is being merged into wrist_3_link
```

`ee_link`는 좌표 기준용 더미 링크(질량 없음) → 임포터가 앞 링크로 병합.
**payload를 실을 실제 말단 링크는 `wrist_3_link`.**

## 6.3 ⚠ 이 경고는 정상이 아니다 — Collision From Visuals

```
triangle mesh collision (approximation None/MeshSimplification) cannot be
a part of a dynamic body, falling back to convexHull: /World/ur10/base_link/visuals
```

**경로 끝의 `visuals`가 진짜 원인이다.** approximation을 바꾸라는 말로 읽히지만 아니다.

| 잘못된 것 | 결과 |
|---|---|
| `Collision From Visuals` **ON** | URDF의 정확한 `<collision>`을 버리고 시각 메시를 콜라이더로 씀 |
| Collider Approximation = None / MeshSimplification | 동적 강체에 불가 → convexHull 강제 폴백 |

**실측 (ur10.urdf)** — `<collision>` 15개가 **전부 primitive**(cylinder 14 + box 1)인데 임포트는 `.obj` 시각 메시 7개를 쓰고 있었다. forearm 3.6MB · upper_arm 3.7MB를 cylinder 하나로 될 걸로 계산하던 셈.

**해결** — 재임포트 시 Colliders 탭에서 **Collision From Visuals 끄기**. 이 옵션은 URDF에 `<collision>`이 **없을 때만** 켠다.

## 6.4 ⚠ 직접 임포트한 에셋 vs 배포본은 내용이 다르다

같은 `robotiq_2f_140.urdf`라도 **직접 임포트하면 배포본과 다른 결과**가 나온다. 실측 비교.

| | 배포본 (S3) | 직접 URDF 임포트 |
|---|---|---|
| `/colliders` 최상위 스코프 | ✓ | ✓ |
| **물리재질** | ✓ `Looks/PhysicsMaterial` (1.0/1.0) | **✗ 0개** |
| Looks 내용 | `PhysicsMaterial`, `DefaultMaterial`, `material_*` | `material_191919`, `material_CAD1EE`, `material_E6E6E6` |
| 메시 프림 이름 | `mesh` | `node_STL_BINARY_` |
| RigidBody 수 | 7 | 9 (coupling·pad 링크 추가) |
| 산출물 | — | `*.tmp.usd` (메시 변환 잔여물) |

**Looks에 hex 이름(`material_191919`) 재질만 보이면 직접 임포트한 것이다.** URDF의 색상값에서 임포터가 자동 생성한 이름이다.

**의미** — Tutorial 7이 "재질은 이미 있으니 바인딩만 하라"고 하는 건 **배포본 기준**이다. 직접 임포트했다면 **재질 생성부터** 해야 한다.

## 6.5 URDF에 관성텐서가 없으면

```
ur10.urdf:  <inertial> 7개 · <mass> 7개 · <inertia> 0개 · <dynamics> 0개
```

`<inertia>`(관성텐서)가 0개면 임포터가 형상에서 **추정**한다. 그 추정이 실제 articulation 질량행렬과 어긋난다.

**증상** — 임포트 시 `ωₙ=25`로 균일하게 넣었는데 Gain Tuner가 읽는 실제 고유진동수는 **0.86~76 Hz로 88배 흩어진다.**

**의미** — "Natural Frequency를 300으로 설정하라"는 지침도 관성 추정이 맞아야 성립한다. **ωₙ 표시값을 목표로 삼지 말고 Run Test 응답으로 검증할 것.**

**복귀** — [실습(기본) §2](GUI_실습_URDF임포트_게인튜닝_중력보상.md#2-urdf-임포트-gui)
**원문** — [Import URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html)

---

## 아직 안 정리 (만나면 추가)

- Robot Wizard [Beta] — `robot_wizard.html`
- Simulation Data Visualizer — `physics/ext_isaacsim_inspect_physics.html`
- USD to URDF Exporter — Tutorial 8의 `File > Export URDF`
- Onshape Importer — 조인트 180° 뒤집힘 이슈
- Asset Validation — `asset_validation.html`
