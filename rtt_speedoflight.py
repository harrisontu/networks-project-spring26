"""
RTT vs. Speed-of-Light
Networks Assignment — Measurement & Geography

Run with: python rtt_speedoflight.py   (no sudo needed)
Requires: pip install requests matplotlib numpy
"""

import math, time, os, requests, numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import urllib.request

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

TARGETS = {
    "Tokyo":        {"url": "http://www.google.co.jp",   "coords": (35.6762,  139.6503), "continent": "Asia"},
    "São Paulo":    {"url": "http://www.google.com.br",  "coords": (-23.5505, -46.6333), "continent": "S. America"},
    "Lagos":        {"url": "http://www.google.com.ng",  "coords": (6.5244,     3.3792), "continent": "Africa"},
    "Frankfurt":    {"url": "http://www.google.de",      "coords": (50.1109,    8.6821), "continent": "Europe"},
    "Sydney":       {"url": "http://www.google.com.au",  "coords": (-33.8688, 151.2093), "continent": "Oceania"},
    "Mumbai":       {"url": "http://www.google.co.in",   "coords": (19.0760,   72.8777), "continent": "Asia"},
    "London":       {"url": "http://www.google.co.uk",   "coords": (51.5074,   -0.1278), "continent": "Europe"},
    "Singapore":    {"url": "http://www.google.com.sg",  "coords": (1.3521,   103.8198), "continent": "Asia"},
}

PROBES           = 15
FIBER_SPEED_KM_S = 200_000
FIGURES_DIR      = "figures"

CONTINENT_COLORS = {
    "Asia":      "#e63946",
    "S. America":"#2a9d8f",
    "Africa":    "#e9c46a",
    "Europe":    "#457b9d",
    "Oceania":   "#a8dadc",
}

# ─────────────────────────────────────────────
# TASK 1 — MEASURE RTTs
# ─────────────────────────────────────────────

def measure_rtt(url: str, probes: int = PROBES) -> dict:
    """
    Measure RTT to `url` using HTTP requests.

    Return:
        {
            "min_ms":   float | None,
            "mean_ms":  float | None,
            "median_ms":float | None,
            "loss_pct": float,
            "samples":  list[float],
        }
    """
    samples = []
    lost    = 0

    for _ in range(probes):
        try:
            start = time.perf_counter()
            urllib.request.urlopen(url, timeout=3)
            elapsed_ms = (time.perf_counter() - start) * 1000
            samples.append(elapsed_ms)
        except Exception:
            lost += 1
        time.sleep(0.2)

    if not samples:
        return {"min_ms": None, "mean_ms": None, "median_ms": None,
                "loss_pct": 100.0, "samples": []}

    arr = np.array(samples)
    return {
        "min_ms":    float(np.min(arr)),
        "mean_ms":   float(np.mean(arr)),
        "median_ms": float(np.median(arr)),
        "loss_pct":  (lost / probes) * 100,
        "samples":   samples,
    }


# ─────────────────────────────────────────────
# TASK 2 — HAVERSINE + INEFFICIENCY
# ─────────────────────────────────────────────

def great_circle_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute great-circle distance in km using the Haversine formula.

    Haversine:
        a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
        c = 2 * atan2(√a, √(1−a))
        d = R * c       where R = 6371 km
    """
    R = 6371
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def get_my_location() -> tuple[float, float, str]:
    """Return (lat, lon, city) for this machine's public IP."""
    try:
        r = requests.get("https://ipinfo.io/json", timeout=5).json()
        lat, lon = map(float, r["loc"].split(","))
        return lat, lon, r.get("city", "Your Location")
    except Exception:
        print("Could not auto-detect location. Defaulting to Boston.")
        return 42.3601, -71.0589, "Boston"


def compute_inefficiency(results: dict, src_lat: float, src_lon: float) -> dict:
    """
    Annotate each city in results with:
        "distance_km"        — great-circle distance from source
        "theoretical_min_ms" — 2 * (distance / FIBER_SPEED_KM_S) * 1000
        "inefficiency_ratio" — median_ms / theoretical_min_ms
        "high_inefficiency"  — True if ratio > 3.0
    """
    for city, data in results.items():
        lat2, lon2 = data["coords"]
        dist_km = great_circle_km(src_lat, src_lon, lat2, lon2)
        theoretical_min_ms = (dist_km / FIBER_SPEED_KM_S) * 2 * 1000

        median_ms = data.get("median_ms")
        if median_ms is not None and theoretical_min_ms > 0:
            ratio = median_ms / theoretical_min_ms
        else:
            ratio = None

        data["distance_km"]        = dist_km
        data["theoretical_min_ms"] = theoretical_min_ms
        data["inefficiency_ratio"] = ratio
        data["high_inefficiency"]  = (ratio is not None and ratio > 3.0)

    return results


# ─────────────────────────────────────────────
# TASK 3 — PLOTS
# ─────────────────────────────────────────────

def make_plots(results: dict):
    """
    Produce two figures saved to FIGURES_DIR/.

    Figure 1 — fig1_rtt_comparison.png
        Grouped bar chart: measured median RTT vs. theoretical min RTT per city.
        Sort cities by distance_km ascending.

    Figure 2 — fig2_distance_scatter.png
        Scatter: x = distance_km, y = measured median RTT.
        Dashed line for theoretical minimum.
        Label each point with city name.
        Color by continent.
    """
    os.makedirs(FIGURES_DIR, exist_ok=True)
    valid  = {c: d for c, d in results.items() if d.get("median_ms") is not None}
    cities = sorted(valid, key=lambda c: valid[c]["distance_km"])

    if not cities:
        print("No valid measurements — skipping plots.")
        return

    # ── Figure 1: Grouped bar chart ───────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(11, 6))

    x        = np.arange(len(cities))
    width    = 0.35
    medians  = [valid[c]["median_ms"]          for c in cities]
    theorets = [valid[c]["theoretical_min_ms"] for c in cities]

    bars1 = ax.bar(x - width/2, medians,  width, label="Measured Median RTT",     color="#4361ee", alpha=0.85)
    bars2 = ax.bar(x + width/2, theorets, width, label="Theoretical Minimum RTT", color="#f77f00", alpha=0.85)

    ax.set_xlabel("City (sorted by distance from source)", fontsize=12)
    ax.set_ylabel("Round-Trip Time (ms)", fontsize=12)
    ax.set_title("Measured vs. Theoretical Minimum RTT by City", fontsize=14, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(cities, rotation=20, ha="right", fontsize=10)
    ax.legend(fontsize=11)
    ax.yaxis.grid(True, linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    for bar in bars1:
        h = bar.get_height()
        ax.annotate(f"{h:.0f}", xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8)
    for bar in bars2:
        h = bar.get_height()
        ax.annotate(f"{h:.0f}", xy=(bar.get_x() + bar.get_width()/2, h),
                    xytext=(0, 3), textcoords="offset points",
                    ha="center", va="bottom", fontsize=8)

    plt.tight_layout()
    plt.savefig(f"{FIGURES_DIR}/fig1_rtt_comparison.png", dpi=150, bbox_inches="tight")
    plt.close()

    # ── Figure 2: Scatter plot ────────────────────────────────────────────────
    fig, ax = plt.subplots(figsize=(10, 7))

    distances = [valid[c]["distance_km"]        for c in cities]
    medians2  = [valid[c]["median_ms"]          for c in cities]
    colors    = [CONTINENT_COLORS[valid[c]["continent"]] for c in cities]

    ax.scatter(distances, medians2, c=colors, s=120, zorder=5,
               edgecolors="black", linewidths=0.6)

    max_dist = max(distances) * 1.08
    line_x   = np.linspace(0, max_dist, 400)
    line_y   = (line_x / FIBER_SPEED_KM_S) * 2 * 1000
    ax.plot(line_x, line_y, "k--", linewidth=1.5, alpha=0.7)

    for city, dist, med in zip(cities, distances, medians2):
        ax.annotate(city, (dist, med), textcoords="offset points",
                    xytext=(6, 4), fontsize=9, ha="left")

    legend_patches = [
        mpatches.Patch(color=col, label=cont)
        for cont, col in CONTINENT_COLORS.items()
        if any(valid[c]["continent"] == cont for c in cities)
    ]
    legend_patches.append(
        plt.Line2D([0], [0], linestyle="--", color="black",
                   label="Theoretical Minimum (fiber)")
    )
    ax.legend(handles=legend_patches, fontsize=10, loc="upper left")

    ax.set_xlabel("Great-Circle Distance (km)", fontsize=12)
    ax.set_ylabel("Measured Median RTT (ms)", fontsize=12)
    ax.set_title("RTT vs. Great-Circle Distance (colored by continent)", fontsize=14, fontweight="bold")
    ax.yaxis.grid(True, linestyle="--", alpha=0.4)
    ax.xaxis.grid(True, linestyle="--", alpha=0.4)
    ax.set_axisbelow(True)

    plt.tight_layout()
    plt.savefig(f"{FIGURES_DIR}/fig2_distance_scatter.png", dpi=150, bbox_inches="tight")
    plt.close()

    print(f"Figures saved to {FIGURES_DIR}/")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    src_lat, src_lon, src_city = get_my_location()
    print(f"Your location: {src_city} ({src_lat:.4f}, {src_lon:.4f})\n")

    results = {}
    for city, info in TARGETS.items():
        print(f"Probing {city} ({info['url']}) ...", end=" ", flush=True)
        stats = measure_rtt(info["url"])
        results[city] = {**stats, "coords": info["coords"], "continent": info["continent"]}
        med = stats.get("median_ms")
        print(f"median={med:.1f} ms  loss={stats['loss_pct']:.0f}%" if med else "unreachable")

    results = compute_inefficiency(results, src_lat, src_lon)

    print(f"\n{'City':<14} {'Dist km':>8} {'Median ms':>10} {'Theor. ms':>10} {'Ratio':>7}")
    print("─" * 55)
    for city, d in sorted(results.items(), key=lambda x: x[1].get("distance_km", 0)):
        dist  = d.get("distance_km", 0)
        med   = d.get("median_ms")
        theor = d.get("theoretical_min_ms")
        ratio = d.get("inefficiency_ratio")
        flag  = " ⚠️" if d.get("high_inefficiency") else ""
        print(f"{city:<14} {dist:>8.0f} "
              f"{(f'{med:.1f}' if med else 'N/A'):>10} "
              f"{(f'{theor:.1f}' if theor else 'N/A'):>10} "
              f"{(f'{ratio:.2f}' if ratio else 'N/A'):>7}{flag}")

    make_plots(results)

if __name__ == "__main__":
    main()
