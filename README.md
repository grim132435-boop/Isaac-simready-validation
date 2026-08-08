# Sim-Ready 물성값 검증 파이프라인 (Isaac Sim 5.1)

정적 3D 에셋과 로봇을 **물리적으로 맞는 상태**로 만드는 과정을 정량 지표로 검증한다.

## 문제

시뮬레이션 에셋은 "형상이 맞는 것"과 "물리가 맞는 것"이 다르다.

- **로봇 쪽** — URDF에는 관절의 물리적 성질(`limit`, `dynamics/damping`, `inertial`)은 있지만
  액추에이터 제어 모델(**drive stiffness / damping**)이 **없다.**
  임포트 직후 로봇은 기구학만 맞고 제어 특성은 근거 없는 기본값이라, 그대로 돌리면
  진동하거나 처지거나 오버슈트한다.
- **에셋 쪽** — CAD를 시뮬레이터로 옮기면 형상만 남고 작동 메커니즘이 사라진다.
  컨베이어는 돌지 않고 서랍은 열리지 않는다. 관절 구조와 물성을 새로 부여해야 한다.
- **결합** — 에셋의 물성값이 틀리면 **로봇의 거동이 틀어진다.**
  가상에서 뻑뻑하게 설정된 서랍을 실제처럼 가볍게 열면 로봇이 과도하게 움직인다.

그런데 "얼마나 맞아야 맞는 것인가"에 대한 **공유된 기준이 없다.**
이 저장소는 그 기준을 숫자로 만드는 시도다.

## 구성

| 단계 | 내용 | 산출 지표 | 상태 |
|---|---|---|---|
| **P1** | 로봇 URDF 임포트 → drive gain 직접 주입 → 추종오차 측정 | 중력 처짐 [deg], 궤적 추종 RMS [deg] | 초안 |
| **P2** | 관절 0인 정적 에셋에 Joint·질량·마찰 부여 (Sim-Ready 변환) | 변환 성공 / 스펙 준수 | 예정 |
| **P3** | 로봇이 에셋을 조작 → 물성 오차가 거동에 미치는 영향 정량화 | 물성 오차 → 거동 오차 민감도 | 예정 |

각 단계는 독립적으로 완결된다. P1만으로도 결과가 나온다.

### P1 — drive gain과 추종오차

두 가지를 측정한다.

- **T1. 중력 처짐 (static)** — 팔을 수평으로 뻗은 자세에서 정상상태 관절 오차.
  중력 토크가 최대가 되는 자세라 gain 부족이 가장 잘 드러난다.
- **T2. 궤적 추종 (dynamic)** — 사인 궤적을 따라갈 때의 RMS 오차.

`--payload` 로 엔드이펙터 질량을 추가하면, **payload를 반영하지 않고 잡은 gain이
어떻게 처짐을 만드는지**를 정량으로 볼 수 있다.

> 이 테스트는 실제 현장 사례를 시뮬레이션에서 재현한 것이다.
> 무빙실러 셋업에서 실러 엔드이펙터의 payload가 로봇에 반영되지 않아
> TCP가 약 3mm 처지고 실링 품질 NG가 반복된 적이 있다.
> 자세와 경로를 바꾸는 임시방편 대신 payload 미반영이 원인임을 규명하고
> 무게를 적용해 정확도를 회복했다. T1은 그 문제 구조를 그대로 옮긴 것이다.

대상 로봇은 **UR10**(Universal Robots, 협동로봇)이다.
URDF importer 익스텐션에 기본 동봉돼 있어 별도 다운로드가 필요 없다.

## 환경

| 항목 | 버전 |
|---|---|
| Isaac Sim | **5.1.0** |
| Python | **3.11** |
| PyTorch | 2.7.0 + **cu128** |
| GPU | RTX 5070 (Blackwell, sm_120) |

> **버전을 핀하는 이유** — Isaac Sim 6.0이 이미 나와 있지만 "Early Developer Release"이고,
> 지원하는 Isaac Lab이 3.0.0 Beta 2뿐이며 의존성 충돌이 보고돼 있다.
> 또한 6.0은 PyTorch 기반 Core API를 Warp 기반으로 교체하는 코어 재설계가 진행 중이고
> Python을 3.12로 고정한다. `main` 브랜치 문서의 "Python 3.12"는 6.0 기준 숫자이므로
> 5.1에 적용하면 안 된다.

### 설치

```bash
# Miniconda (JustMe 설치 — 관리자 권한 불필요)
conda create -p D:\ic\env python=3.11 -y --override-channels -c conda-forge
conda activate D:\ic\env

# pip 임시 디렉터리를 데이터 드라이브로 (시스템 드라이브 공간 부족 회피)
set TEMP=D:\ic\tmp
set TMP=D:\ic\tmp

pip install "isaacsim[all,extscache]==5.1.0" --extra-index-url https://pypi.nvidia.com --cache-dir D:\ic\pipcache
pip install -U torch==2.7.0 torchvision==0.22.0 --index-url https://download.pytorch.org/whl/cu128
```

`conda-forge` 만 쓰는 이유 — Anaconda `defaults` 채널은 ToS 동의가 필요하고
일정 규모 이상 조직의 상용 이용 시 유료 라이선스 대상이다. conda-forge는 그 제약이 없다.

## 실행

```bash
python scripts/p1_drive_tuning.py --stiffness 1e5 --damping 5e3
python scripts/p1_drive_tuning.py --sweep                 # gain 스윕
python scripts/p1_drive_tuning.py --payload 5.0 --gui     # payload 추가 + GUI
```

결과는 `results/p1_drive_tuning.csv` 에 기록된다.

## 결과 (P1, 실측)

측정 대상: UR10 (협동로봇) · Isaac Sim 5.1.0 · PhysX · 120Hz · RTX 5070

### 1. 중력 처짐은 게인으로 잡힌다 — 97% 감소

수평으로 뻗은 자세에서 정상상태 관절 오차.

| Stiffness | Damping | 처짐 max | 처짐 RMS |
|---:|---:|---:|---:|
| 1,000 | 50 | 0.0741° | 0.0305° |
| 10,000 | 500 | 0.0074° | 0.0032° |
| 100,000 | 5,000 | **0.0021°** | 0.0010° |
| 1,000,000 | 50,000 | 0.0021° | 0.0009° |

**0.0741° → 0.0021° (97.2% 감소).** 10⁵ 이후로는 포화한다 —
게인을 더 올려도 얻는 게 없고 수치 불안정 위험만 커지므로 **10⁵ 부근이 작업점**이다.

### 2. 궤적 추종오차는 게인으로 안 잡힌다 — 지연이 지배한다

같은 스윕에서 동적 추종오차(15° 진폭, 0.5Hz 사인)는 **게인과 무관하게 평평했다.**

| Stiffness | 궤적 RMS | 궤적 max |
|---:|---:|---:|
| 1,000 | 0.8776° | 2.1574° |
| 10,000 | 0.8755° | 2.1471° |
| 100,000 | 0.8755° | 2.1468° |
| 1,000,000 | 0.8755° | 2.1468° |

게인을 **1000배** 올렸는데 오차가 0.24% 변했다. 지표가 파라미터에 반응하지 않으면
지표를 의심해야 한다. 두 번 의심했고, 두 개를 찾았다.

**(1) 초기 과도응답 오염 — 수정함**
관절마다 다른 위상을 주는 바람에 t=0에서 10.6°짜리 계단 입력이 걸렸고,
그 과도응답이 통계를 지배했다. 위상을 정렬하고 초기 구간을 통계에서 제외하자
`track_max` 가 **10.02° → 2.15°** 로 떨어졌다. 그래도 평탄함은 남았다.

**(2) 남은 평탄함의 정체 — 고정 시간지연**
게인을 고정(10⁵)하고 주파수만 바꿔 측정했다.

| 주파수 | 궤적 RMS | RMS ÷ f | 역산한 지연 τ |
|---:|---:|---:|---:|
| 0.125 Hz | 0.2083° | 1.666 | 25.0 ms |
| 0.25 Hz | 0.4373° | 1.749 | 26.3 ms |
| 0.5 Hz | 0.8755° | 1.751 | 26.3 ms |

**오차가 주파수에 정확히 비례한다.** 순수 시간지연 τ 를 가진 계는
`RMS = A·ω·τ/√2` 를 따르므로 역산하면 τ 가 세 점 모두에서 **약 26ms** 로 일치한다.
물리 스텝(1/120초 = 8.33ms) 기준 **약 3스텝**이다.

즉 이 구간의 오차는 **강성 부족이 아니라 지령→구동→관측 파이프라인의 지연**이다.
게인 튜닝으로는 원리적으로 줄일 수 없다.

### 이게 왜 중요한가 — Sim-to-Real 관점

**물리 충실도는 질량·마찰 같은 "값"만의 문제가 아니라 "타이밍"의 문제이기도 하다.**

실제 로봇 컨트롤러에도 통신·연산 지연이 있다. 시뮬이 그 지연을 모델링하지 않으면,
아무리 물성값을 맞춰도 **시뮬-실기 갭에 지연 항이 남는다.** 그리고 그 항은
물성값 튜닝으로는 절대 닫히지 않는다 — 위 실험이 정확히 그걸 보여준다.

반대로 이 분해가 되면 갭을 **"게인으로 닫을 수 있는 몫"과 "지연으로만 설명되는 몫"** 으로
나눌 수 있다. 정확도 목표를 "몇 %"라는 단일 숫자 대신 원인별로 말할 수 있게 된다.

### 재현

```bash
python scripts/p1_drive_tuning.py --sweep      --out results/p1_sweep.csv
python scripts/p1_drive_tuning.py --freq-scan  --out results/p1_freqscan.csv
```

원자료: [results/p1_sweep.csv](results/p1_sweep.csv) · [results/p1_freqscan.csv](results/p1_freqscan.csv)

## 참고

- [Isaac Sim 5.1 — Import URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html)
- [Isaac Sim 5.1 — Requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)
- [SimReady Specification](https://docs.omniverse.nvidia.com/simready/latest/overview/simready-spec.html)
- [SimReady Foundation](https://nvidia.github.io/simready-foundation/guides/getting_started.html)
