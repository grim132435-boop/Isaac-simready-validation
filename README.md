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

## 결과

[측정 예정]

## 참고

- [Isaac Sim 5.1 — Import URDF](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/importer_exporter/import_urdf.html)
- [Isaac Sim 5.1 — Requirements](https://docs.isaacsim.omniverse.nvidia.com/5.1.0/installation/requirements.html)
- [SimReady Specification](https://docs.omniverse.nvidia.com/simready/latest/overview/simready-spec.html)
- [SimReady Foundation](https://nvidia.github.io/simready-foundation/guides/getting_started.html)
