# GUI 실습 — 매니퓰레이터+그리퍼 임포트 → 어셈블 → 클로즈드루프 → 게인튜닝 → 최적화

> 🌐 **통합 웹 매뉴얼** — https://claude.ai/code/artifact/52ad7d3c-f237-4329-809f-c058a6123a5b
> 이 문서 + 레퍼런스 2종이 한 페이지. 용어에 마우스를 올리면 정의 팝오버가 뜬다.
>
> **모르는 용어** → [레퍼런스_IsaacSim_용어사전.md](레퍼런스_IsaacSim_용어사전.md)
> **도구 조작법** → [레퍼런스_IsaacSim_도구.md](레퍼런스_IsaacSim_도구.md)
> **이전 단계(로봇 1대 기준)** → [GUI_실습_URDF임포트_게인튜닝_중력보상.md](GUI_실습_URDF임포트_게인튜닝_중력보상.md)

**범위** — 공식 Robot Setup Tutorials **6~9**(조립) + **10~12**(클로즈드루프·게인튜닝·최적화).

**ROS 2 경로 제외 이유** — 튜토리얼 6번은 URDF 조달을 ROS 2 라이브 토픽 + xacro로 설명한다. Linux 전용이고 조립·튜닝과 무관하다. **이미 있는 URDF/USD를 Isaac Sim 안에서 조립·튜닝하는 부분**만 다룬다. OS 무관이고 실무에서 더 자주 쓴다.

---

## 0. 실행

새 PowerShell 창마다 세 줄 먼저.

```powershell
$env:TEMP='D:\ic\tmp'; $env:TMP='D:\ic\tmp'
$env:OMNI_KIT_ACCEPT_EULA='YES'
D:\ic\env\Scripts\isaacsim.exe
```

- 첫 실행 = 셰이더 컴파일로 수 분. 멈춘 게 아님
- 스크립트는 `-u` 필수 → 없으면 출력 버퍼링
- **GUI와 스크립트 동시 실행 금지** → VRAM 12GB 부담
- PC방 = 매 세션 재설치. 결과물은 GitHub 푸시해야 남음

## 1. 문서 범위

| 튜토리얼 | 제목 | 이 문서 | 다루는 정도 |
|---|---|---|---|
| 6 | Setup a Manipulator | §2~3 | ROS 2 제외, 조립부 전체 |
| 7 | Configure a Manipulator | §4 | 전체 |
| 8 | Generate Robot Configuration File | §5 | 요약 |
| 9 | Pick and Place Example | §5 | 요약 |
| 10 | Rig Closed-Loop Structures | §6 | 전체 — **핵심** |
| 11 | Tuning Joint Drive Gains | §7 | 절차 상세 |
| 12 | Asset Optimization | §8 | 전체 |

---

# Part A — 임포트 및 어셈블 (Tutorial 6~9)

## 2. 임포트 경로 두 갈래

매니퓰레이터 URDF를 받으면 둘 중 하나. 이 환경엔 두 경로 모두 시험할 자산이 있다.

```
경로 A                          경로 B
로봇+그리퍼가 한 URDF에           로봇 URDF, 그리퍼 URDF가 별도
      │                                │
File > Import 1회                각각 임포트 → articulation 2개 발생
      │                                │
관절 트리가 이미 이어짐            Robot Assembler로 병합 → articulation 1개
```

### 2-1. 경로 A — 이 환경에서 즉시 확인

`franka_description`, `cobotta_pro_900`은 팔과 그리퍼가 **한 URDF에 관절 트리로 이미 연결**돼 있다.

```
D:\ic\env\Lib\site-packages\isaacsim\exts\isaacsim.asset.importer.urdf\data\urdf\robots\
  ├ franka_description\robots\panda_arm_hand.urdf   팔 + 그리퍼 통합
  └ cobotta_pro_900\...                              팔 + 그리퍼 통합
```

- `File > Import` → 위 URDF 선택. 옵션 의미는 [도구 §6 URDF Importer](레퍼런스_IsaacSim_도구.md#6-urdf-importer)
- Stage 트리 확인: `panda_link0 → ... → panda_hand → panda_leftfinger / panda_rightfinger`
- 그리퍼 관절이 팔 관절의 자식으로 들어와 있음 = 이미 조립된 상태

### 2-2. 경로 B — 실무 다수

로봇 제조사와 그리퍼 제조사가 다르면 파일이 따로 온다. 직접 붙여야 한다.

완성 그리퍼 USD는 `Window > Browsers > Content` → Nucleus `Isaac/Robots`. 이미 USD로 변환된 자산을 쓰는 것뿐이라 ROS 2와 무관.

## 3. Robot Assembler로 병합

`Tools > Robotics > Asset Editor > Robot Assembler`
📖 [도구 §2](레퍼런스_IsaacSim_도구.md#2-robot-assembler) · [용어 §2.3 Articulation](레퍼런스_IsaacSim_용어사전.md#23-articulation)

수동 조립은 프림을 직접 재배치·삭제해야 해서 실수하기 쉽다. Assembler는 양쪽 부착점만 받고 나머지를 자동 처리한다.

### 3-1. 절차

| # | 조작 |
|---|---|
| 1 | UR10 USD 열기 |
| 2 | 그리퍼 USD를 뷰포트로 드래그&드롭 → `ee_link`로 rename |
| 3 | **Select Base Robot** `/ur` · **Attach Point** `wrist_3_link` |
| 4 | **Select Attach Robot** `/ur/ee_link` · **Attach Point** 그리퍼 베이스 링크 · **Namespace** `ee_link` |
| 5 | **Begin Assembling Process** |
| 6 | 자세 어긋나면 **Z +90** 등으로 정렬 |
| 7 | **Assemble and Simulate** — 물리를 실제로 돌려 접합부 확인 |
| 8 | **End Simulation And Finish** |

조립 후 로봇 Prim에 [Variant](레퍼런스_IsaacSim_용어사전.md#15-variant--variantset)가 자동 생성된다. Property → **Variants**에서 그리퍼 교체. 같은 팔에 여러 그리퍼를 비교 실험할 때의 재사용 구조.

### 3-2. 수동 연결 — Assembler가 뭘 대신하는지

| # | 조작 | 이유 |
|---|---|---|
| 1 | `ee_link` Translate/Orient를 손목 플랜지 좌표로 입력 | 조합마다 값이 다름 |
| 2 | `ee_link/root_joint` → **Articulation Root 제거** | articulation은 로봇당 1개 |
| 3 | 같은 조인트의 **Body0** = `/ur/wrist_3_link` | 실제 물리 연결 |
| 4 | `ur` IsaacRobotAPI의 `robotJoints`/`robotLinks`에 `/ur/ee_link` 추가 | [Robot Schema](레퍼런스_IsaacSim_용어사전.md#31-robot-schema--isaacrobotapi)가 그리퍼 인식 |

**Articulation Root가 하나여야 하는 이유** — PhysX 솔버는 트리 전체를 한 번에 푼다. 독립된 root가 둘이면 어느 쪽이 관절을 소유하는지 모호해져 깨진다.

## 4. 조립 직후 물리 다듬기 (Tutorial 7)

조립만으로는 안 돈다.

### 4-1. Articulation 솔버

`ur/root_joint` → Property → **Physics/Articulation** 📖 [용어 §2.12](레퍼런스_IsaacSim_용어사전.md#212-솔버-설정)

| 항목 | 값 | 이유 |
|---|---|---|
| Articulation Enabled | ✅ | 꺼지면 관절 전체가 리지드바디 취급되어 무너짐 |
| Solver Position Iterations | `64` | 그리퍼 접촉엔 기본값 4~8로 부족 |
| Solver Velocity Iterations | `4` | |
| Sleep Threshold | `0.00005` | 미세 움직임에서 로봇이 잠들지 않게 |
| Stabilization Threshold | `0.00001` | |

### 4-2. 그리퍼 마찰 재질

물체를 잡으려면 손가락에 마찰이 필요하다. 기본 재질은 마찰이 낮다. 📖 [용어 §2.10](레퍼런스_IsaacSim_용어사전.md#210-physics-material)

1. `Create > Physics > Physics Material > Rigid Body Material` (이름 `finger`)
2. **Static/Dynamic Friction** `1.0` (고무 근사는 `0.8`)
3. 손가락 콜라이더 메시(`left_inner_finger`, `right_inner_finger`)에 드래그

### 4-3. 관절 힘 제한

`finger_joint` → **Drive/Angular/Max Force** `200`. 데이터시트가 없으면 §7 절차로 찾는다.

### 4-4. Physics Inspector로 즉석 검증

`Tools > Physics > Physics Inspector` 📖 [도구 §3](레퍼런스_IsaacSim_도구.md#3-physics-inspector)

로봇 선택 → 새로고침 → 관절 슬라이더 조작. **Play 없이** 관절 축·제한·충돌을 확인한다.

> **⚠ 쓰고 나면 반드시 창을 닫을 것.** 열어두면 일반 시뮬 거동이 틀어진다.

## 5. Config 생성 · Pick&Place (Tutorial 8~9, 요약)

물성값 검증 범위 밖. 모션 플래닝이 필요해지면 돌아온다.

- **USD → URDF 재수출** — `File > Export URDF`. Lula/플래너 입력용
- **[Lula Robot Description Editor](레퍼런스_IsaacSim_도구.md#5-lula-robot-description-editor)** — 관절 Active/Fixed 지정 + 링크별 충돌 구체 생성. **Play 중에만 동작** — 중간에 멈추면 처음부터
- **예제 난이도 순** — `gripper_control.py` → `follow_target_example.py` → `follow_target_example_rmpflow.py` → `pick_up_example.py`

---

# Part B — 클로즈드루프 · 게인튜닝 · 최적화 (Tutorial 10~12)

## 6. 클로즈드루프 — 그리퍼가 팔과 근본적으로 다른 이유

📖 [용어 §2.4 Closed Loop](레퍼런스_IsaacSim_용어사전.md#24-closed-loop) · [§2.5 Exclude](레퍼런스_IsaacSim_용어사전.md#25-exclude-from-articulation) · [§1.3 Layer](레퍼런스_IsaacSim_용어사전.md#13-layer--sublayer)

### 6-1. 문제

로봇 팔의 관절 트리 = 가지 없는 사슬. PhysX articulation 솔버는 이 트리 구조를 전제로 설계됐다.

평행 그리퍼는 손가락이 **4절 링크(four-bar linkage)** 로 지지된다. 관절 그래프로 그리면 같은 두 몸체 사이에 경로가 둘 생긴다 = **닫힌 루프**.

```
열린 체인 (팔) — OK          닫힌 루프 (평행 그리퍼) — 경고

  base                          base_link
   │                        ┌───────┴───────┐
  shoulder             outer_knuckle   inner_knuckle
   │                        │               │
  elbow                outer_finger ── inner_finger
   │                          ↑ 여기서 다시 만난다
  wrist
                       base_link → finger 경로가 2개
```

- 이 기구학이 평행 운동을 만드는 원리 → **회피 불가**
- 그대로 두면 물리 경고. 최악의 경우 관절이 튀거나 발산

### 6-2. 해결 — 루프 관절 하나를 제외

루프 관절 1개를 articulation 솔버 계산에서 뺀다. 관절은 물리적으로 남되 낮은 우선순위의 maximal-coordinate 조인트로 처리된다.

**선정 기준**

| 기준 | 이유 |
|---|---|
| 기능 영향 적음 | 빠져도 그리퍼 동작이 안 바뀜 |
| limit 없음 | limit은 솔버가 지켜야 하는데 빠지면 불가 |
| 드라이브 불필요 | 힘을 만드는 관절은 정확히 풀려야 함 |
| 순수 공간 구속 | 「여기 붙어 있어라」만 하는 관절 |

Robotiq → `left/right_inner_knuckle_joint`가 해당.

**절차** — 해당 조인트 Prim → Property → **Physics** → **Exclude From Articulation** 체크 (좌·우 각각)

→ 루프 경고 사라지고 그리퍼는 정상 시뮬레이션.

### 6-3. Mimic Joint — 손가락 두 개를 하나의 입력으로

📖 [용어 §2.9](레퍼런스_IsaacSim_용어사전.md#29-mimic-joint)

루프를 끊어도 끝이 아니다. 실제 그리퍼는 모터 하나로 양쪽 손가락이 동시에 움직인다. 관절을 따로 제어하면 그 관계를 계속 손으로 맞춰야 한다.

```
finger_joint (master, Drive 있음)
      │  q_follower = q_master × Gearing
      ▼
outer_knuckle_joint (follower, Drive 없음)
```

| 항목 | 값 | 의미 |
|---|---|---|
| 대상 관절 | `right_outer_knuckle_joint` | 종속시킬 관절 |
| Reference Joint | `finger_joint` | 마스터 |
| Gearing | `-1.0` | 마스터 각도에 곱할 비율. 음수 = 반대 방향 |
| Rotation Axis | `rotX` | 1 DOF 관절에선 무의미 |

**⚠ 주의 2가지**
1. mimic 관절 자체에 Drive 걸지 않음 → reference에서 자동 복사. 걸면 두 제어가 충돌
2. 기존 Drive가 있으면 **값을 0으로 지운 뒤** mimic 추가

절차 — Property → **Add > Physics > Mimic Joint**

→ 「그리퍼 열기/닫기」가 스칼라 하나로 제어됨.

### 6-4. 힘 기반 파지 — 위치제어를 안 쓰는 이유

📖 [용어 §2.8 Joint Drive](레퍼런스_IsaacSim_용어사전.md#28-joint-drive)

「몇 도까지 닫아라」(위치제어)로 제어하면 물체 크기가 조금만 달라도 못 잡거나 으스러뜨린다. 실제 파지는 **Stiffness = 0**, Damping·Max Force만으로 민다. "정지 위치"가 아니라 "얼마나 세게 미는가"로 제어.

| 관절 | Stiffness | Damping | Max Force | Max Velocity | 역할 |
|---|---:|---:|---:|---:|---|
| `finger_joint` | **0.0** | 5000.0 | 180.0 | 130.0 | 메인 액추에이터. 힘으로만 |
| `outer_finger_joint` | 0.05 | 5000.0 | 180.0 | 130.0 | 약한 스프링으로 평행 유지 |

**실측 관찰**
- payload 200g 정상 → 2.5kg(정격) 미끄러짐 → **물리 스텝 80Hz로 해결** (접촉 계산 빈도 부족)
- Max Force 180 → 5.0으로 **낮추자** 긴 원통 파지가 오히려 안정화 → 힘이 세면 접촉점 미세 슬립이 생겨 역설적으로 불안정
- 같은 축의 문제가 [용어 §2.13 Physics Timestep](레퍼런스_IsaacSim_용어사전.md#213-physics-timestep)에 있다. P1의 τ≈26ms 발견과 동일 계열

### 6-5. 충돌 형상과 Self-Collision

📖 [용어 §2.7](레퍼런스_IsaacSim_용어사전.md#27-collider-approximation)

| 옵션 | 그리퍼에서의 판단 |
|---|---|
| Convex Hull (기본) | 손가락 안쪽 오목부가 메워짐 → 물체가 실제보다 일찍 닿은 것으로 계산 |
| **Convex Decomposition** | 손가락 안쪽 윤곽 유지 → 그리퍼엔 이쪽 |
| Self-Collision Enabled | 임포트 기본값 꺼짐. 손가락 겹침을 막으려면 로봇 루트 → **Articulation Root Options**에서 켬 |

시각화 — 뷰포트 눈 아이콘 → `Show By Type > Physics > Colliders > All`

## 7. Gain Tuner 절차 (Tutorial 11)

📖 **도구 상세** → [도구 §1](레퍼런스_IsaacSim_도구.md#1-gain-tuner) (UI 필드·테스트 파형·저장·알려진 버그)
📖 값의 의미 → [용어 §2.11 ωₙ/ζ](레퍼런스_IsaacSim_용어사전.md#211-natural-frequency--damping-ratio)

### 7-1. 위치 드라이브

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

### 7-2. 속도 드라이브 (바퀴 등)

- Stiffness = 0 고정 → Damping만 ↑ → 목표 속도 수렴
- 예상 부하만큼 **+10%** 여유
- Max Joint Velocity / Max Force로 상한

### 7-3. 실전 기준

| 기준 | 값 |
|---|---|
| 목표 오버슈트 | **1% 이내** |
| 중력보상 내장 로봇 | Disable Gravity 켜고 순수 제어 응답만 |
| 튜닝 순서 | 관절을 **소그룹으로** 먼저. 6축 동시 튜닝 금지 |
| 최대속도 | 임포터 기본값은 비현실적 → 실제 스펙으로 낮춤 |

결과는 **Run Test**로 지령 vs 추종 플롯 확인. [scripts/p1_drive_tuning.py](../scripts/p1_drive_tuning.py)가 이 과정을 스크립트로 재현해 CSV로 남기는 버전이다. **GUI로 감을 잡고 스크립트로 정량화.**

## 8. 에셋 최적화 (Tutorial 12)

CAD에서 온 로봇은 링크 하나에 메시가 수십 개(나사·브래킷·로고까지 별도). 공식 예제(Jetbot) 정리 시 **40 → 64 FPS**.

### 8-1. 메시 병합

`Tools > Robotics > Asset Editors > Mesh Merge Tool` 📖 [도구 §4](레퍼런스_IsaacSim_도구.md#4-mesh-merge-tool)

1. 병합할 링크 선택
2. **Combine Materials** 체크 · 저장 위치 `<로봇>/Looks`
3. **Merge** → 시각 메시 수십 개가 하나로
4. 결과 메시 transform 클리어 → `Visuals` Scope로 이동 → `/Merged` 삭제

렌더링 비용은 **메시 개수(draw call)** 에 비례하는 부분이 크다. 폴리곤 총량이 같아도 개수를 줄이면 가벼워진다.

### 8-2. Scenegraph Instancing

📖 [용어 §1.6](레퍼런스_IsaacSim_용어사전.md#16-instanceable)

좌·우 바퀴, 그리퍼 손가락 둘처럼 기하학적으로 동일한 부품이 데이터를 공유하게 만든다.

1. 대표 하나(`left_wheel`)만 남기고 나머지(`right_wheel`) 삭제
2. 삭제한 쪽의 Reference 경로를 대표 프림으로 갱신
3. 관련 프림 다중선택 → Property → **Instanceable** 체크
4. 레퍼런스 아이콘이 파란 「I」로 바뀌면 완료

**⚠ 제약** — 자식 속성 개별 수정 불가. **완전 대칭 부품에만** 적용. 좌우가 미세하게 다른 부품(케이블 배선 등)엔 쓰지 않는다.

### 8-3. 물리 성능

- 시각 메시보다 **콜라이더가 성능 영향이 크다** — 접촉점 계산이 매 스텝 반복
- 바퀴처럼 회전하는 단순 형상은 **실린더/구 콜라이더**로 근사 → 성능도 오르고 지면 접촉도 부드러워짐 (각진 메시 콜라이더는 굴러갈 때 미세하게 튐)
- **부위별로 다른 근사를 쓰는 게 핵심** — 「전체를 정밀하게」와 「전체를 가볍게」는 둘 다 오답

### 8-4. 렌더링

| 항목 | 권장 |
|---|---|
| 라이트 개수 | 10개 초과 시 샘플 기반 라이팅으로 자동 전환 → 급격히 느려짐 |
| 반투명 재질 | 기본 OmniPBR보다 훨씬 무거움. 로봇 표면엔 불필요 |

---

## 9. 체크리스트

| 단계 | 할 일 | 확인 |
|---|---|---|
| §2 | `franka_description` 임포트 | 그리퍼 관절이 팔 관절의 자식으로 |
| §3 | UR10 + 그리퍼 Assembler 조립 | Articulation Root **1개**만 |
| §4 | Solver Iterations · 마찰 재질 `1.0` | Physics Inspector 확인 후 **창 닫기** |
| §6-2 | `Exclude From Articulation` | 루프 경고 사라짐 |
| §6-3 | Mimic Joint | 명령 하나로 양쪽 손가락 대칭 동작 |
| §6-4 | Stiffness = 0 힘 기반 파지 | 크기 다른 물체도 잡힘 |
| §6-5 | Convex Decomposition + Self-Collision | 손가락 겹침 없음 |
| §7 | Gain Tuner 6단계를 관절 1개에 | 오버슈트 1% 이내 |
| §8-1 | Mesh Merge 1개 링크 | FPS 전후 비교 |

---

## 참고

- [Tutorial 6 — Setup a Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_import_assemble_manipulator.html)
- [Tutorial 7 — Configure a Manipulator](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_configure_manipulator.html)
- [Tutorial 8 — Generate Robot Configuration File](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_generate_robot_config.html)
- [Tutorial 9 — Pick and Place Example](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/tutorial_pickplace_example.html)
- [Tutorial 10 — Rig Closed-Loop Structures](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/rig_closed_loop_structures.html)
- [Tutorial 11 — Tuning Joint Drive Gains](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/joint_tuning.html)
- [Tutorial 12 — Asset Optimization](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/robot_setup_tutorials/optimizing_asset.html)
