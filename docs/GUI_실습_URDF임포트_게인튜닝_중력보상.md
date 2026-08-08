# GUI 실습 — URDF 임포트 → 조인트 게인 튜닝 → 중력보상

> **용도** — 실무 면접에서 "지금 Isaac Sim 켜서 로봇 하나 불러오고 제어 붙여보세요" 를 요구받을 때
> 손이 기억하도록 만드는 문서. 클릭 순서만 외우면 "왜 그렇게 했냐"에서 무너지므로
> **각 단계마다 근거를 같이 적었다.**

---

## 0. 먼저 이해할 것 — Isaac Sim의 관절 제어는 PD 제어기다

Isaac Sim(PhysX)의 위치 제어는 이 식 하나로 돌아간다.

```
Force = (Stiffness × Δposition) + (Damping × Δvelocity)
```

- **Stiffness** — 목표 위치로 당기는 힘. P 게인.
- **Damping** — 속도에 저항하는 힘. D 게인. 진동을 죽인다.

즉 **stiffness/damping은 로봇의 물리적 성질이 아니라 "제어기 설정"이다.**
그래서 URDF에 없다. URDF에 있는 `<dynamics damping="...">` 은 **관절의 마찰·점성**이지
제어기 게인이 아니다. 이 구분을 말할 수 있어야 한다.

### Natural Frequency / Damping Ratio 모드

Gain Tuner는 stiffness를 직접 넣는 대신 **ωₙ(고유진동수)과 ζ(감쇠비)** 로 지정하는 모드를 제공한다.
내부적으로 관절의 **등가 관성 m** 을 써서 stiffness/damping을 역산한다.

- **ζ = 1.0** — 임계감쇠(critically damped). 진동 없이 가장 빠르게 수렴. **보통 목표값.**
- **ζ < 1.0** — 부족감쇠(underdamped). 오버슈트·진동 발생.
- **ζ > 1.0** — 과감쇠(overdamped). 진동은 없지만 느리다.

> 저장될 때는 **항상 Stiffness 값으로 변환되어 저장된다** ("Saved values will always be in Stiffness").
> ωₙ/ζ는 입력 편의를 위한 표현일 뿐이다.

**면접용 한 줄** — "게인을 숫자로 찍는 게 아니라 ζ=1 임계감쇠를 목표로 잡고,
관절 등가관성 기준으로 ωₙ을 올려가며 오버슈트 없이 추종오차가 줄어드는 지점을 찾습니다."

---

## 1. GUI 실행

```bash
conda activate D:\ic\env
set OMNI_KIT_ACCEPT_EULA=YES
isaacsim
```

> 첫 실행은 셰이더 컴파일로 수 분 걸린다. 멈춘 게 아니다.
> 두 번째부터는 캐시가 있어 빠르다 (이번 환경 실측: **약 10초 기동**).

---

## 2. URDF 임포트 (GUI)

### 2-1. 익스텐션 확인
`Window > Extensions` 에서 **`isaacsim.asset.importer.urdf`** 가 켜져 있는지 확인.
보통 기본 활성화돼 있다.

### 2-2. 임포트
`File > Import` → URDF 파일 선택.

연습용으로 익스텐션에 **UR10이 동봉**돼 있다. 별도 다운로드가 필요 없다.

```
<익스텐션 경로>/data/urdf/robots/ur10/urdf/ur10.urdf
```

익스텐션 경로는 파이썬으로 확인할 수 있다.
```python
from isaacsim.core.utils.extensions import get_extension_path_from_name
print(get_extension_path_from_name("isaacsim.asset.importer.urdf"))
```

### 2-3. 임포트 옵션 — 각각 무슨 뜻인지

| 옵션 | 의미 | 면접에서 물으면 |
|---|---|---|
| **Fix Base Link** | 베이스를 월드에 고정 | 매니퓰레이터는 켠다. 모바일 로봇·휴머노이드는 끈다 |
| **Joint Drive Type** | Position / Velocity / None | 위치제어면 Position. **None(토크제어)이면 stiffness/damping이 0으로 들어간다** |
| **Joint Drive Strength** | 드라이브 세기 | 임포트 시 damping 파라미터로 반영된다 |
| **Natural Frequency / Damping Ratio** | ωₙ, ζ 로 게인 지정 | §0 참조 |
| **Self Collision** | 자기 링크 간 충돌 | 보통 끈다. 켜면 무겁고 URDF 정밀도에 따라 오탐 |
| **Convex Decomposition** | 오목 메시를 볼록 조각으로 분해 | 정확한 충돌이 필요하면 켠다. 무겁다 |
| **Density** | 관성 미지정 링크의 밀도 | URDF에 `<inertial>` 이 있으면 0으로 두고 URDF 값을 쓴다 |
| **Distance Scale** | 단위 스케일 | URDF는 m 단위. 스테이지도 m면 1 |

> **실측 관찰** — UR10 임포트 시 이런 경고가 뜬다.
> `link ee_link has no body properties (mass, inertia, or collisions) and is being merged into wrist_3_link`
> URDF의 `ee_link` 는 좌표 기준용 더미 링크라 질량이 없다 → 임포터가 앞 링크로 병합한다.
> **정상이다.** 그래서 payload를 실을 실제 말단 링크는 `wrist_3_link` 다.

### 2-4. Colliders 탭 — 충돌 형상을 어떻게 만들 것인가

| 옵션 | 원문 설명 | 판단 기준 |
|---|---|---|
| **Collision From Visuals** | *"collision geometry is generated from the visual meshes in the URDF file"* | URDF에 `<collision>` 이 없을 때 켠다. 있으면 그걸 쓰는 게 정확하다 |
| **Convex Hull** | *"Creates a convex hull around the visual mesh"* | 기본값. 빠르지만 오목한 부분이 메워진다 |
| **Convex Decomposition** | *"Decomposes the visual mesh into multiple convex pieces"* | 그리퍼 손가락처럼 오목 형상이 중요할 때. 무겁다 |
| **Bounding Sphere / Cube** | *"Uses a simple bounding sphere/box approximation"* | 가장 가볍다. 충돌 정밀도가 필요 없는 링크에 |
| **Allow Self-Collision** | *"allows the robot model to collide with itself"* | 보통 끈다. URDF 충돌 형상이 거칠면 오탐이 대량 발생 |

> **면접 포인트** — "왜 Convex Hull이 기본인가"를 물으면:
> PhysX의 충돌 검사는 볼록 형상에서 훨씬 빠르다. 오목 메시는 그대로 못 쓰고
> 분해하거나 근사해야 한다. **정밀도와 연산량의 트레이드오프**를 링크마다 다르게 줄 수 있다.

### 2-5. 구조 관련 옵션

| 옵션 | 의미 |
|---|---|
| **Base Type: Fixed** | *"adds a world-to-root fixed joint"* — 베이스를 월드에 고정 |
| **Base Type: Mobile** | *"removes any existing world-to-root fixed joint"* — 떠 있는 베이스 (모바일·휴머노이드) |
| **Robot Type** | `isaac:robotType` 속성을 설정 — Default / End Effector / Manipulator / Humanoid / Wheeled |

`Robot Type` 은 다른 익스텐션(모션 생성·파지 등)이 이 에셋을 어떻게 다룰지 판단하는 메타데이터다.
Manipulator로 지정해두면 Gain Tuner 같은 도구가 자동으로 인식한다.

> 위 표의 인용문은 **6.0.1 문서** 기준이다. 5.1에서도 항목 구성은 사실상 동일하지만,
> 문서 화면과 실제 UI가 미세하게 다를 수 있다. **실제 창에 뜨는 라벨을 기준으로 삼을 것.**

---

## 3. 조인트 드라이브 속성 확인·수정 (Property 패널)

1. Stage 트리에서 관절 프림 선택 (예: `.../shoulder_lift_joint`)
2. 우측 **Property** 패널 → **Drive** 섹션
3. `Stiffness`, `Damping`, `Max Force`, `Target Position` 확인·수정

관련 항목:
- `Joint > Advanced > Maximum Joint Velocity` — 최대 관절 속도 제한

> **주의** — Drive Type이 **토크 제어**면 *"Stiffness and damping have no effect and will be imported as zero"*.
> 게인을 아무리 넣어도 안 먹는데 원인을 못 찾는 상황이 여기서 나온다.

---

## 4. Gain Tuner 확장 — 이게 핵심 도구다

`Tools > Robotics > Asset Editors > Gain Tuner`

- **Select Robot** 드롭다운에 튜닝 가능한 로봇이 자동으로 뜬다
- **Stiffness 직접 입력** 모드와 **Natural Frequency** 모드 중 선택
- **Run Test** 를 누르면 관절별 테스트를 돌리고, **결과가 플롯으로 시각화**된다
- 관절을 선택하면 해당 관절의 응답 곡선이 보인다

**튜닝 절차 (권장 순서)**
1. ζ = 1.0 (임계감쇠)으로 고정
2. ωₙ 을 낮은 값부터 올려가며 Run Test
3. 오버슈트가 생기기 직전까지 올린다
4. 추종오차 플롯이 평탄해지는 지점에서 정지

### ⚠️ 알려진 버그 (면접에서 안 되면 당황하지 말 것)
- [Issue #104](https://github.com/isaac-sim/IsaacSim/issues/104) — Gain Tuner로 Stiffness/Damping 튜닝 시 문제
- [Issue #186](https://github.com/isaac-sim/IsaacSim/issues/186) — **Run Test 버튼이 선택 안 되는** 버그

> GUI가 안 먹으면 **Property 패널에서 직접 값 수정** 또는 **파이썬 스크립트**로 우회한다.
> "GUI 버그가 있어서 스크립트로 우회했습니다"는 감점이 아니라 가점이다.

---

## 5. 중력보상 (Gravity Compensation)

실제 산업용·협동로봇 컨트롤러는 **중력 토크를 미리 계산해 피드포워드로 상쇄**한다.
그래서 팔을 수평으로 뻗어도 처지지 않는다. 시뮬에서 이걸 흉내내는 방법이 두 가지다.

### 방법 A — Disable Gravity (GUI, 가장 빠름)

공식 문서 원문:
> *"To emulate a control that includes gravity compensation, **select all rigid bodies of the robot
> and check Disable Gravity** in the properties panel."*

1. Stage 트리에서 로봇의 **모든 링크(rigid body)** 를 다중 선택
2. Property 패널 → **Disable Gravity** 체크

**장점** — 즉시 됨. 로봇 **자체 무게**에 대한 완벽한 중력보상과 등가.

**한계 — 여기가 핵심이다.**
로봇 링크에만 Disable Gravity를 걸면 잡은 물체(별도 강체, 중력 ON)의 무게는 **그대로 느낀다.**
즉 "자기 무게는 보상하고 외부 부하는 느낀다"는 실제 중력보상과 구조가 같다.

문제는 그게 **너무 완벽하다**는 것이다.
- 실제 컨트롤러의 중력보상은 **모델 오차**를 갖는다. 질량·무게중심 추정이 조금씩 틀리다.
- Disable Gravity는 오차가 0인 이상적 보상이라 **불완전한 보상을 모델링할 수 없다.**
- Sim-to-Real 갭을 측정하려면 바로 그 "불완전함"을 재현해야 하는데, 이 방법으로는 못 한다.
- on/off 이진값이라 "80%만 보상되는 상태" 같은 걸 표현할 수 없다.

> **면접에서 이렇게 말하면 된다** — "빠른 확인에는 Disable Gravity를 쓰지만,
> Sim-to-Real 갭을 정량화할 때는 못 씁니다. 보상 오차가 0인 이상적 상태만 만들 수 있어서,
> 실기와의 차이를 만드는 원인 자체가 사라지거든요."

### 방법 B — 피드포워드 토크 (스크립트, 물리적으로 정확)

중력 토크를 계산해 effort로 더해준다.

```python
tau_g = art.get_generalized_gravity_forces()   # 중력 보상 토크
art.set_joint_efforts(tau_g)                   # 피드포워드로 상쇄
```

**장점** — 중력은 살아있고 로봇만 보상한다. 실제 컨트롤러와 같은 구조.
파지한 물체의 무게는 그대로 작용한다.
**면접 어필** — "Disable Gravity는 물체 무게까지 사라져서, 저는 피드포워드 방식을 씁니다."

> 매대정리 프로젝트에서 **joint_2 추종오차 4.55° → 0.17° (96% 감소)** 를 만든 게 이 방법이다.

---

## 6. 검증 — 숫자로 확인하는 법

게인을 바꿨으면 **효과를 숫자로** 보여야 한다. 두 가지를 잰다.

| 테스트 | 방법 | 의미 |
|---|---|---|
| **중력 처짐 (static)** | 팔을 수평으로 뻗고 유지 → 지령 대비 정상상태 관절 오차 | 중력 토크가 최대인 자세. 게인 부족·payload 미반영이 여기서 드러난다 |
| **궤적 추종 (dynamic)** | 사인 궤적 지령 → 지령 대비 실제 관절각 RMS 오차 | 동적 지연. 정적으로 멀쩡해도 여기서 터진다 |

이 저장소의 [scripts/p1_drive_tuning.py](../scripts/p1_drive_tuning.py) 가 이 둘을 자동 측정한다.
GUI로 감을 잡고, 스크립트로 정량화하는 흐름을 보여주면 된다.

---

## 7. 면접 직전 리허설 체크리스트

30분 안에 한 번은 손으로 돌려볼 것.

- [ ] `isaacsim` 으로 GUI 기동
- [ ] `File > Import` 로 UR10 URDF 임포트 (옵션 의미 설명하며)
- [ ] `ee_link merged` 경고를 보고 **왜 나는지 설명**
- [ ] Stage에서 관절 선택 → Property > Drive 에서 Stiffness/Damping 확인
- [ ] Stiffness를 10배 올려보고 거동 변화 관찰
- [ ] `Tools > Robotics > Asset Editors > Gain Tuner` 열기 → Run Test → 플롯 확인
- [ ] 모든 링크 선택 → Disable Gravity 체크 → 처짐이 사라지는지 확인
- [ ] **Disable Gravity의 한계**(물체 무게도 사라짐) 설명
- [ ] Play 눌러 시뮬 돌려보고, 팔이 진동하면 damping을 올려 잡기

### 자주 나올 질문과 답
| 질문 | 답의 뼈대 |
|---|---|
| "URDF에 게인이 있나요?" | 없다. `<dynamics damping>` 은 관절 마찰이고 제어기 게인이 아니다. 임포터가 사용자에게 받는다 |
| "Stiffness를 무조건 높이면?" | 수치 불안정·진동. damping과 짝으로 올려야 하고 ζ=1 근처를 목표로 한다 |
| "중력보상을 어떻게 하나요?" | Disable Gravity(빠름, 물체 무게도 사라짐) vs 피드포워드 토크(정확). 용도에 따라 선택 |
| "게인이 잘 잡혔는지 어떻게 아나요?" | 정적 처짐과 동적 추종오차 두 축으로 측정. 오버슈트 없이 오차 최소인 지점 |

---

## 참고

- [Tutorial 11: Tuning Joint Drive Gains (5.1)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/joint_tuning.html)
- [Tutorial: Import URDF (5.1)](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html)
- [URDF Importer Extension (5.1)](https://docs.robotsfan.com/isaacsim/5.1.0/importer_exporter/ext_isaacsim_asset_importer_urdf.html)
- [Gain Tuner 버그 #104](https://github.com/isaac-sim/IsaacSim/issues/104) · [#186](https://github.com/isaac-sim/IsaacSim/issues/186)
