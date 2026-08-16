---
type: readme
project: Isaac-simready-validation
updated: 2026-08-16
tags: [project, simready, readme]
---
# Isaac-simready-validation — 이 폴더가 무엇인가

> 옆 폴더 `SO-ARM101_SimToReal` 과 헷갈릴 때 이 파일을 먼저 본다.

## 한 줄

정적 3D 에셋과 로봇을 **물리적으로 맞는 상태**로 만드는 과정을 **정량 지표로 검증**한다.
자세한 문제의식과 P1/P2/P3 구성은 [README.md](README.md), 이어서 할 일은 [RESUME.md](RESUME.md).

## 옆 폴더와 구분하는 법 — **로봇을 보면 된다**

| | **이 폴더** (Isaac-simready-validation) | 옆 폴더 (SO-ARM101_SimToReal) |
|---|---|---|
| 로봇 | **UR10 / Robotiq 2F-85** | **SO-ARM101** (5자유도 저가 팔) |
| 목적 | 에셋·로봇의 **물성값이 맞는지 검증**한다 | 정책을 **학습**시킨다 (ACT, RL) |
| 지표 | 중력 처짐[deg], 궤적 추종 RMS[deg] | 파지 성공률, sim-real 갭 |
| 산출 | 검증 스코어카드, drive gain 값 | 학습된 정책, LeRobot 데이터셋 |

**UR10이 나오면 여기, SO-ARM101이 나오면 옆.** 이 한 가지로 거의 다 갈린다.

## 이 폴더가 겸하고 있는 것 두 가지

프로젝트 문서 말고도 **두 프로젝트가 공유하는 것**이 여기 얹혀 있다. 알고 있어야 덜 헷갈린다.

**1) 환경 구축 가이드 (공용)**
```
docs/PC방_환경_재구축_가이드.md
```
Isaac Sim 설치를 두 프로젝트가 같이 쓰므로 한 곳에만 둔다. SO-ARM101 쪽 절차
(B-10-1 LeRobot, B-11 자동 커밋)도 여기 들어 있다.

**2) Isaac Sim 레퍼런스 (실습 문서의 짝)**
```
docs/레퍼런스_IsaacSim_도구.md      ← GUI_실습_* 이 11회 참조
docs/레퍼런스_IsaacSim_용어사전.md  ← GUI_실습_* 이 17회 참조
docs/문서작성_가이드.md
```
일반 자료처럼 보이지만 **실습 문서와 상호참조가 28곳**이라 떼면 링크가 다 깨진다.
그래서 볼트로 빼지 않고 여기 둔다. 2026-08-16에 옮겨봤다가 되돌린 결과다.

> **프로젝트와 무관한 일반 지식은 볼트로 갔다.** 아래 셋은 `30_Study/topics/` 에 있다.
> `[[IsaacSim_핵심개념]]` · `[[IsaacSim_학습커리큘럼]]` · `[[강화학습_기초개념]]`

## 폴더 구성

```
Isaac-simready-validation/
├── 00_README.md      이 파일 (폴더 정체)
├── README.md         프로젝트 본문 — 문제의식, P1/P2/P3 구성
├── RESUME.md         이어서 할 일
├── docs/             실습·레퍼런스·환경 가이드
├── scripts/          p1_drive_tuning.py, smoke_test.py 등
└── results/          측정 원자료
```
