# 레퍼런스 — Isaac Sim 용어·구조 사전

> 🌐 **통합 웹 매뉴얼** — https://claude.ai/code/artifact/52ad7d3c-f237-4329-809f-c058a6123a5b
> 실습 + 레퍼런스가 한 페이지. 용어에 마우스를 올리면 정의 팝오버, 클릭하면 해당 항목으로 이동.
> Isaac Sim이 메인 화면을 쓰므로 작업 중엔 이쪽을 띄워두는 편이 낫다.

**목적** — 공식 튜토리얼의 초록 하이퍼링크를 원문 대신 여기서 확인하고 즉시 실습 복귀.
**범위** — Robot Setup Tutorials 6~12.
**도구(익스텐션)** → [레퍼런스_IsaacSim_도구.md](레퍼런스_IsaacSim_도구.md)

## 왜 필요했나

- Tutorial 10 도입부 한 화면에 초록 링크 10개 — `USD Layers` `closed loop` `mimic joints` `collision shapes` `Omnigraph` `Gain Tuner` …
- 하나씩 눌러 원문 정독 → 맥락 끊김 → 실습 없이 읽어 이해 안 됨 → 돌아오면 어디였는지 잊음 → 진도 정체
- 해결: 항목마다 `한 줄 정의` + `실습에서 할 일` + `복귀 지점`

## 빠른 조회

| 막힌 지점 | 항목 |
|---|---|
| Layer가 뭔데 파일이 여러 개지 | [§1.3](#13-layer--sublayer) |
| articulation이 뭐고 왜 root가 하나여야 하지 | [§2.3](#23-articulation) |
| closed loop가 왜 문제지 | [§2.4](#24-closed-loop) |
| Exclude From Articulation 체크하면 뭐가 달라지지 | [§2.5](#25-exclude-from-articulation) |
| Stiffness/Damping을 뭘 기준으로 넣지 | [§2.8](#28-joint-drive) · [§2.11](#211-natural-frequency--damping-ratio) |
| Mimic Joint의 gearing이 뭐지 | [§2.9](#29-mimic-joint) |
| Convex Hull / Decomposition 뭘 고르지 | [§2.7](#27-collider-approximation) |
| Variant / Instanceable이 뭐지 | [§1.5](#15-variant--variantset) · [§1.6](#16-instanceable) |
| IsaacRobotAPI에 뭘 등록하라는 거지 | [§3.1](#31-robot-schema--isaacrobotapi) |
| **프림이 비어 보이고 mass·joint 편집이 안 돼** | [§1.4 Payload 함정](#14-합성-방식-4종--sublayer--reference--payload--add-on) |
| **조립본에서 그리퍼 설정이 안 돼** | [§1.6 실사례](#16-instanceable) · [§3.2 물리 레이어](#32-권장-에셋-구조) |
| 다이어그램 화살표 색이 뭘 뜻하지 | [§1.4](#14-합성-방식-4종--sublayer--reference--payload--add-on) |
| 폴더를 어떻게 놔야 하지 | [§3.3](#33-실험-프로젝트-폴더-구조) |

---

# 1. USD 구조

씬을 기술하는 포맷이자 **합성(composition) 시스템**. 파일 하나에 씬 하나가 아니라 여러 파일을 겹쳐 하나의 씬을 만든다.

## 1.1 Prim

- 씬 트리의 노드. Stage 패널에 보이는 항목 전부
- Type 1개 + API Schema 여러 개 (§1.7)

## 1.2 Xform / Scope

| | Xform | Scope |
|---|---|---|
| 변환(위치·회전·스케일) | **가짐** | 없음 |
| 용도 | 링크·물체의 좌표 원점 | 순수 폴더 |
| 예 | 로봇 링크 | `/Looks`, `/Visuals` |

**실습** — Tutorial 12에서 `Visuals` Scope에 시각 메시를 몰아넣는다. 좌표가 불필요 → Scope. 링크는 좌표 필요 → Xform.

## 1.3 Layer / Sublayer
<sub>원문 링크: USD Layers</sub>

USD 파일 1개 = Layer 1개. 여러 Layer를 겹쳐 합성. 위가 아래를 덮어쓴다.

```
robot_config.usd    Root Layer · 편집 중 (임시 실험)
robot_physics.usd   조인트 · 드라이브 · 콜라이더
robot_base.usd      임포트 직후 원본 · 편집 금지
        ↓ compose
     최종 씬 1개
```

- **비파괴 편집이 목적** — CAD 갱신 → 원본 재임포트 → 위층 물리 설정은 그대로
- 공식: *"source assets must remain unchanged to ensure that they can be re-imported seamlessly without losing downstream modifications."*

**⚠ Authoring Target 함정** — Layer 탭에서 **더블클릭**해야 "여기에 쓴다"가 된다. 모르면 의도한 파일이 아닌 곳에 저장된다.

**실습** — Tutorial 10 §Using Layers / Tutorial 12 §Insert Sublayer
**복귀** — [실습 §6 클로즈드루프](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#6-클로즈드루프closed-loop-구조--그리퍼가-로봇-팔과-근본적으로-다른-이유)

## 1.4 합성 방식 4종 — Sublayer / Reference / Payload / Add-On

공식 에셋 구조 다이어그램의 화살표 색이 이 네 가지다. **구조를 읽으려면 이걸 먼저 알아야 한다.**

| 다이어그램 | 방식 | 동작 | 끌 수 있나 |
|---|---|---|---|
| 초록 실선 | **Sublayer** | 레이어 스택에 통째로 깔림 | ✗ 항상 로드 |
| 주황 | **Reference** | 특정 Prim 아래로 끌어옴 | ✗ 항상 로드 |
| 파랑 | **Payload** | Reference인데 **지연 로딩** | ✓ **끌 수 있음** |
| 초록 점선 | **Add-On** | 작업 중 임시 sublayer | 저장 전 **제거** |

| | Reference | Payload | Sublayer |
|---|---|---|---|
| 로딩 | 항상 | **지연 가능** | 항상 |
| 붙는 위치 | 특정 Prim 아래 | 특정 Prim 아래 | Layer 전체 스택 |
| 용도 | 부품 재사용 · 물리 레이어 | 센서 · 제어 그래프 | 원본 위 편집층 |

**왜 물리는 Reference인데 센서·제어는 Payload인가**
- 물리 없으면 시뮬 자체가 성립 안 함 → 항상 로드 → **Reference**
- 센서·제어는 무겁고 상황에 따라 불필요 → 껐다 켰다 → **Payload**

**Add-On이 헷갈리는 지점** — 센서 레이어를 만들 때 로봇이 화면에 보여야 작업이 된다. 그래서 로봇을 **임시로** sublayer로 깔아두고, **저장 전에 뺀다.** 안 빼면 센서 파일에 로봇이 통째로 박혀서 재사용이 안 된다.

> *"Features that have the simulation asset as a temporary sublayer used during feature creation."*

**⚠ Payload 함정** — payload가 언로드 상태면 프림이 껍데기만 남는다. Property 패널에 Physics 섹션이 사라지고 mass·joint 편집이 안 된다.
복구: 프림 우클릭 → **Refresh Payload** / Property → **Payloads** 섹션 확인.

## 1.5 Variant / VariantSet

같은 Prim이 여러 버전 중 하나를 골라 쓰는 스위치.

```
ur (로봇)
 └ VariantSet "ee_link"
      ├ None
      ├ robotiq_2f_140  ✓
      └ robotiq_2f_85
```

- Robot Assembler가 자동 생성
- 재조립 없이 드롭다운으로 그리퍼 교체 → **물성 비교 실험의 재사용 구조**

**실습** — 로봇 Prim → Property → **Variants**
**복귀** — [실습 §3 Robot Assembler](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#3-robot-assembler로-두-articulation-합치기)

## 1.6 Instanceable
<sub>Scenegraph Instancing</sub>

동일 부품(좌·우 바퀴, 좌·우 손가락)이 메모리 데이터 1개를 공유.

**제약 — 이것 때문에 막힌다**
- Reference된 에셋에만 적용
- **자식 속성 개별 수정 불가** (같은 메모리 공유)
- → Tutorial 8에서 Lula 편집기 쓰기 전 **Instanceable 먼저 해제**. Lula는 인스턴스화된 메시 미지원

> **실사례 (2026-08-09).** 조립한 `ur` 스테이지에서 그리퍼 손가락 콜라이더에 물리재질을 붙이려는데 Property에 Physics 섹션이 안 떴다.
> 원인은 두 겹 — ① `visuals` 쪽을 선택했고(콜라이더는 `collisions`) ② **조립본에서 그리퍼는 instanceable 참조라 자식 편집 자체가 막힌다.**
> 해결: 그리퍼의 **물리 레이어 파일을 직접 열어서** 편집 → 저장하면 그 레이어를 참조하는 조립본에 자동 반영. §3.3 참조.

**실습** — Property → **Instanceable** 체크. 적용되면 레퍼런스 아이콘이 파란 「I」
**복귀** — [실습 §8-2 인스턴싱](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#8-2-scenegraph-instancing--같은-부품-재사용)

## 1.7 Schema — Type(하나) vs API(여러 개)

정체성 = Type 1개. 능력 = API Schema 여러 개를 `.Apply()`로 덧붙임.

```
/World/cube
  Type ── Mesh                    ← 하나만. "무엇인가"
  API ┬── PhysicsRigidBodyAPI     ← 중력 받음
      ├── PhysicsCollisionAPI     ← 충돌함
      └── PhysicsMassAPI          ← 질량 지정
```

- **「정적 에셋을 Sim-Ready로 만든다」가 정확히 이 작업** — CAD Mesh Prim에 물리 API를 쌓는다. Type을 바꾸는 게 아니다. P2 단계의 본질
- Property 패널 `[+ Add]` 버튼이 전부 API Apply
- RigidBody만 있고 Collision 없으면 → 바닥 통과

## 1.8 Default Prim

- 이 USD를 Reference할 때 기본으로 가져올 최상위 Prim
- 미지정 → Reference 실패 또는 엉뚱한 것이 딸려옴
- 실습: 우클릭 → **Set as Default Prim**

---

# 2. PhysX 물리

## 2.3 Articulation

조인트로 연결된 링크 묶음을 한 시스템으로 한 번에 푸는 구조(reduced coordinate).

| | 개별 강체 + 조인트 (maximal) | Articulation (reduced) |
|---|---|---|
| 변수 | 각 링크가 6 DOF | 관절 각도만 |
| 조인트 | 구속으로 억제 | 구조에 내장 |
| 결과 | 오차 누적 · 관절 늘어남 | **정확 · 안정. 로봇 필수** |

**⚠ Articulation Root = 로봇당 정확히 1개.** 그리퍼 부착 시 그리퍼 쪽 root 제거 → root 2개면 관절 소유가 모호해져 시뮬 깨짐.

**실습** — `root_joint` → Property → **Physics/Articulation**
**복귀** — [실습 §3](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#3-robot-assembler로-두-articulation-합치기)

## 2.4 Closed Loop
<sub>closed loop articulation chain</sub>

articulation 솔버는 트리(경로 1개)만 푼다. 경로가 둘 이상 = 닫힌 루프 → 경고.

```
열린 체인 (팔) — OK          닫힌 루프 (평행 그리퍼) — 경고

  base                          base_link
   │                        ┌───────┴───────┐
  shoulder             outer_knuckle   inner_knuckle
   │                        │               │
  elbow                outer_finger ── inner_finger
   │                          ↑ 다시 만난다
  wrist                base_link → finger 경로가 2개
```

- 평행 그리퍼는 손가락이 **4절 링크(four-bar linkage)** 로 지지됨
- 이 기구학이 평행 운동을 만드는 원리 → **회피 불가**

## 2.5 Exclude From Articulation

루프 관절 1개를 솔버 계산에서 제외. 관절은 물리적으로 남되 낮은 우선순위의 maximal-coordinate 조인트로 처리.

**선정 기준**

| 기준 | 이유 |
|---|---|
| 기능 영향 적음 | 빠져도 동작이 안 바뀜 |
| limit 없음 | limit은 솔버가 지켜야 하는데 빠지면 불가 |
| 드라이브 불필요 | 힘을 만드는 관절은 정확히 풀려야 함 |
| 순수 공간 구속 | 「여기 붙어 있어라」만 하는 관절 |

- Robotiq → `left/right_inner_knuckle_joint`
- 실습: 조인트 Prim → Property → **Physics** → **Exclude From Articulation** 체크

**복귀** — [실습 §6-2](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#6-2-해결--루프에서-관절-하나를-제외한다)

## 2.6 Joint 타입

| 타입 | DOF | 용도 |
|---|---|---|
| Fixed | 0 | 로봇↔월드, 그리퍼↔손목 |
| Revolute | 1 (회전) | 로봇 팔 대부분 |
| Prismatic | 1 (직선) | 리니어 축, 테스트 리그 |
| Spherical | 3 | 볼조인트 |
| D6 | ~6 | 축별 개별 지정. 만능이나 무거움 |

## 2.7 Collider Approximation
<sub>collision shapes</sub>

| 방식 | 비용 | 특징 | 대상 |
|---|---|---|---|
| Bounding Sphere / Cube | 최저 | 형상 무시 | 정밀도 무의미한 링크 |
| **Convex Hull** (기본) | 낮음 | 오목부가 메워짐 | 팔 링크 대부분 |
| **Convex Decomposition** | 중~높음 | 볼록 조각으로 윤곽 근사 | 그리퍼 손가락 |
| SDF | 높음 | 부호거리장 · 오목 정밀 | 정밀 파지 |
| Triangle Mesh | 최고 | 원본 그대로 | 정적 물체만 |

**Hull이 그리퍼에서 문제인 이유** — 손가락 안쪽 파지면은 오목. Hull이 그 파인 부분을 채움 → 물체가 실제 접촉면보다 일찍 닿은 것으로 계산 → 미끄러짐·관통.

> **⚠ 정정 기록.** 기존 문서의 「Convex Hull이 그리퍼 **사이**를 메운다」 = **틀림.**
> Hull은 **링크별** 적용 → 좌·우 손가락 사이가 아니라 **각 손가락 자체의 오목부**가 메워진다.
> collider 시각화로 확인해 잡은 오류. **문서와 화면이 다르면 화면이 맞다.**

- 실습: Prim → Property → **Physics** → **Collider Approximation**
- 시각화: 뷰포트 눈 아이콘 → `Show By Type > Physics > Colliders > All`

**복귀** — [실습 §6-5](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#6-5-충돌-형상과-self-collision)

## 2.8 Joint Drive
<sub>joint drives</sub>

관절의 액추에이터 모델. URDF에 없으므로 임포트 시 사용자가 정한다.

```
τ = Stiffness × (q_target − q) + Damping × (q̇_target − q̇)
        └─ P 게인 ─┘                └─ D 게인 ─┘
```

| 파라미터 | 의미 |
|---|---|
| Stiffness | 목표 위치로 당기는 힘 (P) |
| Damping | 속도 저항. 진동을 죽임 (D) |
| Max Force | 낼 수 있는 최대 힘/토크 |
| Target Position / Velocity | 지령값 |

**핵심 구분** — Stiffness/Damping은 **로봇의 물리적 성질이 아니라 제어기 설정**. 그래서 URDF에 없다. URDF의 `<dynamics damping>`은 **관절 마찰·점성**이지 제어기 게인이 아니다.

**드라이브 모드**

| 모드 | 조건 | 대상 |
|---|---|---|
| Position | Stiffness > 0 | 관절 대부분 |
| Velocity | Stiffness = 0, Damping > 0 | 바퀴 |
| **None** | 둘 다 0 | 토크 제어 → **게인이 안 먹음** |
| Mimic | 다른 관절 종속 | 그리퍼 팔로워 |

> **⚠ 함정** — Drive Type이 토크 제어면 *"Stiffness and damping have no effect and will be imported as zero"*. 게인을 아무리 넣어도 안 먹는데 원인을 못 찾는 상황이 여기서 나온다.

**힘 기반 파지** — 그리퍼는 일부러 Stiffness = 0. Damping·Max Force만으로 "이만큼의 힘으로 계속 밀어라" → 물체 크기가 달라도 저항 만날 때까지 닫힘.

**복귀** — [실습 §6-4](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#6-4-힘-기반force-driven-파지--위치제어를-안-쓰는-이유)

## 2.9 Mimic Joint

한 관절 각도를 다른 관절에 종속.

```
finger_joint (master, Drive 있음)
      │  q_follower = q_master × Gearing
      ▼
outer_knuckle_joint (follower, Drive 없음)
```

| 파라미터 | 값 예 | 의미 |
|---|---|---|
| Reference Joint | `finger_joint` | 마스터 관절 |
| Gearing | `-1.0` | 마스터 각도에 곱할 비율. 음수 = 반대 방향 |
| Rotation Axis | `rotX` | 1 DOF 관절에선 **무의미**. Spherical 등 다축에서만 |

**⚠ 주의 2가지**
1. mimic 관절 자체에 Drive 걸지 않음 → reference에서 자동 복사. 걸면 두 제어가 충돌
2. 기존 Drive가 있으면 **값을 0으로 지운 뒤** mimic 추가

- 실습: Property → **Add > Physics > Mimic Joint**

**복귀** — [실습 §6-3](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#6-3-mimic-joint--손가락-두-개를-하나의-입력으로)

## 2.10 Physics Material

마찰·반발 계수. **시각 재질(Looks)과 별개.**

| 속성 | 의미 |
|---|---|
| Static / Dynamic Friction | 정지 / 운동 마찰 |
| Restitution | 반발 계수 |
| **Combine Mode** | 두 물체 값 결합 방식: `Average` / `Min` / `Max` / `Multiply` |

**Combine Mode가 중요한 이유** — 손가락 0.8 + 물체 0.1 → `Average`면 0.45로 떨어짐. 파지에선 **`Max`** 로 두어 손가락 재질이 지배하게 한다.

참고값 — 고무 근사 `0.8` / 그리퍼 파지 `1.0`

- 실습: `Create > Physics > Physics Material > Rigid Body Material` → 콜라이더에 드래그
- Xform이 instanceable이면 먼저 해제 필요할 수 있음

## 2.11 Natural Frequency / Damping Ratio

Stiffness/Damping 대신 ωₙ·ζ로 지정. 관절의 등가 관성 `m`으로 내부 변환.

```
ωₙ = √(K_p / m)          K_p = m · ωₙ²
ζ  = K_d / (2·m·ωₙ)      K_d = 2·ζ·m·ωₙ
```

| ζ | 거동 |
|---|---|
| **1.0** | 임계감쇠. 진동 없이 최속 수렴. **보통 목표값** |
| < 1.0 | 부족감쇠. 오버슈트·진동 |
| > 1.0 | 과감쇠. 진동 없지만 느림 |

**왜 이 표현을 쓰나** — `K_p = m·ωₙ²`. 같은 ωₙ이라도 **관절마다 등가 관성 m이 달라 Stiffness가 다르게 나온다.** 어깨는 팔 전체를 들어 m이 크고 손목은 작다. 「모든 관절 Stiffness 1000」은 물리적으로 말이 안 되지만 「모든 관절 ωₙ=25」는 말이 된다.

**저장은 항상 Stiffness로.** ωₙ/ζ는 입력 편의용 표현.

**미해결 질문**

| 출처 | ωₙ |
|---|---|
| URDF Importer 기본값 | 25 |
| NVIDIA 매니퓰레이터 튜토리얼 (UR10e) | **300** |

`K_p = m·ωₙ²` 이므로 **144배** 차이. **왜 ζ를 올리지 않고 ωₙ만 올릴까?** 직접 답을 만들면 「기본값을 그대로 쓰셨나요?」에 대한 답이 된다.

**복귀** — [실습 §7](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#7-gain-tuner-절차--표준-튜닝-알고리즘-tutorial-11)

## 2.12 솔버 설정

| 항목 | 의미 | 조정 |
|---|---|---|
| Solver Position Iterations | 위치 구속 반복 | 기본 4~8 → 그리퍼 접촉이면 **64** |
| Solver Velocity Iterations | 속도 구속 반복 | 보통 **4** |
| Sleep Threshold | 이 속도 이하면 계산 제외 | 미세 움직임 보려면 낮춤 (0.00005) |
| Stabilization Threshold | 안정화 보정 임계 | 낮추면 미세 거동 보존 (0.00001) |
| Self-Collision Enabled | 같은 articulation 내 충돌 | 보통 끔. 손가락 겹침 방지엔 켬 |

**복귀** — [실습 §4-1](GUI_실습_매니퓰레이터_그리퍼_어셈블_클로즈드루프_최적화.md#4-1-articulation-솔버-정밀도)

## 2.13 Physics Timestep

이 프로젝트에서 가장 중요한 발견의 축.

- 기본 60Hz. P1은 **120Hz**(8.33ms)로 측정
- Tutorial 10 — 2.5kg 파지 미끄러짐 → **80Hz로 해결**(접촉 계산 빈도 부족)
- P1 측정 — 궤적 추종오차 **τ ≈ 26ms ≈ 3 물리 스텝**. **게인으로는 원리적으로 못 줄이는 지연**

**미실행 실험** — `PHYSICS_DT` 1/120 → 1/240 시 τ가 13ms(고정 스텝 수)인가 26ms(고정 실시간)인가. [RESUME.md](../RESUME.md) 우선순위 2

---

# 3. 로봇 스키마 · 에셋 구조

## 3.1 Robot Schema / IsaacRobotAPI

「이 Prim 묶음이 하나의 로봇이다」를 시뮬레이션 에셋 구조와 무관하게 기술하는 메타데이터 계층.

| 속성 | 내용 |
|---|---|
| `isaac:physics:robotLinks` | 이 로봇의 링크 Prim 목록 |
| `isaac:physics:robotJoints` | 이 로봇의 조인트 Prim 목록 |
| `isaac:robotType` | Default / End Effector / Manipulator / Humanoid / Wheeled |

**⚠ Gain Tuner 드롭다운이 비어 있으면 여기를 의심한다.** 도구가 「튜닝 가능한 로봇」을 자동으로 띄우는 근거가 이 스키마. 없으면 목록에 안 뜬다.

- 수동 조립 시 `/ur/ee_link`를 두 목록에 **직접 추가**
- Robot Assembler 사용 시 자동 처리

## 3.2 권장 에셋 구조
<sub>공식: [Asset Structure](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup/asset_structure.html)</sub>

핵심 발상은 하나 — **원본은 절대 안 건드리고 위에 얹는 레이어로만 작업한다.** 사진 보정의 조정 레이어와 같은 구조다.

> *"The source assets must remain unchanged to ensure that they can be re-imported seamlessly without losing downstream modifications."*

**왜 이렇게까지 하나** — CAD가 갱신되면 `asset_base.usd`만 갈아끼운다. 그동안 잡아둔 게인·마찰·조인트 설정이 안 날아간다.

### 3층 구조

```
① Asset Source (불변)
   asset_base.usd     임포트 직후 구조 그대로
   parts.usd          부품별 메시 (메시 1개당 USD 1개)
   materials.usd      PBR 재질 모음
        │ Sublayer
② Transformation (건너뛸 수 있음)
   asset_sim_base.usd       시뮬용 재구성 (Visual / Collider 분리)
   asset_sim_optimized.usd  메시 병합 · instanceable 참조
        │ Sublayer
③ Features (선택 부착)
   asset_physics.usd   Articulation · RigidBody · Collider · Joint   ← Reference
   asset_sensors.usd   센서                                          ← Payload
   asset_control.usd   OmniGraph 제어 그래프                          ← Payload
   asset_ros.usd       ROS Omnigraph                                 ← Payload
        │
   asset.usd  최종 합성물
```

②는 조건부로 생략 가능하다.
> *"If the asset source is already in a format suitable for simulation, this step or parts of it can be skipped."*

### 물리 레이어만 특별하다

> *"The physics asset adds the original asset as a sub-layer and **completely replaces the final composition base reference**."*

그래서 **그리퍼 물리를 고치려면 `_physics.usd`를 직접 열어야 한다.** 조립본에서는 안 된다(§1.6 실사례).

Gain Tuner의 **Save Gains to Physics Layer**가 찾는 것도 이 파일이다. 구조를 안 따르면 저장 위치를 못 찾는다.

### ⚠ 공식 문서와 실제 배포 에셋이 다르다

문서 권장:
```
asset_name/
├── asset.usd
├── source/      asset_base.usd · parts.usd · materials.usd
└── features/    asset_physics.usd · asset_sensors.usd · ...
```

실제 NVIDIA 배포본 (로컬 실측):
```
ur10e/
├── ur10e.usd
└── configuration/            ← source/ + features/ 를 한 폴더에
    ├── ur10e_base.usd
    ├── ur10e_physics.usd
    ├── ur10e_robot.usd       ← Robot Schema. 문서 폴더표엔 없음
    ├── ur10e_sensor.usd
    └── ur10e_Gripper_2F_140.usd   ← 조립 Variant
```

**실물을 기준으로 삼는다.** 문서와 화면이 다르면 화면이 맞다.

## 3.3 실험 프로젝트 폴더 구조 <sub>공식 문서에 없음 — 이 프로젝트 설계</sub>

§3.2는 **"에셋을 만들어 배포할 때"** 의 구조다. **씬을 구성하고 실험하는 워크스페이스**는 별개 문제이고 공식 문서에 없다.

| 하는 일 | 필요한 구조 |
|---|---|
| 그리퍼 물리 튜닝 → 재사용 | §3.2 asset_structure |
| 씬 구성 · 실험 · 결과 기록 | 아래 프로젝트 레이아웃 |

```
D:\ic\assets\                      git 제외. 재다운로드 가능
├── vendor\                        NVIDIA 배포본. 절대 수정 금지
│   └── Manipulator\
│       ├── import_manipulator\
│       └── configure_manipulator\
└── tuned\                         내가 튜닝한 에셋 (§3.2 준수)
    └── ur10e_2f140\
        ├── ur10e_2f140.usd
        └── configuration\
            ├── ur10e_2f140_physics.usd   ★ 내 게인·마찰
            └── ur10e_2f140_robot.usd

Isaac-simready-validation\         git (GitHub)
├── scenes\                        실험 씬 (수십 KB, 커밋)
├── scripts\                       fetch_tutorial_assets.ps1 등
├── results\                       CSV
└── docs\
```

**설계 근거**

| 원칙 | 이유 |
|---|---|
| `vendor/` ↔ `tuned/` 분리 | Source Immutability를 폴더 레벨로. vendor를 손대면 재다운로드 시 튜닝이 날아감 |
| 씬은 git, 에셋은 git 제외 | 씬 USD는 참조만 담아 수십 KB. 에셋은 MB 단위이고 스크립트로 재생성 가능 |
| `D:\ic` 절대경로 고정 | conda 환경을 `D:\ic\env`에 고정한 것과 같은 이유 |

**재다운로드** — `scripts\fetch_tutorial_assets.ps1` (기본은 기존 파일 보존, `-Force`로 덮어쓰기)

> **현재 예외** — 튜토리얼 진행 중인 작업(직접 임포트한 그리퍼, 조립한 `ur.usd`)이 `vendor/` 안에 있다. 상대참조 때문에 지금 옮기면 깨진다. **튜닝 값이 확정되면 `tuned/`로 이관한다.**

---

# 4. Kit · 포맷 · 외부 도구

| 용어 | 내용 |
|---|---|
| **Extension** | Kit의 기능 단위 플러그인. `Window > Extensions`. **AUTOLOAD 체크**해야 다음 실행에도 켜짐. 안 보이면 `@feature` 필터 제거 |
| **Stage** | 씬의 Prim 트리 |
| **Property** | 선택한 Prim의 속성. 물리 설정 대부분 |
| **Layer** | Layer 스택(§1.3). 편집 대상 전환 |
| **Content** | Nucleus/로컬 에셋 브라우저. `Window > Browsers > Content` → `Isaac/Robots` |
| **OmniGraph / Action Graph** | 노드 연결형 비주얼 프로그래밍. Tutorial 10에서 **클릭 한 번 그리퍼 개폐** 컨트롤러를 이걸로. `Window > Graph Editors > Action Graph` |
| **URDF** | ROS 로봇 기술 XML. 링크·조인트·관성·충돌 있음, **드라이브 게인 없음** |
| **xacro** | URDF 매크로 전처리. `xacro a.xacro > a.urdf`. **ROS 도구 — 이 프로젝트에선 안 씀** |
| **USD** | Isaac Sim 네이티브 포맷 |
| **Onshape Importer** | 클라우드 CAD 직접 임포트. Tutorial 10 Robotiq 출처. **알려진 이슈: 조인트 180° 뒤집힘** |
| **Lula / RMPFlow / cuMotion** | 모션 플래닝 솔버. `.yaml`/`.xrdf` + 충돌 구체 요구 |

---

## 사용 규칙

1. 초록 링크는 원문 대신 [빠른 조회](#빠른-조회)부터
2. 「실습」 줄을 읽고 **즉시 복귀**
3. 없는 용어는 **그 자리에서 추가** — 완성본이 아니라 누적본
4. **문서와 화면이 다르면 화면이 맞다.** 다르면 정정 기록을 남긴다 (§2.7 사례)
