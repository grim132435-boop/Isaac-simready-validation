"""P1 — Isaac Sim GUI 화면을 실제로 캡처해서 발표덱 시각자료를 만든다.

지시서 원안은 헤드리스 Replicator 렌더였지만, GUI에서 직접 눈으로 확인한 화면을
그대로 캡처하는 방식으로 바꿨다 (사용자 요청). 뷰포트 캡처 API는
`omni.kit.viewport.utility.capture_viewport_to_file()` — future 비슷한 걸 돌려주고
`await capture_helper.wait_for_result()` 로 완료를 기다려야 한다.

p1_gui_compare.py 에서 검증된 build_gain_asset/spawn_instance 를 그대로 재사용한다
(참조 방식 배치 — MovePrim/XformCommonAPI를 쓰면 안 되는 이유는 그 파일 주석 참고).

사용법
------
    python scripts/p1_gui_capture.py --mode sag        # sim_gravity_sag.png
    python scripts/p1_gui_capture.py --mode collider    # sim_collider_view.png
"""

import argparse
import math
import shutil
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
parser.add_argument("--mode", choices=["sag", "collider"], required=True)
parser.add_argument("--out-dir", type=str,
                    default=r"C:\Users\Administrator\Desktop\n2p\10_Career\11_companies"
                            r"\엔닷라이트\30_interview\assets")
parser.add_argument("--asset-dir", type=str, default=r"D:\ic\tmp\gui_capture")
parser.add_argument("--stiffness-low", type=float, default=1000.0)
parser.add_argument("--damping-low", type=float, default=50.0)
parser.add_argument("--stiffness-high", type=float, default=1.0e5)
parser.add_argument("--damping-high", type=float, default=5.0e3)
parser.add_argument("--separation", type=float, default=2.0,
                    help="dual-compare GUI에서 봤던 4.0m의 절반 — 사용자 요청으로 좁힘. "
                         "이 스크립트는 정적 처짐만 보고(사인 궤적 없음) 관절이 더 안 움직이니 "
                         "p1_gui_compare.py의 2m 크래시(그건 사실 별개의 matplotlib 버그였다)와는 "
                         "무관하게 안전할 가능성이 높다 — 그래도 첫 실행에서 화면으로 확인할 것")
parser.add_argument("--settle-steps", type=int, default=240)
parser.add_argument("--payload-low", type=float, default=0.0,
                    help="저게인 로봇 엔드이펙터에 추가할 payload [kg]. 순수 게인만으로는 "
                         "실제 처짐이 0.05° 수준이라 렌더에서 육안으로 안 보인다 — 무빙실러 "
                         "사례(payload 미반영 gain)처럼 payload를 실어야 처짐이 시각적으로 보인다")
args = parser.parse_args()

from isaacsim import SimulationApp  # noqa: E402

simulation_app = SimulationApp({"headless": False})

import carb.settings  # noqa: E402
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
from omni.kit.viewport.utility import capture_viewport_to_file, get_active_viewport  # noqa: E402
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
    """검증된 방식 그대로 (p1_gui_compare.py와 동일) — URDF를 특정 게인으로 구워
    독립 USD 파일로 저장한다. 스테이지에 바로 넣지 않는다."""
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
    """⚠️ XformCommonAPI().SetTranslate()는 쓰지 않는다 — reference로 가져온
    xformOpOrder를 "호환 안 됨"으로 오판해 조용히 실패한다. 기존 translate op을
    직접 찾아 값만 덮어쓴다 (p1_gui_compare.py에서 검증된 방식)."""
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


EE_LINK = "wrist_3_link"


def add_payload(prim_path: str, extra_kg: float) -> float:
    """말단 링크에 payload 질량을 더한다 (p1_drive_tuning.py와 동일한 방식).

    무빙실러 사례의 재현 지점 — 엔드이펙터 무게가 gain에 반영 안 되면
    중력 처짐이 생긴다. 반환값은 적용 후 질량.
    """
    stage = omni.usd.get_context().get_stage()
    link = stage.GetPrimAtPath(f"{prim_path}/{EE_LINK}")
    if not link or not link.IsValid():
        raise RuntimeError(f"말단 링크를 찾지 못했다: {prim_path}/{EE_LINK}")

    from pxr import UsdPhysics

    mass_api = (
        UsdPhysics.MassAPI(link)
        if link.HasAPI(UsdPhysics.MassAPI)
        else UsdPhysics.MassAPI.Apply(link)
    )
    attr = mass_api.GetMassAttr()
    base = attr.Get() if attr and attr.Get() else 0.0
    attr.Set(float(base) + extra_kg)
    return float(base) + extra_kg


def horizontal_pose(n_dof: int) -> np.ndarray:
    q = np.zeros(n_dof, dtype=np.float32)
    if n_dof >= 3:
        q[1] = -math.pi / 2.0
        q[2] = 0.0
    return q


def capture(viewport, path: Path):
    """뷰포트를 지금 상태 그대로 PNG로 저장하고 완료를 기다린다.

    ⚠️ asyncio.run(capture_helper.wait_for_result())은 쓰면 안 된다 — Kit이
    이미 자기 asyncio 루프를 돌리고 있는데 asyncio.run()이 별개의 새 루프를
    만들어서 "Future attached to a different loop" 에러가 난다. Kit 루프를
    simulation_app.update()로 계속 펌핑하면서 파일이 실제로 생길 때까지
    폴링하는 쪽이 표준 스탠드얼론 스크립트 패턴과 맞다.

    ⚠️ 최종 경로에 한글(엔닷라이트)이 들어가면 네이티브 저장 플러그인
    (omni.renderercapture.plugin)이 "Reason: ." 이라는 빈 이유만 남기고
    조용히 실패한다 — 아마 내부에서 좁은(ANSI) 문자열로 경로를 다루는 듯하다.
    ASCII 전용 임시 경로에 먼저 저장하고 Python(유니코드 경로 문제 없음)으로
    최종 목적지에 복사하는 식으로 우회한다.
    """
    tmp_path = Path(args.asset_dir) / f"_capture_tmp_{path.stem}.png"
    tmp_path.parent.mkdir(parents=True, exist_ok=True)
    if tmp_path.exists():
        tmp_path.unlink()
    capture_viewport_to_file(viewport, file_path=str(tmp_path))

    for _ in range(300):  # 최대 ~수 초, 캡처가 이보다 오래 걸리면 뭔가 잘못된 것
        simulation_app.update()
        if tmp_path.exists():
            break
    else:
        raise TimeoutError(f"캡처가 끝나지 않았다: {tmp_path}")

    path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(tmp_path, path)
    print(f"[capture] wrote {path}")


# --------------------------------------------------------------------------
def run_sag(out_dir: Path, asset_dir: Path):
    """sim_gravity_sag.png — 저게인 vs 고게인 UR10을 나란히 세우고 처진 최종
    자세를 GUI 뷰포트에서 그대로 캡처한다."""
    world = World(physics_dt=PHYSICS_DT, rendering_dt=PHYSICS_DT, stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    urdf_path = resolve_ur10_urdf()
    usd_lo = build_gain_asset(urdf_path, args.stiffness_low, args.damping_low,
                               asset_dir / "ur10_low.usd")
    usd_hi = build_gain_asset(urdf_path, args.stiffness_high, args.damping_high,
                               asset_dir / "ur10_high.usd")

    half = args.separation / 2.0
    path_lo = spawn_instance(usd_lo, "/World/ur10_low", -half)
    path_hi = spawn_instance(usd_hi, "/World/ur10_high", +half)

    if args.payload_low > 0.0:
        total = add_payload(path_lo, args.payload_low)
        print(f"[capture] 저게인 로봇 payload +{args.payload_low}kg -> {EE_LINK} = {total:.2f}kg")

    art_lo = SingleArticulation(prim_path=path_lo, name="ur10_low")
    art_hi = SingleArticulation(prim_path=path_hi, name="ur10_high")
    world.scene.add(art_lo)
    world.scene.add(art_hi)
    world.reset()

    n_dof = art_lo.num_dof
    q_cmd = horizontal_pose(n_dof)
    art_lo.set_joint_positions(q_cmd)
    art_hi.set_joint_positions(q_cmd)
    art_lo.set_joint_velocities(np.zeros(n_dof, dtype=np.float32))
    art_hi.set_joint_velocities(np.zeros(n_dof, dtype=np.float32))

    print(f"[capture] settling {args.settle_steps} steps...")
    for _ in range(args.settle_steps):
        art_lo.apply_action(ArticulationAction(joint_positions=q_cmd))
        art_hi.apply_action(ArticulationAction(joint_positions=q_cmd))
        world.step(render=True)

    q_lo = np.degrees(np.asarray(art_lo.get_joint_positions(), dtype=np.float64))
    q_hi = np.degrees(np.asarray(art_hi.get_joint_positions(), dtype=np.float64))
    q_tgt = np.degrees(q_cmd.astype(np.float64))
    print(f"[capture] 저게인 전체 관절(deg): {np.round(q_lo, 3).tolist()}")
    print(f"[capture] 고게인 전체 관절(deg): {np.round(q_hi, 3).tolist()}")
    print(f"[capture] 목표      전체 관절(deg): {np.round(q_tgt, 3).tolist()}")
    sag_lo = float(np.abs(q_lo - q_tgt).max())
    sag_hi = float(np.abs(q_hi - q_tgt).max())
    print(f"[capture] 최종 sag(전체 관절 중 최대) — 저게인 {sag_lo:.4f}°  고게인 {sag_hi:.4f}°")

    # 해상도를 먼저 바꾸고 카메라를 그 다음에 잡는다 — 순서를 반대로 하면
    # 카메라가 이전 종횡비 기준으로 셋업돼서 해상도를 바꾼 뒤 프레임이
    # 한쪽으로 쏠린다 (실제로 겪음: 로봇이 화면 왼쪽 아래 구석에 몰렸었다).
    viewport = get_active_viewport()
    viewport.resolution = (1920, 1080)
    for _ in range(5):
        world.step(render=True)

    camera_state = ViewportCameraState("/OmniverseKit_Persp")
    camera_state.set_position_world(Gf.Vec3d(3.3, 0.0, 1.5), True)
    camera_state.set_target_world(Gf.Vec3d(0.0, 0.0, 0.65), True)
    for _ in range(10):  # 카메라 변경이 렌더에 반영될 시간을 준다
        world.step(render=True)

    out_path = out_dir / "sim_gravity_sag.png"
    capture(viewport, out_path)
    annotate_sag(out_path, sag_lo, sag_hi, args.stiffness_low, args.stiffness_high,
                 args.payload_low)


def annotate_sag(path: Path, sag_lo: float, sag_hi: float,
                  stiffness_low: float, stiffness_high: float, payload_low: float):
    """처짐 각도를 숫자로 오버레이한다.

    1.9° 같은 값은 이 카메라 거리에서 픽셀로는 사실상 안 보인다 (실제로 렌더링해서
    확인함 — 육안 구분 불가). 그림만으로 안 보이는 차이는 숫자로 보여줘야 한다.
    "(시뮬 기준)" 표기는 지시서 규칙 3 — 실기 검증 안 한 값을 실측처럼 보이지 않게.
    """
    from PIL import Image, ImageDraw, ImageFont

    img = Image.open(path).convert("RGB")
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("malgun.ttf", 34)
        font_small = ImageFont.truetype("malgun.ttf", 22)
    except OSError:
        font_big = font_small = ImageFont.load_default()

    w, h = img.size
    amber = (255, 176, 32)
    muted = (154, 170, 187)

    label_lo = f"sag {sag_lo:.2f}°"
    sub_lo = (f"stiffness={stiffness_low:g}, payload+{payload_low:g}kg (시뮬 기준)"
              if payload_low > 0 else f"stiffness={stiffness_low:g} (시뮬 기준)")
    label_hi = f"sag {sag_hi:.3f}°"
    sub_hi = f"stiffness={stiffness_high:g} (시뮬 기준)"

    draw.text((w * 0.22, h * 0.86), label_lo, font=font_big, fill=amber, anchor="mm")
    draw.text((w * 0.22, h * 0.91), sub_lo, font=font_small, fill=muted, anchor="mm")
    draw.text((w * 0.78, h * 0.86), label_hi, font=font_big, fill=amber, anchor="mm")
    draw.text((w * 0.78, h * 0.91), sub_hi, font=font_small, fill=muted, anchor="mm")

    img.save(path)
    print(f"[capture] 주석 추가 완료 -> {path}")


# --------------------------------------------------------------------------
def run_collider(out_dir: Path, asset_dir: Path):
    """sim_collider_view.png — 같은 로봇의 시각 메시 / 충돌 메시를 각각 캡처해
    좌우로 합친다. 고게인으로 세팅해 자세가 안정적으로 보이게 한다."""
    world = World(physics_dt=PHYSICS_DT, rendering_dt=PHYSICS_DT, stage_units_in_meters=1.0)
    world.scene.add_default_ground_plane()

    urdf_path = resolve_ur10_urdf()
    usd_path = build_gain_asset(urdf_path, args.stiffness_high, args.damping_high,
                                 asset_dir / "ur10_collider_demo.usd")
    prim_path = spawn_instance(usd_path, "/World/ur10", 0.0)

    art = SingleArticulation(prim_path=prim_path, name="ur10")
    world.scene.add(art)
    world.reset()

    n_dof = art.num_dof
    q_cmd = horizontal_pose(n_dof)
    art.set_joint_positions(q_cmd)
    art.set_joint_velocities(np.zeros(n_dof, dtype=np.float32))

    for _ in range(120):
        art.apply_action(ArticulationAction(joint_positions=q_cmd))
        world.step(render=True)

    # 해상도를 먼저, 카메라를 그 다음에 (run_sag와 같은 순서 버그 방지)
    viewport = get_active_viewport()
    viewport.resolution = (960, 1080)  # 나중에 좌우로 합칠 거라 절반 폭
    for _ in range(5):
        world.step(render=True)

    camera_state = ViewportCameraState("/OmniverseKit_Persp")
    camera_state.set_position_world(Gf.Vec3d(1.8, -1.8, 1.3), True)
    camera_state.set_target_world(Gf.Vec3d(0.3, 0.0, 0.3), True)
    for _ in range(10):
        world.step(render=True)

    # ⚠️ USD 프림의 visibility/purpose를 직접 건드려 충돌 메시만 보이게 하는
    # 시도는 실패했다 — 프림은 스테이지에 있는데("/collisions/mesh_0/..."
    # 존재 확인함) 렌더 결과가 텅 비었다. 원인을 더 파기보다, Isaac Sim이
    # 원래 제공하는 PhysX 콜라이더 시각화(디버그 와이어프레임 오버레이)를
    # 쓰는 쪽이 훨씬 표준적이고 확실하다 — 시각 메시 위에 충돌 형상을
    # 하이라이트로 겹쳐 그린다.
    # 콜라이더 디버그 와이어프레임을 실제로 그리는 코드는 omni.physx.ui에 있다
    # (기본 experience.kit에는 로드 안 돼 있음) — 켜야 시각화 설정이 반영된다.
    enable_extension("omni.physx.ui")
    for _ in range(5):
        world.step(render=True)

    settings = carb.settings.get_settings()
    DISPLAY_COLLIDERS = "/persistent/physics/visualizationDisplayColliders"
    DISPLAY_JOINTS = "/persistent/physics/visualizationDisplayJoints"
    NONE, ALL = 0, 2

    # omni.physx.ui를 켜면 조인트 기즈모(자홍색 동심원)도 기본으로 같이 켜진다 —
    # 콜라이더만 보여줄 거라 명시적으로 꺼둔다.
    settings.set(DISPLAY_JOINTS, NONE)

    print("[capture] 시각 메시 캡처...")
    settings.set(DISPLAY_COLLIDERS, NONE)
    for _ in range(10):
        world.step(render=True)
    p_visual = asset_dir / "_collider_view_visual_half.png"
    capture(viewport, p_visual)

    print("[capture] 충돌 형상 오버레이 캡처...")
    settings.set(DISPLAY_COLLIDERS, ALL)
    for _ in range(10):
        world.step(render=True)
    p_collision = asset_dir / "_collider_view_collision_half.png"
    capture(viewport, p_collision)
    settings.set(DISPLAY_COLLIDERS, NONE)

    from PIL import Image

    left = Image.open(p_visual)
    right = Image.open(p_collision)
    combined = Image.new("RGB", (1920, 1080))
    combined.paste(left, (0, 0))
    combined.paste(right, (960, 0))
    out_path = out_dir / "sim_collider_view.png"
    combined.save(out_path)
    print(f"[capture] wrote {out_path}")


def main():
    out_dir = Path(args.out_dir)
    asset_dir = Path(args.asset_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    asset_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "sag":
        run_sag(out_dir, asset_dir)
    else:
        run_collider(out_dir, asset_dir)


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
