"""Isaac Sim 5.1 설치 검증 — headless로 앱을 띄우고 최소 씬을 한 번 굴려본다.

첫 실행은 셰이더 컴파일 때문에 수 분 걸릴 수 있다. 멈춘 게 아니다.
"""

from isaacsim import SimulationApp

simulation_app = SimulationApp({"headless": True})

import numpy as np  # noqa: E402
from isaacsim.core.api import World  # noqa: E402
from isaacsim.core.api.objects import DynamicCuboid  # noqa: E402

world = World(stage_units_in_meters=1.0)
world.scene.add_default_ground_plane()

cube = world.scene.add(
    DynamicCuboid(
        prim_path="/World/cube",
        name="cube",
        position=np.array([0.0, 0.0, 1.0]),
        scale=np.array([0.2, 0.2, 0.2]),
    )
)

world.reset()

z0 = float(cube.get_world_pose()[0][2])
for _ in range(120):
    world.step(render=False)
z1 = float(cube.get_world_pose()[0][2])

print(f"[smoke] cube z: {z0:.4f} -> {z1:.4f}  (dropped {z0 - z1:.4f} m)")
print("[smoke] PhysX stepping OK" if z1 < z0 else "[smoke] WARNING: cube did not fall")

simulation_app.close()
print("[smoke] DONE")
