"""USD 스테이지의 컴포지션 구조를 읽는다.

GPU도 Isaac Sim도 필요 없다. usd-core(pxr)만 있으면 된다.

    D:\\ic\\usdenv\\Scripts\\python.exe scripts/p2_inspect_stage.py <스테이지.usd>

무엇을 보여주나
  - 스테이지 메타데이터 (upAxis / metersPerUnit)  ← 단위 사고의 진원지
  - 서브레이어 스택 (강도 순서 그대로)
  - 프림별 컴포지션 아크 (reference / payload / inherit / variant / specialize)
  - 인스턴싱 상태와 프로토타입 수
  - 커스텀 속성 (스키마에 없는, 사람이 붙인 속성)

왜 만들었나
  씬이 커지면 "이 값이 어디서 왔나"를 눈으로 못 쫓는다. 컴포지션은 파일을 나눠서
  얻는 이득만큼 추적을 어렵게 만든다. 그 추적을 자동화하는 게 이 스크립트다.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

from pxr import Pcp, Sdf, Usd, UsdGeom


def _rule(title: str) -> None:
    print(f"\n{'=' * 72}\n{title}\n{'=' * 72}")


def show_metadata(stage: Usd.Stage) -> dict:
    """단위와 상방 축. 에러 없이 조용히 틀리는 유일한 항목이라 제일 먼저 본다."""
    _rule("1. 스테이지 메타데이터")

    up = UsdGeom.GetStageUpAxis(stage)
    mpu = UsdGeom.GetStageMetersPerUnit(stage)
    unit_name = {1.0: "미터", 0.01: "센티미터", 0.001: "밀리미터"}.get(mpu, "비표준")

    print(f"  upAxis          : {up}")
    print(f"  metersPerUnit   : {mpu}  ({unit_name})")

    default_prim = stage.GetDefaultPrim()
    print(f"  defaultPrim     : {default_prim.GetPath() if default_prim else '없음 ← 참조할 때 경로를 매번 적어야 한다'}")

    return {"upAxis": str(up), "metersPerUnit": mpu}


def show_layer_stack(stage: Usd.Stage) -> None:
    """서브레이어는 LIVRPS의 L에 해당한다. 앞에 나열된 것이 이긴다."""
    _rule("2. 레이어 스택 (위가 강하다)")

    for i, layer in enumerate(stage.GetLayerStack()):
        ident = layer.identifier
        # 익명 레이어(세션 레이어 등)는 경로가 아니라 메모리 주소를 갖는다
        label = ident if not layer.anonymous else f"<익명: {ident}>"
        muted = " [MUTED]" if stage.IsLayerMuted(ident) else ""
        print(f"  [{i}] {label}{muted}")

    root = stage.GetRootLayer()
    if root.subLayerPaths:
        print(f"\n  루트의 subLayers ({len(root.subLayerPaths)}개):")
        for p in root.subLayerPaths:
            print(f"    - {p}")


def _arc_name(arc: Usd.CompositionArc) -> str:
    """Pcp.ArcType 을 사람이 읽을 이름으로. 버전에 따라 displayName 유무가 달라 방어한다."""
    t = arc.GetArcType()
    return str(getattr(t, "displayName", t)).replace("PcpArcType", "")


def _arc_target(arc: Usd.CompositionArc) -> str:
    """아크가 가리키는 레이어 파일명."""
    layer = None
    getter = getattr(arc, "GetTargetLayer", None)
    if getter is not None:
        layer = getter()
    if layer is None:
        node = arc.GetTargetNode()
        layer = node.layerStack.identifier.rootLayer if node else None
    return Path(layer.identifier).name if layer else "?"


def show_composition(stage: Usd.Stage, max_prims: int) -> Counter:
    """프림마다 어떤 아크로 무엇을 끌어왔는지."""
    _rule("3. 컴포지션 아크")

    arc_counts: Counter = Counter()
    shown = 0

    for prim in stage.TraverseAll():
        query = Usd.PrimCompositionQuery(prim)
        # 루트 아크(프림 자신이 정의된 자리)는 "끌어온 것"이 아니므로 뺀다
        arcs = [a for a in query.GetCompositionArcs()
                if a.GetArcType() != Pcp.ArcTypeRoot]
        if not arcs:
            continue

        for arc in arcs:
            arc_counts[_arc_name(arc)] += 1

        if shown < max_prims:
            shown += 1
            inst = " [instanceable]" if prim.IsInstanceable() else ""
            print(f"\n  {prim.GetPath()}{inst}")
            print(f"    type={prim.GetTypeName() or '-'}  kind={Usd.ModelAPI(prim).GetKind() or '-'}")
            for arc in arcs:
                print(f"    <- {_arc_name(arc):<12} {_arc_target(arc)}")

    if shown >= max_prims:
        print(f"\n  ... (--max-prims {max_prims} 로 잘림)")

    print("\n  아크 종류별 총계:")
    for kind, n in arc_counts.most_common():
        print(f"    {kind:<14} {n}")

    return arc_counts


def show_instancing(stage: Usd.Stage) -> None:
    """참조는 디스크를, 인스턴싱은 GPU를 아낀다. 아끼는 자원이 다르다."""
    _rule("4. 인스턴싱")

    protos = stage.GetPrototypes()
    instanceable = [p for p in stage.TraverseAll() if p.IsInstanceable()]

    print(f"  instanceable 프림 : {len(instanceable)}")
    print(f"  프로토타입        : {len(protos)}")

    if protos:
        print("\n  프로토타입별 인스턴스 수:")
        for proto in protos:
            getter = getattr(proto, "GetInstances", None)
            n = len(getter()) if getter is not None else "?"
            print(f"    {proto.GetPath()}  <- {n}개")
    elif instanceable:
        print("  (instanceable 은 켜져 있는데 프로토타입이 없다 — 참조·페이로드가 안 붙은 프림이다)")
    else:
        print("  인스턴싱을 쓰지 않는다. 같은 에셋이 반복되면 VRAM에서 그 배수로 든다.")


# DCC 툴이 남긴 잔재. 사람이 의미를 담아 붙인 속성이 아니라 노이즈다.
DCC_JUNK = ("smoothgroups3DSMax", "3dsmax", "MaxHandle", "blenderData")


def _brief(value, width: int = 70) -> str:
    """긴 배열이 출력을 덮지 않게 자른다. 배열은 길이만 보여준다."""
    if value is None:
        return "None"
    n = getattr(value, "__len__", None)
    if n is not None and not isinstance(value, str) and len(value) > 6:
        head = ", ".join(repr(v) for v in list(value)[:3])
        return f"<{len(value)}개> [{head}, ...]"
    s = repr(value)
    return s if len(s) <= width else s[:width] + "..."


def show_custom_attrs(stage: Usd.Stage, limit: int, keep_junk: bool = False) -> Counter:
    """USD 스키마에 없는, 사람이 이 프로젝트를 위해 붙인 속성.

    코스의 'Custom Attributes' 모듈이 만드는 것이 여기 잡힌다
    (ProductID, Capacity_UnitsPerHour 같은 공정 메타데이터).
    """
    _rule("5. 커스텀 속성")

    names: Counter = Counter()
    shown = 0

    for prim in stage.TraverseAll():
        customs = [a for a in prim.GetAttributes() if a.IsCustom()]
        if not keep_junk:
            customs = [a for a in customs
                       if not any(j.lower() in a.GetName().lower() for j in DCC_JUNK)]
        if not customs:
            continue

        for attr in customs:
            names[attr.GetName()] += 1

        if shown < limit:
            shown += 1
            print(f"\n  {prim.GetPath()}")
            for attr in customs:
                print(f"    {attr.GetName():<28} = {_brief(attr.Get())}  ({attr.GetTypeName()})")

    if shown >= limit:
        print(f"\n  ... (--max-custom {limit} 로 잘림)")

    if not names:
        print("  없다." if keep_junk else "  없다 (DCC 잔재는 제외했다. --keep-junk 로 포함).")
    else:
        print("\n  속성 이름별 개수:")
        for name, n in names.most_common(20):
            print(f"    {name:<32} {n}")

    return names


def main() -> int:
    ap = argparse.ArgumentParser(description="USD 컴포지션 구조 조회")
    ap.add_argument("stage", help="열 스테이지 (.usd / .usda / .usdc)")
    ap.add_argument("--max-prims", type=int, default=15, help="아크를 출력할 프림 수 상한")
    ap.add_argument("--max-custom", type=int, default=10, help="커스텀 속성을 출력할 프림 수 상한")
    ap.add_argument("--unloaded", action="store_true",
                    help="페이로드를 로드하지 않고 연다 (payload가 무엇을 감추고 있는지 비교용)")
    ap.add_argument("--keep-junk", action="store_true",
                    help="DCC 잔재(smoothgroups3DSMax 등)도 커스텀 속성에 포함")
    args = ap.parse_args()

    path = Path(args.stage)
    if not path.exists():
        print(f"파일이 없다: {path}", file=sys.stderr)
        return 1

    mask = Usd.Stage.LoadNone if args.unloaded else Usd.Stage.LoadAll
    stage = Usd.Stage.Open(str(path), load=mask)
    if not stage:
        print(f"열지 못했다: {path}", file=sys.stderr)
        return 1

    print(f"스테이지 : {path}")
    print(f"로드 정책: {'LoadNone (페이로드 안 펼침)' if args.unloaded else 'LoadAll'}")

    show_metadata(stage)
    show_layer_stack(stage)
    show_composition(stage, args.max_prims)
    show_instancing(stage)
    show_custom_attrs(stage, args.max_custom, keep_junk=args.keep_junk)

    _rule("요약")
    all_prims = list(stage.TraverseAll())
    print(f"  프림 총계 : {len(all_prims)}")
    print(f"  로드된 페이로드 : {len(stage.GetLoadSet())}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
