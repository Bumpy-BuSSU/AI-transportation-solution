"""Run the frozen Stage3B H1/H2 confirmatory analysis on approved Stage3A data."""
from __future__ import annotations

from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import platform
import sys
import tempfile
import traceback

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow
import statsmodels

from subway.src.analysis.confirmatory import (
    build_confirmatory_tables,
    fit_confirmatory_models,
    load_confirmatory_config,
)
from subway.src.utils.paths import resolve_repo_relative

SPEC_FREEZE_SHA = "f5433eb98d96d8098c265de0859282dcc53046f1"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _json(path: Path, payload: dict) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _csv(path: Path, frame: pd.DataFrame, sort: list[str]) -> None:
    if not sort or any(c not in frame for c in sort):
        raise ValueError("invalid confirmatory sort contract")
    if frame.duplicated(sort).any():
        raise ValueError("confirmatory sort columns are not unique")
    frame.sort_values(sort, kind="stable", na_position="last").reset_index(drop=True).to_csv(
        path, index=False, encoding="utf-8", lineterminator="\n"
    )


def _render_effects(family: pd.DataFrame, path: Path) -> None:
    labels = {
        "h1_hot_senior_differential": "H1 hot",
        "h1_cold_senior_differential": "H1 cold",
        "h2_hot_daytime_amplification": "H2 hot × daytime",
        "h2_cold_daytime_amplification": "H2 cold × daytime",
    }
    order = list(labels)
    frame = family.set_index("hypothesis").loc[order].reset_index()
    y = np.arange(len(frame))
    effect = frame["relative_percent"].to_numpy(float)
    low = (frame["irr_ci95_low"].to_numpy(float) - 1.0) * 100.0
    high = (frame["irr_ci95_high"].to_numpy(float) - 1.0) * 100.0
    fig, ax = plt.subplots(figsize=(8, 4.8))
    ax.errorbar(effect, y, xerr=np.vstack([effect - low, high - effect]), fmt="o", capsize=4)
    ax.axvline(0.0, linewidth=1, linestyle="--")
    ax.set_yticks(y, [labels[v] for v in order])
    ax.set_xlabel("Age-differential relative change (%) with 95% CI")
    ax.set_title("Frozen confirmatory H1/H2 estimates")
    ax.grid(True, axis="x", alpha=0.2)
    fig.text(
        0.5, 0.01,
        "PPML; date-clustered SE; p90/p10 primary extremes. Relative effects are associations, not trip-purpose or causal policy effects.",
        ha="center", fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(path, dpi=160, metadata={"Software": "subway Stage3B / matplotlib " + matplotlib.__version__})
    plt.close(fig)


def run_confirmatory(repo_root: Path, year: int) -> int:
    repo = Path(repo_root).resolve()
    try:
        config = load_confirmatory_config(repo, year)
        analysis_base = repo / "subway/data/analysis" / f"analysis_base_{year}.parquet"
        eda_summary_path = repo / "subway/results/tables/eda_summary.json"
        if not analysis_base.exists():
            from subway.run_eda import run_eda
            if run_eda(repo, year):
                raise ValueError("Stage3A regeneration blocked")
        if not eda_summary_path.exists():
            raise ValueError("Stage3A summary missing")
        eda = json.loads(eda_summary_path.read_text(encoding="utf-8"))
        expected = eda.get("output_hashes", {}).get(f"subway/data/analysis/analysis_base_{year}.parquet")
        if not expected or sha256(analysis_base) != expected:
            raise ValueError("Stage3A analysis-base hash mismatch")
        if eda.get("status") != "EDA COMPLETE":
            raise ValueError("Stage3A technical completion required")

        base = pd.read_parquet(analysis_base)
        boarding_h1, boarding_h2, extreme, boarding_summary = build_confirmatory_tables(base, config, year)
        alighting_h1, alighting_h2, extreme_a, alighting_summary = build_confirmatory_tables(
            base, config, year, event="alighting"
        )
        pd.testing.assert_frame_equal(extreme, extreme_a)

        outputs, model_meta = fit_confirmatory_models(
            boarding_h1, boarding_h2, alighting_h1, alighting_h2
        )
        family = outputs["confirmatory_test_family.csv"]

        model_spec = {
            "spec_freeze_sha": SPEC_FREEZE_SHA,
            "year": year,
            "study_area_id": config["study_area_id"],
            "primary_event": config["primary_event"],
            "primary_hot": config["hot_primary"],
            "primary_cold": config["cold_primary"],
            "sensitivity_hot": config["hot_sensitivity"],
            "sensitivity_cold": config["cold_sensitivity"],
            "daytime": config["daytime"],
            "h1_inference_unit": "date_x_age_group",
            "h2_inference_unit": "date_x_age_group_x_daytime",
            "h1_design": "date FE + senior + senior×month FE + senior×DOW FE + senior×hot + senior×cold",
            "h2_design": "date FE + senior/daytime/lower-order + senior/daytime×month/DOW differentials + extreme lower-order + senior×extreme×daytime",
            "covariance": "cluster_date",
            "multiple_testing": config["multiple_testing"],
            "benchmark": config["robustness"]["log_ratio_benchmark"],
            "statistical_interpretation": "age-differential association under frozen citywide daily exposure; not causal trip-purpose evidence",
        }

        summary = {
            "status": "CONFIRMATORY H1/H2 COMPLETE",
            "year": year,
            "spec_freeze_sha": SPEC_FREEZE_SHA,
            "stage3a_human_approved_on": config["stage3a_human_approved_on"],
            "analysis_base_sha256": expected,
            "config_sha256": sha256(repo / "subway/config" / f"confirmatory_analysis_{year}.yaml"),
            "code_sha256": sha256(repo / "subway/src/analysis/confirmatory.py"),
            "runner_sha256": sha256(repo / "subway/run_confirmatory.py"),
            "boarding_sample": boarding_summary,
            "alighting_sample": alighting_summary,
            "model_meta": model_meta,
            "primary_test_count": int(len(family)),
            "holm_rejections": int(family["holm_reject"].sum()),
            "threshold_changed_after_results": False,
            "spatial_secondary_started": False,
            "trip_purpose_inferred": False,
            "causal_policy_conclusion": False,
            "environment": {
                "python": platform.python_version(),
                "pandas": pd.__version__,
                "numpy": np.__version__,
                "pyarrow": pyarrow.__version__,
                "matplotlib": matplotlib.__version__,
                "statsmodels": statsmodels.__version__,
            },
        }

        root = repo / "subway"
        models = root / "results/models"
        tables = root / "results/tables"
        figures = root / "results/figures"
        models.mkdir(parents=True, exist_ok=True)
        tables.mkdir(parents=True, exist_ok=True)
        figures.mkdir(parents=True, exist_ok=True)

        with tempfile.TemporaryDirectory(prefix=".confirmatory-staging-", dir=root / "data") as tmp:
            stage = Path(tmp)
            (stage / "models").mkdir()
            (stage / "tables").mkdir()
            (stage / "figures").mkdir()

            _csv(stage / "models/h1_primary_results.csv", outputs["h1_primary_results.csv"], ["hypothesis"])
            _csv(stage / "models/h2_primary_results.csv", outputs["h2_primary_results.csv"], ["hypothesis"])
            _csv(
                stage / "models/confirmatory_sensitivity_results.csv",
                outputs["confirmatory_sensitivity_results.csv"],
                ["model", "event", "threshold", "hypothesis"],
            )
            _csv(stage / "models/confirmatory_test_family.csv", family, ["hypothesis"])
            _json(stage / "models/confirmatory_model_spec.json", model_spec)
            _json(stage / "models/confirmatory_summary.json", summary)

            _csv(stage / "tables/confirmatory_daily_age_counts.csv", boarding_h1, ["date", "age_group"])
            _csv(
                stage / "tables/confirmatory_daily_age_daytime_counts.csv",
                boarding_h2,
                ["date", "daytime", "age_group"],
            )
            _csv(stage / "tables/extreme_temperature_days_2024.csv", extreme, ["date"])
            _render_effects(family, stage / "figures/confirmatory_effects.png")

            staged = []
            for folder in ("models", "tables", "figures"):
                for path in sorted((stage / folder).iterdir()):
                    staged.append((path, root / "results" / folder / path.name))
            for source, target in staged:
                os.replace(source, target)

        print("Stage3B confirmatory H1/H2 COMPLETE; frozen specification used; human result review PENDING")
        return 0
    except Exception as exc:
        logs = repo / "subway/logs"
        logs.mkdir(parents=True, exist_ok=True)
        with (logs / "run_confirmatory.log").open("a", encoding="utf-8") as log:
            log.write(traceback.format_exc() + "\n")
        print(f"CONFIRMATORY BLOCKED: {type(exc).__name__}; inspect subway/logs/run_confirmatory.log", file=sys.stderr)
        return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year", type=int, required=True)
    return run_confirmatory(ROOT, parser.parse_args(argv).year)


if __name__ == "__main__":
    raise SystemExit(main())
