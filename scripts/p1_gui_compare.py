"""P1 보조 — 저게인·고게인 UR10 두 대를 한 씬에 세우고 실시간 그래프로 비교한다.

목적
----
지금까지 만든 chart_gain_sweep.png / chart_freq_scan.png 는 다 끝난 결과의 스냅샷이다.
이 스크립트는 반대로 "그 결과가 만들어지는 과정"을 GUI로 직접 보여준다.

  좌(저게인) / 우(고게인) 로 같은 자리에 UR10 두 대를 세우고
  동일한 목표 궤적을 동시에 먹인 뒤, Isaac Sim의 Gain Tuner 확장이 보여주는 것과
  같은 형태로 "목표값 vs 실제값" 그래프를 matplotlib 창에 실시간으로 그린다.

씬 안에서 이미 눈으로 처짐 차이가 보이고, 옆의 그래프에서는 그 차이가
정확히 몇 도(°)인지 숫자로 확인된다.

두 로봇 배치 방식 (중요 — 한 번 잘못 만들었던 방식)
--------------------------------------------------
처음에는 URDF를 "/ur10"에 임포트한 뒤 `MovePrim`으로 "/ur10_low"로 옮기고,
같은 자리에 두 번째 로봇을 다시 임포트하는 방식을 썼다. 그런데 `MovePrim`이
URDF 임포터가 만든 fixed-base 관절(root_joint)의 내부 relationship을 깨뜨려서
로봇이 실제로는 고정되지 않고 쓰러지며 두 로봇이 서로 겹치는 버그가 났다
(sag 값도 3~8°로 튀어서 바로 티가 났다).

지금 방식 — 게인별로 별도 USD 파일(D:\\ic\\tmp\\gui_compare\\)에 로봇을 굽고,
`add_reference_to_stage()`로 그 파일을 서로 다른 두 prim 경로에 **참조**로
배치한다. 참조는 프림을 옮기는 게 아니라 새로 인스턴스화하는 것이라
내부 관절 relationship이 절대 깨지지 않는다 — Isaac Sim이 멀티로봇 씬에
공식적으로 쓰는 방식과 같다.

⚠️ GUI 전용 스크립트다 (--headless 옵션 없음). 지시서 규칙 2에 따라 다른
Isaac Sim 프로세스(GUI든 헤드리스든)가 떠 있는 동안에는 실행하지 말 것 — VRAM 부담.

사용법
------
    python scripts/p1_gui_compare.py
    python scripts/p1_gui_compare.py --stiffness-low 1000 --stiffness-high 1e5
"""

import argparse
import math
from pathlib import Path

# --------------------------------------------------------------------------
# 인자 파싱은 SimulationApp 기동 전에 (kit이 sys.argv를 건드리므로)
# --------------------------------------------------------------------------
parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--stiffness-low", type=float, default=1000.0)
parser.add_argument("--damping-low", type=float, default=50.0)
parser.add_argument("--stiffness-high", type=float, default=1.0e5)
parser.add_argument("--damping-high", type=float, default=5.0e3)
parser.add_argument("--freq", type=float, default=0.5, help="T2 사인 궤적 주파수 [Hz]")
parser.add_argument("--separation", type=float, default=4.0,
                    help="두 로봇 베이스 사이 간격 [m] (Y축). 2.0m로 줄였다가 첫 physics "
                         "스텝에서 바로 크래시가 났다(PyEval_RestoreThread 네이티브 폴트, "
                         "재현 2회) — set_joint_positions()가 자세를 순간이동시키는데, "
                         "그 자세에서 두 팔이 겹칠 만큼 가까우면 첫 스텝에 극심한 관통이 "
                         "생겨 솔버가 죽는 것으로 보인다. UR10 도달범위(~1.3m)가 둘 합쳐 "
                         "최대 2.6m라 4.0m를 새 기본값으로 — 이 값도 실행해서 완주 확인했다. "
                         "8.0m는 확실히 안전하지만(완주 검증됨) 화면에 너무 멀어 보인다는 "
                         "피드백이 있었다")
parser.add_argument("--settle-steps", type=int, default=240)
parser.add_argument("--track-steps", type=int, default=600)
parser.add_argument("--track-settle-steps", type=int, default=120)
parser.add_argument("--plot-every", type=int, default=3,
                    help="N 스텝마다 그래프를 갱신 (너무 자주 갱신하면 느려진다)")
parser.add_argument("--out", type=str, default="results/p1_gui_compare.csv")
parser.add_argument("--asset-dir", type=str, default=r"D:\ic\tmp\gui_compare",
                    help="게인별로 구운 로봇 USD 파일을 저장할 스크래치 디렉터리")
args = parser.parse_args()

# --------------------------------------------------------------------------
# SimulationApp은 다른 isaacsim/omni 임포트보다 반드시 먼저 기동해야 한다
# --------------------------------------------------------------------------
from isaacsim import SimulationApp  # noqa: E402

simulation_app = SimulationApp({"headless": False})

import csv  # noqa: E402

import matplotlib  # noqa: E402

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt  # noqa: E402

# 한글 폰트 — 이걸 안 하면 DejaVu Sans에 한글 글리프가 없어서 네모(tofu)로 깨진다.
# unicode_minus는 같이 꺼야 마이너스 부호도 안 깨진다.
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

import numpy as np  # noqa: E402
import omni.kit.commands  # noqa: E402
import omni.usd  # noqa: E402
from isaacsim.asset.importer.urdf import _urdf  # noqa: E402
from isaacsim.core.api import World  # noqa: E402
from isaacsim.core.prims import SingleArticulation  # noqa: E402
from isaacsim.core.utils.extensions import (  # noqa: E402
    enable_extension,
    get_extension_path_from_name,
)
from isaacsim.core.utils.stage import add_reference_to_stage  # noqa: E402
from isaacsim.core.utils.types import ArticulationAction  # noqa: E402
from omni.kit.viewport.utility.camera_state import ViewportCameraState  # noqa: E402
from pxr import Gf, Usd, UsdGeom  # noqa: E402

PHYSICS_DT = 1.0 / 120.0


def resolve_ur10_urdf() -> str:
    enable_extension("isaacsim.asset.importer.urdf")
    ext_path = get_extension_path_from_name("isaacsim.asset.importer.urdf")
    urdf_path = Path(ext_path) / "data" / "urdf" / "robots" / "ur10" / "urdf" / "ur10.urdf"
    if not urdf_path.exists():
        raise FileNotFoundError(f"UR10 URDF를 찾지 못했다: {urdf_path}")
    return str(urdf_path)


def build_gain_asset(urdf_path: str, stiffness: float, damping: float, out_usd: Path) -> str:
    """URDF를 특정 게인으로 파싱해서 독립 USD 파일로 굽는다 (스테이지에 바로 넣지 않는다).

    게인 주입은 검증된 방식(p1_drive_tuning.py와 동일) 그대로 — URDF 파싱 직후
    UrdfRobot 객체의 drive.strength/damping에 값을 넣고 임포트한다. 임포트 후에
    USD DriveAPI 속성을 직접 건드리는 방식은 단위 변환이 importer 내부에서
    어떻게 되는지 보장이 없어 쓰지 않는다.
    """
    out_usd.parent.mkdir(parents=True, exist_ok=True)

    import_config = _urdf.ImportConfig()
    import_config.convex_decomp = False
    import_config.fix_base = True
    import_config.make_default_prim = True
    import_config.self_collision = False
    import_config.distance_scale = 1
    import_config.density = 0.0

    result, robot_model = omni.kit.commands.execute(
        "URDFParseFile", urdf_path=urdf_path, import_config=import_config,
    )
    if not result:
        raise RuntimeError(f"URDFParseFile 실패: {urdf_path}")

    for joint_name in robot_model.joints:
        robot_model.joints[joint_name].drive.strength = stiffness
        robot_model.joints[joint_name].drive.damping = damping

    result, _ = omni.kit.commands.execute(
        "URDFImportRobot", urdf_robot=robot_model, import_config=import_config,
        dest_path=str(out_usd),
    )
    if not result:
        raise RuntimeError(f"URDFImportRobot 실패 (dest_path={out_usd})")
    return str(out_usd)


def spawn_instance(usd_path: str, prim_path: str, y_offset: float) -> str:
    """구워둔 로봇 USD를 prim_path에 참조로 배치하고 Y축으로 옮긴다.

    ⚠️ XformCommonAPI().SetTranslate()는 여기서 쓰면 안 된다 — reference로
    가져온 xformOpOrder([translate, orient, scale], 참조 레이어에서 상속됨)를
    "공통 API와 호환 안 됨"으로 오판해서 *조용히* 실패한다("Could not determine
    xform ops for incompatible xformable" 경고만 찍고 아무 것도 안 옮긴다).
    그래서 두 로봇이 둘 다 원점에 겹친 채로 시작해 충돌한 적이 있다.
    이미 존재하는 translate op을 직접 찾아 값만 덮어쓰면 이 문제를 피한다.
    """
    prim = add_reference_to_stage(usd_path, prim_path)
    xformable = UsdGeom.Xformable(prim)
    translate_op = next(
        (op for op in xformable.GetOrderedXformOps()
         if op.GetOpType() == UsdGeom.XformOp.TypeTranslate),
        None,
    )
    if translate_op is None:
        translate_op = xformable.AddTranslateOp()
    translate_op.Set(Gf.Vec3d(0.0, y_offset, 0.0))
    return prim_path


def horizontal_pose(n_dof: int) -> np.ndarray:
    q = np.zeros(n_dof, dtype=np.float32)
    if n_dof >= 3:
        q[1] = -math.pi / 2.0
        q[2] = 0.0
    return q


class LiveScope:
    """Isaac Sim의 Gain Tuner 확장이 보여주는 것과 같은 "목표 vs 실제" 실시간 그래프.

    위 패널 — shoulder_lift 관절의 목표각(공통)과 두 로봇의 실제각.
    아래 패널 — 목표-실제 오차(=처짐/추종오차 지표)를 로봇별로 겹쳐서 직접 비교.
    """

    def __init__(self, stiffness_low, damping_low, stiffness_high, damping_high):
        plt.ion()
        self.fig, (self.ax_pos, self.ax_err) = plt.subplots(2, 1, figsize=(10, 7.5), sharex=True)
        self.fig.suptitle("UR10 gain 비교 — shoulder_lift 관절 (수평 자세 + 사인 궤적)")

        self.t, self.tgt, self.act_lo, self.act_hi = [], [], [], []
        self.err_lo, self.err_hi = [], []

        # k=stiffness, d=damping을 범례에 같이 박는다 — "게인"이라고만 하면
        # stiffness인지 damping인지 안 보여서 헷갈린다는 피드백을 반영했다.
        label_lo = f"저게인 (stiffness={stiffness_low:g}, damping={damping_low:g})"
        label_hi = f"고게인 (stiffness={stiffness_high:g}, damping={damping_high:g})"

        # 동적 추종오차는 원래 게인에 거의 반응하지 않는다 (freq_scan 실험에서
        # 이미 확인된 사실 — 지연이 지배적이라서다). 그래서 두 선이 거의 겹쳐
        # 뒤에 그려진 색이 앞 선을 완전히 덮어버린다. 겹쳐도 둘 다 보이도록
        # 하나는 굵은 반투명 실선, 하나는 얇은 점선으로 스타일을 분리한다.
        (self.l_tgt,) = self.ax_pos.plot([], [], color="0.5", linestyle="--", linewidth=1.5,
                                          label="목표 (공통)")
        (self.l_lo,) = self.ax_pos.plot([], [], color="#E8735C", linewidth=2.0, label=label_lo)
        (self.l_hi,) = self.ax_pos.plot([], [], color="#3B82C4", linewidth=2.0, label=label_hi)
        self.ax_pos.set_ylabel("shoulder_lift (°)")
        self.ax_pos.legend(loc="upper right", fontsize=9)
        self.ax_pos.grid(True, linewidth=0.5, alpha=0.5)

        (self.l_err_lo,) = self.ax_err.plot([], [], color="#E8735C", linewidth=2.0,
                                             label="저게인 오차 |목표-실제|")
        (self.l_err_hi,) = self.ax_err.plot([], [], color="#3B82C4", linewidth=2.0,
                                             label="고게인 오차 |목표-실제|")
        self.ax_err.set_ylabel("오차 (°)")
        self.ax_err.set_xlabel("시간 (s)")
        self.ax_err.legend(loc="upper right", fontsize=9)
        self.ax_err.grid(True, linewidth=0.5, alpha=0.5)

        self.fig.tight_layout()
        self.fig.canvas.draw()
        plt.pause(0.01)

    def push(self, t, tgt_deg, act_lo_deg, act_hi_deg):
        self.t.append(t)
        self.tgt.append(tgt_deg)
        self.act_lo.append(act_lo_deg)
        self.act_hi.append(act_hi_deg)
        self.err_lo.append(abs(tgt_deg - act_lo_deg))
        self.err_hi.append(abs(tgt_deg - act_hi_deg))

    def redraw(self):
        self.l_tgt.set_data(self.t, self.tgt)
        self.l_lo.set_data(self.t, self.act_lo)
        self.l_hi.set_data(self.t, self.act_hi)
        self.l_err_lo.set_data(self.t, self.err_lo)
        self.l_err_hi.set_data(self.t, self.err_hi)
        for ax in (self.ax_pos, self.ax_err):
            ax.relim()
            ax.autoscale_view()
        self.fig.canvas.draw_idle()
        plt.pause(0.001)


def main():
    world = World(physics_dt=PHYSICS_DT, rendering_dt=PHYSICS_DT, stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    urdf_path = resolve_ur10_urdf()
    asset_dir = Path(args.asset_dir)
    usd_lo = build_gain_asset(urdf_path, args.stiffness_low, args.damping_low,
                               asset_dir / "ur10_low.usd")
    usd_hi = build_gain_asset(urdf_path, args.stiffness_high, args.damping_high,
                               asset_dir / "ur10_high.usd")

    half = args.separation / 2.0
    path_lo = spawn_instance(usd_lo, "/World/ur10_low", -half)
    path_hi = spawn_instance(usd_hi, "/World/ur10_high", +half)

    # translate가 실제로 먹었는지 바로 검증한다 — 예전에 XformCommonAPI가
    # "incompatible xformable" 경고만 찍고 조용히 실패해서 두 로봇이 원점에
    # 겹친 채로 시작한 적이 있다. 다시 그러면 여기서 바로 걸린다.
    stage = omni.usd.get_context().get_stage()
    for path, expected_y in ((path_lo, -half), (path_hi, +half)):
        world_pos = UsdGeom.Xformable(stage.GetPrimAtPath(path)).ComputeLocalToWorldTransform(
            Usd.TimeCode.Default()).ExtractTranslation()
        if abs(world_pos[1] - expected_y) > 1e-3:
            raise RuntimeError(
                f"{path} 배치 실패 — 기대 Y={expected_y}, 실제 Y={world_pos[1]:.4f}. "
                "translate op이 안 먹은 것 같다 (xformOpOrder 확인할 것)."
            )
        print(f"[gui-compare] {path} world pos = {tuple(world_pos)} (검증 통과)")

    art_lo = SingleArticulation(prim_path=path_lo, name="ur10_low")
    art_hi = SingleArticulation(prim_path=path_hi, name="ur10_high")
    world.scene.add(art_lo)
    world.scene.add(art_hi)
    world.reset()

    # separation이 커진 만큼 두 로봇이 한 프레임에 다 들어오게 카메라도 물러난다
    cam_dist = max(3.6, args.separation * 0.85)
    camera_state = ViewportCameraState("/OmniverseKit_Persp")
    camera_state.set_position_world(Gf.Vec3d(cam_dist, 0.0, cam_dist * 0.55), True)
    camera_state.set_target_world(Gf.Vec3d(0.0, 0.0, 0.4), True)

    n_dof = art_lo.num_dof
    q_cmd = horizontal_pose(n_dof)
    art_lo.set_joint_positions(q_cmd)
    art_hi.set_joint_positions(q_cmd)
    art_lo.set_joint_velocities(np.zeros(n_dof, dtype=np.float32))
    art_hi.set_joint_velocities(np.zeros(n_dof, dtype=np.float32))

    scope = LiveScope(args.stiffness_low, args.damping_low,
                       args.stiffness_high, args.damping_high)

    amp = math.radians(15.0)
    total_settle = args.settle_steps
    total_track = args.track_steps
    rows = []

    def step_and_record(q_t, i, phase):
        art_lo.apply_action(ArticulationAction(joint_positions=q_t))
        art_hi.apply_action(ArticulationAction(joint_positions=q_t))
        world.step(render=True)

        t = i * PHYSICS_DT
        tgt_deg = math.degrees(float(q_t[1]))
        act_lo_deg = math.degrees(float(art_lo.get_joint_positions()[1]))
        act_hi_deg = math.degrees(float(art_hi.get_joint_positions()[1]))
        scope.push(t, tgt_deg, act_lo_deg, act_hi_deg)
        rows.append({
            "t": round(t, 4), "phase": phase,
            "target_deg": round(tgt_deg, 4),
            "actual_low_deg": round(act_lo_deg, 4),
            "actual_high_deg": round(act_hi_deg, 4),
            "err_low_deg": round(abs(tgt_deg - act_lo_deg), 4),
            "err_high_deg": round(abs(tgt_deg - act_hi_deg), 4),
        })
        if i % args.plot_every == 0:
            scope.redraw()

    print(f"[gui-compare] T1 정적 처짐 — {total_settle} 스텝 정상상태 대기 중...")
    for i in range(total_settle):
        step_and_record(q_cmd, i, "settle")

    print(f"[gui-compare] T2 궤적 추종 — {total_track} 스텝, freq={args.freq}Hz")
    for k in range(total_settle, total_settle + total_track):
        i = k - total_settle
        t_local = i * PHYSICS_DT
        s = amp * math.sin(2.0 * math.pi * args.freq * t_local)
        q_t = q_cmd.copy()
        q_t[1] += s
        if n_dof >= 3:
            q_t[2] += s
        step_and_record(q_t, k, "track")

    # 요약 통계 — track_settle_steps 이후 구간만 (초기 과도응답 제외)
    track_rows = [r for r in rows if r["phase"] == "track"][args.track_settle_steps:]
    err_lo_rms = float(np.sqrt(np.mean([r["err_low_deg"] ** 2 for r in track_rows])))
    err_hi_rms = float(np.sqrt(np.mean([r["err_high_deg"] ** 2 for r in track_rows])))
    settle_rows = [r for r in rows if r["phase"] == "settle"]
    sag_lo = settle_rows[-1]["err_low_deg"]
    sag_hi = settle_rows[-1]["err_high_deg"]

    print(f"\n[gui-compare] 정적 처짐(sag)   저게인 {sag_lo:.4f}°  vs  고게인 {sag_hi:.4f}°")
    print(f"[gui-compare] 동적 RMS 오차    저게인 {err_lo_rms:.4f}°  vs  고게인 {err_hi_rms:.4f}°")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"[gui-compare] wrote {out} ({len(rows)} rows)")

    print("[gui-compare] 그래프 창을 닫으면 시뮬레이션도 함께 종료된다.")
    plt.ioff()
    plt.show()


if __name__ == "__main__":
    import sys
    import traceback

    try:
        main()
    except Exception:
        traceback.print_exc(file=sys.stdout)
        sys.stdout.flush()
    finally:
        sys.stdout.flush()
        simulation_app.close()
