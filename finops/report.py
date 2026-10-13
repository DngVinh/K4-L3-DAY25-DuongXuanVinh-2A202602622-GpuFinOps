"""Report assembly — the lab's deliverable: baseline vs optimized + savings chart."""
from __future__ import annotations


def build_report(baseline_usd: float, optimized_usd: float, levers: dict,
                 sustainability: dict | None = None, period: str = "monthly") -> str:
    """Return a markdown cost-optimization report."""
    savings = baseline_usd - optimized_usd
    pct = (savings / baseline_usd * 100.0) if baseline_usd > 0 else 0.0
    lines = [
        "# NimbusAI — GPU Cost Optimization Report",
        "",
        f"**Period:** {period}", "",
        f"**Baseline spend:** ${baseline_usd:,.2f}", "",
        f"**Optimized spend:** ${optimized_usd:,.2f}", "",
        f"**Projected savings:** ${savings:,.2f}  (**{pct:.0f}%**; precise: {pct:.2f}%)",
        "",
        "## Savings by lever",
        "",
        "| Lever | Savings (USD) |",
        "|---|---|",
    ]
    for name, amount in levers.items():
        lines.append(f"| {name} | ${amount:,.2f} |")
    if sustainability:
        lines += [
            "",
            "## Sustainability",
            "",
            f"- Energy per query (illustrative ordinary query): {sustainability.get('wh_per_query', 0):.2f} Wh",
            f"- Carbon per query (us-east-1, illustrative): {sustainability.get('carbon_g', 0):.3f} gCO2e",
            f"- Cleanest region: {sustainability.get('best_region', 'n/a')}",
            f"- Cheapest electricity region: {sustainability.get('cheapest_region', 'n/a')}",
        ]
    lines += ["", "_Figures are June-2026 as-of snapshots; re-baseline before acting._"]
    return "\n".join(lines)


def savings_waterfall(levers: dict, path: str, baseline_usd: float | None = None) -> str:
    """Write floating savings steps with baseline and final spend totals."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return ""
    names = list(levers.keys())
    vals = [levers[n] for n in names]
    baseline = baseline_usd if baseline_usd is not None else sum(vals)
    labels = ["Baseline"] + names + ["Optimized"]
    fig, ax = plt.subplots(figsize=(12, 6))
    remaining = baseline
    ax.bar(0, baseline, color="#2e548a")
    ax.text(0, baseline, f"${baseline:,.2f}", ha="center", va="bottom", fontsize=9)
    for i, amount in enumerate(vals, 1):
        after = remaining - amount
        ax.plot([i-1+0.4, i-0.4], [remaining, remaining], color="#888888", linewidth=1)
        ax.bar(i, amount, bottom=after, color="#25876a")
        ax.text(i, remaining, f"-${amount:,.2f}" if amount else "$0 booked\n(conditional)",
                ha="center", va="bottom", fontsize=9)
        remaining = after
    ax.bar(len(labels)-1, remaining, color="#2e548a")
    ax.text(len(labels)-1, remaining, f"${remaining:,.2f}", ha="center", va="bottom", fontsize=9)
    ax.set_xticks(range(len(labels)), labels, rotation=18, ha="right")
    ax.set_ylim(0, baseline*1.18)
    ax.set_ylabel("Spend (USD / month)")
    ax.set_title("NimbusAI: reconciled monthly savings waterfall")
    ax.spines[["top", "right"]].set_visible(False)
    plt.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return path
