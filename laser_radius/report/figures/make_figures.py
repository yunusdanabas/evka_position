#!/usr/bin/env python3
# Requires matplotlib (not a project dependency): pip install matplotlib
"""Generate the price/sourcing figures for the laser-radius study.

Only the two 2026-07-08 price-survey figures live here:
  - price_vs_accuracy.png  (device accuracy vs. USD price, log price axis)
  - turkey_availability.png (representative lead-time per device, by sourcing class)

The physics figures (accuracy_vs_range.png, error_budget.png) are NOT regenerated
here — the price survey did not change their underlying data.

Style deliberately matches those two: default matplotlib style, light grid, titled,
legend box, dpi 120. Prices are USD midpoints from the two survey files dated
2026-07-08; see procurement_and_bom.md for the sourced ranges and CONFIRMED/ESTIMATE
labels. ponytail: plain dicts, no plotting abstraction — it's two charts.
"""
import matplotlib.pyplot as plt

OUT = __file__.rsplit("/", 1)[0] if "/" in __file__ else "."

# availability class -> colour (kept consistent across both figures)
CLASS_COLOR = {
    "domestic": "#2ca02c",   # in-stock Turkey / fast
    "import":   "#ff7f0e",   # direct import (China/EU) or intl retail
    "quote":    "#d62728",   # quote + dealer/import, slow
}
CLASS_LABEL = {
    "domestic": "In-stock domestic (TR)",
    "import":   "Import / intl retail",
    "quote":    "Quote + dealer/import",
}

# name, accuracy_mm, price_usd (midpoint), confirmed?, availability, lead_days, flagged?
DEVICES = [
    ("Meskernel LDL-T-80",   1.0,   87.5, True,  "import",   21, False),
    ("Meskernel LDL-T 40",   1.0,   74.0, False, "import",   21, False),
    ("Meskernel LDK-40",     2.0,   70.0, False, "import",   21, False),
    ("JRT M88B",             1.0,   43.0, False, "import",   21, True),
    ("JRT B605B",            2.6,   60.0, False, "import",   21, True),
    ("Bosch PLR 40 C",       2.0,  117.0, True,  "domestic",  2, True),
    ("Bosch GLM 50-27 CG",   1.5,  175.0, True,  "domestic",  2, True),
    ("RS PRO ILDM-150H",     1.5,  110.0, False, "domestic",  4, False),
    ("Stanley TLM165i",      1.5,  112.0, False, "import",   10, False),
    ("Leica DISTO D2",       1.5,  290.0, True,  "domestic",  3, False),
    ("Leica DISTO D5",       1.0,  510.0, True,  "domestic",  3, False),
    ("Leica DISTO X6",       1.0, 2263.0, True,  "domestic",  3, False),
    ("Leica DISTO S910",     1.0, 2024.0, True,  "domestic",  3, False),
    ("Hilti PD-I",           1.5,  450.0, False, "quote",    14, False),
    ("Dimetix DBN-50-050",   5.0, 1332.0, True,  "import",   14, False),
    ("Dimetix DAE-10-050",   1.0, 2772.0, True,  "import",   14, False),
    ("Micro-Epsilon ILR2250",1.0, 1800.0, False, "quote",    35, False),
    ("Jenoptik LDM41",       3.0, 1500.0, False, "quote",    35, False),
    ("FAE LS 121/122 FA",    3.0, 1400.0, False, "quote",    35, False),
]

# labels worth annotating on the scatter (the story: same accuracy, huge price spread)
ANNOTATE = {
    "Meskernel LDL-T-80", "JRT M88B", "Leica DISTO D2", "Leica DISTO D5",
    "Leica DISTO X6", "Leica DISTO S910", "Dimetix DBN-50-050",
    "Dimetix DAE-10-050", "Micro-Epsilon ILR2250", "FAE LS 121/122 FA",
    "Bosch PLR 40 C",
}


def price_vs_accuracy():
    fig, ax = plt.subplots(figsize=(10, 6.2))
    seen = set()
    for name, acc, price, conf, avail, _days, flagged in DEVICES:
        color = CLASS_COLOR[avail]
        lbl = CLASS_LABEL[avail] if avail not in seen else None
        seen.add(avail)
        ax.scatter(
            acc, price, s=140, zorder=3, label=lbl,
            marker="o",
            facecolor=(color if conf else "none"),
            edgecolor=color, linewidths=1.8,
        )
        if flagged:  # ring the two principle-unconfirmed devices
            ax.scatter(acc, price, s=320, facecolor="none",
                       edgecolor="#7f7f7f", linewidths=1.4, linestyle=":", zorder=2)

    for name, acc, price, *_ in DEVICES:
        if name in ANNOTATE:
            ax.annotate(name, (acc, price), textcoords="offset points",
                        xytext=(8, 4), fontsize=8, color="#333333")

    ax.set_yscale("log")
    ax.set_xlim(0.4, 5.6)
    ax.set_xlabel("Device accuracy (mm, flat across range)")
    ax.set_ylabel("Price (USD, log scale)")
    ax.set_title("Price vs. Accuracy — you pay for housing & brand, not accuracy\n"
                 "(2026-07-08 survey; filled = CONFIRMED price, hollow = ESTIMATE)")
    ax.grid(True, which="both", alpha=0.3)

    # highlight the ~1 mm column price spread
    ax.axvline(1.0, color="#888888", lw=0.8, ls="--", zorder=1)
    ax.annotate("same $\\pm$1 mm accuracy:\n\\$43 → \\$2,772  (~64×)",
                (1.0, 300), xytext=(1.55, 320), fontsize=9, color="#555555",
                arrowprops=dict(arrowstyle="->", color="#888888"))

    # extra legend entry for the flagged ring
    from matplotlib.lines import Line2D
    handles, labels = ax.get_legend_handles_labels()
    handles.append(Line2D([0], [0], marker="o", markersize=11, linestyle="none",
                          markerfacecolor="none", markeredgecolor="#7f7f7f",
                          markeredgewidth=1.4))
    labels.append("Flagged: phase-shift unconfirmed")
    ax.legend(handles, labels, loc="lower right", framealpha=0.95, fontsize=9)

    fig.tight_layout()
    fig.savefig(f"{OUT}/price_vs_accuracy.png", dpi=120)
    plt.close(fig)


def turkey_availability():
    rows = sorted(DEVICES, key=lambda d: (d[5], d[1]))  # by lead days, then accuracy
    names = [d[0] + ("  (confirmed)" if d[3] else "") for d in rows]
    days = [d[5] for d in rows]
    colors = [CLASS_COLOR[d[4]] for d in rows]

    fig, ax = plt.subplots(figsize=(10, 7.0))
    y = range(len(rows))
    ax.barh(list(y), days, color=colors, zorder=3, height=0.66)
    ax.set_yticks(list(y))
    ax.set_yticklabels(names, fontsize=9)
    for tick, d in zip(ax.get_yticklabels(), rows):
        if d[3]:
            tick.set_fontweight("bold")
    ax.invert_yaxis()  # fastest at top
    ax.set_xlabel("Representative lead-time to Istanbul (days)")
    ax.set_title("Turkey sourcing — lead-time by availability class\n"
                 "(bold = confirmed public price; 2026-07-08 survey)")
    ax.grid(True, axis="x", alpha=0.3, zorder=0)

    from matplotlib.patches import Patch
    handles = [Patch(facecolor=CLASS_COLOR[c], label=CLASS_LABEL[c])
               for c in ("domestic", "import", "quote")]
    ax.legend(handles=handles, loc="lower right", framealpha=0.95, fontsize=9)

    fig.tight_layout()
    fig.savefig(f"{OUT}/turkey_availability.png", dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    price_vs_accuracy()
    turkey_availability()
    print("wrote price_vs_accuracy.png, turkey_availability.png")
