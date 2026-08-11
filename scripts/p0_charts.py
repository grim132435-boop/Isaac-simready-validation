"""P0 — 기존 CSV 3종으로 발표덱용 시각자료 3장을 생성한다.

Isaac Sim을 띄우지 않는다. results/ 에 이미 있는 실측 원자료를 그리기만 한다.
지시서: 10_Career/11_companies/엔닷라이트/30_interview/_시각자료_추출_지시서.md

산출
----
    chart_gain_sweep.png  — p1_sweep.csv    : 게인이 닫는 몫 (정적 처짐)
    chart_freq_scan.png   — p1_freqscan.csv : 지연으로만 설명되는 몫 (동적 오차)
    chart_payload.png     — p1_payload.csv  : payload가 정적/동적에 비대칭으로 영향

값(퍼센트, 배율, τ)은 전부 CSV에서 계산한다. 하드코딩하지 않는다 — CSV가
바뀌면 그림도 같이 바뀌어야 재현 가능한 스크립트다.

사용법
------
    python scripts/p0_charts.py
    python scripts/p0_charts.py --out-dir <다른 경로>
"""

import argparse
import csv
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402

# 마이너스 기호 깨짐 방지는 폰트 설정과 반드시 같이 가야 한다 (지시서 참고)
plt.rcParams["font.family"] = "Malgun Gothic"
plt.rcParams["axes.unicode_minus"] = False

# --------------------------------------------------------------------------
# 팔레트 — 덱(_build_deck.py)과 동일한 값. 슬라이드 배경(#0F1720)에 얹었을 때
# 이물감이 없어야 하므로 여기서 갈라지면 안 된다.
# --------------------------------------------------------------------------
BG = "#0F1720"
TEXT = "#F5F7FA"
MUTED = "#9AAABB"
DIM = "#6B7C8D"
LINE = "#2A3644"
ACCENT = "#38BDF8"
AMBER = "#FFB020"

FIGSIZE = (19.2, 10.8)   # 100dpi 기준 1920x1080
DPI = 100

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


def _style_axes(ax):
    """공통 축 스타일 — hairline만 남기고 나머지는 죽인다."""
    ax.set_facecolor(BG)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("bottom", "left"):
        ax.spines[side].set_color(LINE)
        ax.spines[side].set_linewidth(1.0)
    ax.tick_params(colors=MUTED, labelsize=17, length=4)
    ax.yaxis.label.set_color(MUTED)
    ax.xaxis.label.set_color(MUTED)
    ax.grid(axis="y", color=LINE, linewidth=1.0, alpha=0.55, zorder=0)
    ax.set_axisbelow(True)


def _read_csv(name):
    path = RESULTS / name
    with path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows


def _save(fig, out_path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=DPI, facecolor=BG)
    plt.close(fig)
    print(f"[p0] wrote {out_path}")


# ==========================================================================
# 1. chart_gain_sweep.png — 게인으로 닫히는 몫
# ==========================================================================
def make_gain_sweep(out_dir: Path):
    rows = _read_csv("p1_sweep.csv")
    x = np.array([float(r["stiffness"]) for r in rows])
    y = np.array([float(r["sag_max_deg"]) for r in rows])

    reduction_pct = (y[0] - y[-1]) / y[0] * 100.0

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor(BG)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.90, bottom=0.14)
    _style_axes(ax)

    ax.set_xscale("log")
    ax.plot(x, y, color=ACCENT, linewidth=2.5, zorder=3)
    ax.scatter(x, y, s=170, color=ACCENT, edgecolors=BG, linewidths=2.5, zorder=4)

    # 위첨자(³⁴⁵⁶)는 Malgun Gothic에 없는 글리프라 mathtext로 그린다
    # (mathtext는 rcParams['font.family']와 무관하게 자체 수식 폰트를 쓴다)
    ax.set_xticks([1e3, 1e4, 1e5, 1e6])
    ax.xaxis.set_major_formatter(
        mticker.FixedFormatter([r"$10^{3}$", r"$10^{4}$", r"$10^{5}$", r"$10^{6}$"])
    )
    ax.set_xlabel("joint drive stiffness (log scale)", fontsize=18, labelpad=14)
    ax.set_ylabel("중력 처짐 최대값 (°)", fontsize=18, labelpad=14)
    ax.set_ylim(0, y[0] * 1.18)

    # 포화 지점 — 10^5부터 값이 바뀌지 않는다
    sat_x = x[2]
    ax.axvline(sat_x, color=LINE, linewidth=1.4, zorder=1)
    ax.text(sat_x * 1.15, y[0] * 1.10, r"$10^{5}$ 이상 포화", fontsize=16,
            color=MUTED, va="top", ha="left")

    # 끝점 직접 라벨 (숫자는 AMBER 전용) — 첫 점은 마커 오른쪽에, 포화점은
    # 위쪽 화살표로. 감소율 큰 콜아웃은 곡선이 이미 다 내려온 우측 빈 공간에
    # 따로 둬서 서로 겹치지 않게 한다.
    ax.annotate(f"{y[0]:.4f}°", xy=(x[0], y[0]), xytext=(x[0] * 1.55, y[0] * 0.94),
                fontsize=22, color=AMBER, fontweight="bold", va="center")
    ax.annotate(f"{y[-1]:.4f}°", xy=(sat_x, y[2]), xytext=(sat_x * 1.6, y[0] * 0.30),
                fontsize=22, color=AMBER, fontweight="bold", va="bottom",
                arrowprops=dict(arrowstyle="-", color=DIM, linewidth=1.2))

    ax.text(5e5, y[0] * 0.62, f"{reduction_pct:.1f}%↓", ha="left", va="top",
            fontsize=30, color=AMBER, fontweight="bold")
    ax.text(5e5, y[0] * 0.49, "gain 스윕 (payload 0kg)", ha="left", va="top",
            fontsize=15, color=DIM)

    _save(fig, out_dir / "chart_gain_sweep.png")
    return reduction_pct


# ==========================================================================
# 2. chart_freq_scan.png — 지연으로만 설명되는 몫
# ==========================================================================
def make_freq_scan(out_dir: Path):
    rows = _read_csv("p1_freqscan.csv")
    freq = np.array([float(r["freq_hz"]) for r in rows])
    rms = np.array([float(r["track_rms_deg"]) for r in rows])
    assert len(rows) == 3, "측정점은 3개여야 한다 — CSV가 바뀌었으면 지시서부터 다시 확인할 것"

    # 원점 통과 최소자승 회귀: rms = slope * freq
    slope = float((freq * rms).sum() / (freq * freq).sum())

    # 순수 지연 모델(진폭 15°, 소각근사): e(t) = -A*ω*τ*cos(ωt), ω = 2πf
    # RMS[deg] = A_deg * ω * τ / sqrt(2)  →  slope(deg/Hz) = A_deg * 2π * τ / sqrt(2)
    # (각도를 라디안으로 바꿀 필요 없다 — A_deg가 이미 도(deg) 단위라 양변의
    #  deg 단위가 그대로 상쇄된다. 한 번 더 radians()를 걸면 π/180배 만큼
    #  τ가 부풀어 오른다 — 실제로 이 실수로 1501ms가 나온 적 있다.)
    amp_deg = 15.0
    coeff = amp_deg * 2.0 * math.pi / math.sqrt(2.0)
    tau_s = slope / coeff
    tau_ms = tau_s * 1000.0

    fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor(BG)
    fig.subplots_adjust(left=0.09, right=0.97, top=0.90, bottom=0.14)
    _style_axes(ax)

    # 회귀선 — 측정 범위를 살짝 넘겨 추세만 보여준다. 마커는 찍지 않는다 (측정 안 한 점).
    x_line = np.array([0.0, freq.max() * 1.15])
    ax.plot(x_line, slope * x_line, color=ACCENT, linewidth=2.0, alpha=0.45,
            zorder=2)

    ax.scatter(freq, rms, s=190, color=ACCENT, edgecolors=BG, linewidths=2.5,
               zorder=4, label="측정값 (3점)")

    ax.set_xlim(0, freq.max() * 1.2)
    ax.set_ylim(0, rms.max() * 1.25)
    ax.set_xlabel("사인 궤적 주파수 (Hz)", fontsize=18, labelpad=14)
    ax.set_ylabel("궤적 추종 RMS 오차 (°)", fontsize=18, labelpad=14)

    ax.annotate(f"τ ~ {tau_ms:.0f}ms", xy=(freq.max(), rms.max()),
                xytext=(freq.max() * 0.55, rms.max() * 1.12),
                fontsize=26, color=AMBER, fontweight="bold")
    ax.text(0.015, 0.93,
            f"오차 ∝ 주파수  (회귀 기울기 {slope:.3f}°/Hz, R = 원점 통과 최소자승)",
            transform=ax.transAxes, fontsize=15, color=DIM, va="top")
    ax.text(0.015, 0.10, "측정점 3개 (0.125 / 0.25 / 0.5 Hz) — 그 이상은 미측정",
            transform=ax.transAxes, fontsize=15, color=DIM, va="bottom")

    _save(fig, out_dir / "chart_freq_scan.png")
    return slope, tau_ms


# ==========================================================================
# 3. chart_payload.png — 정적/동적 비대칭 (2단 패널. dual-axis는 쓰지 않는다)
# ==========================================================================
def make_payload(out_dir: Path):
    rows = _read_csv("p1_payload.csv")
    payload = np.array([float(r["payload_kg"]) for r in rows])
    sag = np.array([float(r["sag_max_deg"]) for r in rows])
    track = np.array([float(r["track_rms_deg"]) for r in rows])

    static_ratio = sag[-1] / sag[0]
    dynamic_pct = (track[-1] - track[0]) / track[0] * 100.0

    fig, (axL, axR) = plt.subplots(1, 2, figsize=FIGSIZE, dpi=DPI)
    fig.patch.set_facecolor(BG)
    fig.subplots_adjust(left=0.075, right=0.965, top=0.86, bottom=0.14, wspace=0.28)

    # 두 패널 사이 구분선
    fig.add_artist(plt.Line2D([0.515, 0.515], [0.10, 0.90], color=LINE,
                               linewidth=1.2, transform=fig.transFigure))

    for ax in (axL, axR):
        _style_axes(ax)
        ax.set_xlabel("payload (kg)", fontsize=18, labelpad=14)
        ax.set_xticks(payload)

    # ---- 좌: 정적 처짐 — 크게 움직인다 --------------------------------
    axL.set_title("정적 처짐 (T1)", fontsize=17, color=MUTED, pad=14, loc="left")
    axL.plot(payload, sag, color=ACCENT, linewidth=2.5, zorder=3)
    axL.scatter(payload, sag, s=170, color=ACCENT, edgecolors=BG, linewidths=2.5,
                zorder=4)
    axL.set_ylabel("sag_max (°)", fontsize=18, labelpad=14)
    axL.set_ylim(0, sag.max() * 1.25)
    axL.annotate(f"{sag[0]:.4f}°", xy=(payload[0], sag[0]),
                 xytext=(payload[0] + 0.3, sag[0] + sag.max() * 0.06),
                 fontsize=16, color=MUTED)
    axL.annotate(f"{sag[-1]:.4f}°", xy=(payload[-1], sag[-1]),
                 xytext=(payload[-1] - 3.6, sag[-1] + sag.max() * 0.08),
                 fontsize=20, color=AMBER, fontweight="bold")
    axL.text(0.03, 0.93, f"{static_ratio:.1f}×", transform=axL.transAxes,
              fontsize=30, color=AMBER, fontweight="bold", va="top")

    # ---- 우: 동적 오차 — 축을 0~1로 고정해 "거의 안 움직인다"를 왜곡 없이 보여준다
    axR.set_title("동적 오차 (T2, 0.5Hz)", fontsize=17, color=MUTED, pad=14,
                   loc="left")
    axR.plot(payload, track, color=ACCENT, linewidth=2.5, zorder=3)
    axR.scatter(payload, track, s=170, color=ACCENT, edgecolors=BG, linewidths=2.5,
                zorder=4)
    axR.set_ylabel("track_rms (°)", fontsize=18, labelpad=14)
    axR.set_ylim(0, 1.0)
    axR.annotate(f"{track[0]:.4f}° → {track[-1]:.4f}°",
                 xy=(payload[-1], track[-1]),
                 xytext=(payload[-1] - 6.6, track[-1] + 0.10),
                 fontsize=16, color=MUTED)
    axR.text(0.03, 0.93, f"{dynamic_pct:+.2f}%", transform=axR.transAxes,
              fontsize=30, color=AMBER, fontweight="bold", va="top")

    _save(fig, out_dir / "chart_payload.png")
    return static_ratio, dynamic_pct


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out-dir", type=str,
        default=r"C:\Users\Administrator\Desktop\n2p\10_Career\11_companies"
                r"\엔닷라이트\30_interview\assets",
    )
    args = parser.parse_args()
    out_dir = Path(args.out_dir)

    reduction_pct = make_gain_sweep(out_dir)
    slope, tau_ms = make_freq_scan(out_dir)
    static_ratio, dynamic_pct = make_payload(out_dir)

    print("\n[p0] 계산값 요약")
    print(f"  gain sweep  : {reduction_pct:.1f}% 감소 (0.0741° → 0.0021°)")
    print(f"  freq scan   : 기울기 {slope:.4f}°/Hz -> τ ≈ {tau_ms:.1f}ms")
    print(f"  payload     : 정적 {static_ratio:.2f}배 / 동적 {dynamic_pct:+.3f}%")


if __name__ == "__main__":
    main()
