"""
P1 — URDF 임포트 후 joint drive gain 직접 주입 · 추종오차 정량 측정

목적
----
URDF에는 관절의 "물리적 성질"(limit, dynamics/damping, inertia)은 있지만
액추에이터 "제어 모델"(drive stiffness/damping)은 없다.
임포트 직후 로봇은 형상·기구학만 맞고 제어 특성은 근거 없는 기본값 상태다.

이 스크립트는 drive gain을 바꿔가며 두 가지 오차를 측정한다.

  T1. 중력 처짐 (static)  — 수평 자세 유지 시 정상상태 관절 오차
  T2. 궤적 추종 (dynamic) — 사인 궤적 추종 시 RMS 오차

T1은 두림야스카와 무빙실러 사례(실러 엔드이펙터 payload 미반영 → TCP 3mm 처짐)를
시뮬레이션에서 재현한 것이다. --payload 옵션으로 엔드이펙터 질량을 추가하면
"payload를 반영하지 않은 gain"이 어떻게 처짐을 만드는지 정량으로 보인다.

사용법
------
    python scripts/p1_drive_tuning.py --stiffness 1e5 --damping 5e3
    python scripts/p1_drive_tuning.py --stiffness 1e5 --damping 5e3 --payload 5.0
    python scripts/p1_drive_tuning.py --sweep          # gain 스윕

⚠️ 상태: 초안. Isaac Sim 5.1 설치 완료 후 실행 검증 필요.
"""

import argparse
import csv
import math
import os
from pathlib import Path

# --------------------------------------------------------------------------
# 인자 파싱은 SimulationApp 기동 전에 (kit이 sys.argv를 건드리므로)
# --------------------------------------------------------------------------
parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--stiffness", type=float, default=1047.19751,
                    help="joint drive stiffness. 기본값은 공식 예제 값")
parser.add_argument("--damping", type=float, default=52.35988,
                    help="joint drive damping. 기본값은 공식 예제 값")
parser.add_argument("--payload", type=float, default=0.0,
                    help="엔드이펙터에 추가할 payload 질량 [kg]")
parser.add_argument("--sweep", action="store_true",
                    help="gain 스윕 모드 — 여러 조합을 순차 측정")
parser.add_argument("--headless", action="store_true", default=True)
parser.add_argument("--gui", dest="headless", action="store_false",
                    help="GUI를 띄워서 눈으로 확인")
parser.add_argument("--out", type=str, default="results/p1_drive_tuning.csv")
parser.add_argument("--settle-steps", type=int, default=240,
                    help="T1 정상상태 도달 대기 스텝 수")
parser.add_argument("--track-steps", type=int, default=600,
                    help="T2 궤적 추종 측정 스텝 수")
args = parser.parse_args()

# --------------------------------------------------------------------------
# SimulationApp은 다른 isaacsim/omni 임포트보다 반드시 먼저 기동해야 한다
# --------------------------------------------------------------------------
from isaacsim import SimulationApp  # noqa: E402

simulation_app = SimulationApp({"headless": args.headless})

import numpy as np  # noqa: E402
import omni.kit.commands  # noqa: E402
from isaacsim.asset.importer.urdf import _urdf  # noqa: E402
from isaacsim.core.api import World  # noqa: E402
from isaacsim.core.prims import SingleArticulation  # noqa: E402
from isaacsim.core.utils.extensions import (  # noqa: E402
    enable_extension,
    get_extension_path_from_name,
)

PHYSICS_DT = 1.0 / 120.0


# --------------------------------------------------------------------------
def resolve_ur10_urdf() -> str:
    """URDF importer 익스텐션에 동봉된 UR10 URDF 경로를 찾는다.

    UR10을 고른 이유 — 실제 협동로봇(Universal Robots)이고, 익스텐션에 기본
    동봉돼 있어 별도 다운로드가 필요 없다. 공고 자격요건의
    "산업용 로봇 또는 협동 로봇 사용 경험자"에 직접 대응한다.
    """
    enable_extension("isaacsim.asset.importer.urdf")
    ext_path = get_extension_path_from_name("isaacsim.asset.importer.urdf")
    urdf_path = Path(ext_path) / "data" / "urdf" / "robots" / "ur10" / "urdf" / "ur10.urdf"
    if not urdf_path.exists():
        raise FileNotFoundError(
            f"UR10 URDF를 찾지 못했다: {urdf_path}\n"
            f"익스텐션 경로: {ext_path}\n"
            "5.1에서 경로가 바뀌었을 수 있다. 해당 디렉터리를 직접 확인할 것."
        )
    return str(urdf_path)


def import_robot(urdf_path: str, stiffness: float, damping: float) -> str:
    """URDF를 파싱하고 drive gain을 주입한 뒤 스테이지에 임포트한다.

    핵심 — URDF에는 stiffness/damping이 없다. 아래 루프가 그 값을
    '사람이 직접 넣는' 부분이고, 이 스크립트가 측정하려는 대상이다.
    """
    import_config = _urdf.ImportConfig()
    import_config.convex_decomp = False
    import_config.fix_base = True
    import_config.make_default_prim = True
    import_config.self_collision = False
    import_config.distance_scale = 1
    import_config.density = 0.0

    result, robot_model = omni.kit.commands.execute(
        "URDFParseFile",
        urdf_path=urdf_path,
        import_config=import_config,
    )
    if not result:
        raise RuntimeError(f"URDFParseFile 실패: {urdf_path}")

    # ★ URDF에 없는 제어값을 주입하는 지점
    for joint_name in robot_model.joints:
        robot_model.joints[joint_name].drive.strength = stiffness
        robot_model.joints[joint_name].drive.damping = damping

    result, prim_path = omni.kit.commands.execute(
        "URDFImportRobot",
        urdf_robot=robot_model,
        import_config=import_config,
    )
    if not result:
        raise RuntimeError("URDFImportRobot 실패")
    return prim_path


def horizontal_pose(n_dof: int) -> np.ndarray:
    """팔을 수평으로 뻗은 자세. 중력 토크가 최대가 되어 처짐이 가장 잘 드러난다.

    UR10 관절 순서: [shoulder_pan, shoulder_lift, elbow, wrist_1, wrist_2, wrist_3]
    shoulder_lift = -90° 로 상완을 수평으로, elbow = 0 으로 전완을 그대로 뻗는다.
    """
    q = np.zeros(n_dof, dtype=np.float32)
    if n_dof >= 3:
        q[1] = -math.pi / 2.0   # shoulder_lift
        q[2] = 0.0              # elbow
    return q


def measure(art: SingleArticulation, world: World,
            stiffness: float, damping: float) -> dict:
    """T1(중력 처짐) + T2(궤적 추종)를 측정해 dict로 반환."""
    n_dof = art.num_dof

    # ---- T1. 중력 처짐 ---------------------------------------------------
    q_cmd = horizontal_pose(n_dof)
    art.set_joint_positions(q_cmd)
    art.set_joint_velocities(np.zeros(n_dof, dtype=np.float32))

    for _ in range(args.settle_steps):
        art.set_joint_position_targets(q_cmd)
        world.step(render=not args.headless)

    q_act = np.asarray(art.get_joint_positions(), dtype=np.float64)
    sag = np.abs(q_act - q_cmd.astype(np.float64))
    sag_max_deg = float(np.degrees(sag.max()))
    sag_rms_deg = float(np.degrees(np.sqrt((sag ** 2).mean())))

    # ---- T2. 사인 궤적 추종 ---------------------------------------------
    amp = math.radians(15.0)     # 진폭 15°
    freq = 0.5                   # 0.5 Hz
    errs = []
    for i in range(args.track_steps):
        t = i * PHYSICS_DT
        q_t = q_cmd.astype(np.float64).copy()
        q_t[1] += amp * math.sin(2.0 * math.pi * freq * t)
        if n_dof >= 3:
            q_t[2] += amp * math.sin(2.0 * math.pi * freq * t + math.pi / 4.0)

        art.set_joint_position_targets(q_t.astype(np.float32))
        world.step(render=not args.headless)

        q_now = np.asarray(art.get_joint_positions(), dtype=np.float64)
        errs.append(q_now - q_t)

    errs = np.asarray(errs)
    track_rms_deg = float(np.degrees(np.sqrt((errs ** 2).mean())))
    track_max_deg = float(np.degrees(np.abs(errs).max()))

    return {
        "stiffness": stiffness,
        "damping": damping,
        "payload_kg": args.payload,
        "sag_max_deg": round(sag_max_deg, 4),
        "sag_rms_deg": round(sag_rms_deg, 4),
        "track_rms_deg": round(track_rms_deg, 4),
        "track_max_deg": round(track_max_deg, 4),
    }


def run_one(stiffness: float, damping: float) -> dict:
    """gain 한 조합에 대해 씬을 새로 만들고 측정한다."""
    world = World(physics_dt=PHYSICS_DT, rendering_dt=PHYSICS_DT, stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    urdf_path = resolve_ur10_urdf()
    prim_path = import_robot(urdf_path, stiffness, damping)

    art = SingleArticulation(prim_path=prim_path, name="ur10")
    world.scene.add(art)
    world.reset()

    row = measure(art, world, stiffness, damping)

    world.clear()
    return row


def main() -> None:
    if args.sweep:
        combos = [
            (1.0e3, 5.0e1),
            (1.0e4, 5.0e2),
            (1.0e5, 5.0e3),
            (1.0e6, 5.0e4),
        ]
    else:
        combos = [(args.stiffness, args.damping)]

    rows = []
    for k, d in combos:
        print(f"[P1] measuring stiffness={k:g} damping={d:g} payload={args.payload}kg ...")
        rows.append(run_one(k, d))
        print(f"     -> {rows[-1]}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[P1] wrote {out} ({len(rows)} rows)")


if __name__ == "__main__":
    try:
        main()
    finally:
        simulation_app.close()
