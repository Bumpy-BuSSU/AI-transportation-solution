"""Frozen Stage3B confirmatory table construction; no model fit in this module."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import yaml

from subway.src.transform.ridership import KEYS

DAYTIME_BINS = [f"{h:02}_{h+1:02}" for h in range(10, 16)]
AGE_GROUPS = ("senior", "non_senior")
EVENTS = ("boarding", "alighting")

_FROZEN = {
    "schema_version": 1,
    "reference_year": 2024,
    "study_area_id": "seoul_2024",
    "primary_event": "boarding",
    "age_comparison_rule": "common_valid_cells",
    "temperature_source": "seoul_asos108_daily",
    "daytime.start_hour": 10,
    "daytime.end_hour": 16,
    "daytime.bins": DAYTIME_BINS,
    "hot_primary.variable": "temperature_max",
    "hot_primary.quantile": 0.90,
    "hot_primary.threshold_c": 32.75,
    "hot_primary.operator": "ge",
    "cold_primary.variable": "temperature_min",
    "cold_primary.quantile": 0.10,
    "cold_primary.threshold_c": -3.05,
    "cold_primary.operator": "le",
    "hot_sensitivity.variable": "temperature_max",
    "hot_sensitivity.quantile": 0.95,
    "hot_sensitivity.threshold_c": 33.675,
    "hot_sensitivity.operator": "ge",
    "cold_sensitivity.variable": "temperature_min",
    "cold_sensitivity.quantile": 0.05,
    "cold_sensitivity.threshold_c": -4.8,
    "cold_sensitivity.operator": "le",
    "primary_model.family": "ppml",
    "primary_model.inference_unit": "daily_age_group",
    "primary_model.date_fixed_effects": True,
    "primary_model.age_month_interactions": True,
    "primary_model.age_day_of_week_interactions": True,
    "primary_model.covariance": "cluster_date",
    "h2_model.family": "ppml",
    "h2_model.inference_unit": "daily_age_group_daytime",
    "h2_model.date_fixed_effects": True,
    "h2_model.full_lower_order_extreme_daytime_interactions": True,
    "h2_model.age_daytime_month_interactions": True,
    "h2_model.age_daytime_day_of_week_interactions": True,
    "h2_model.covariance": "cluster_date",
    "multiple_testing.method": "holm",
    "multiple_testing.alpha": 0.05,
    "multiple_testing.tests": [
        "h1_hot_senior_differential",
        "h1_cold_senior_differential",
        "h2_hot_daytime_amplification",
        "h2_cold_daytime_amplification",
    ],
    "robustness.threshold_sensitivity": "p95_hot_p05_cold",
    "robustness.event_direction_sensitivity": "alighting",
    "robustness.log_ratio_benchmark.family": "ols",
    "robustness.log_ratio_benchmark.covariance": "hac",
    "robustness.log_ratio_benchmark.maxlags": 7,
}


def _nested(mapping: dict[str, Any], dotted: str) -> Any:
    value: Any = mapping
    for part in dotted.split("."):
        if not isinstance(value, dict) or part not in value:
            raise ValueError(f"confirmatory config missing: {dotted}")
        value = value[part]
    return value


def validate_confirmatory_config(profile: dict[str, Any], year: int) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise ValueError("confirmatory config must be a mapping")
    for dotted, expected in _FROZEN.items():
        actual = _nested(profile, dotted)
        if actual != expected:
            raise ValueError(f"frozen confirmatory setting changed: {dotted}")
    if year != 2024 or profile["reference_year"] != year:
        raise ValueError("confirmatory year mismatch")
    approval = profile.get("stage3a_human_approved_on")
    if approval != "2026-10-07":
        raise ValueError("Stage3A human approval record missing")
    interpretation = profile.get("interpretation")
    if not isinstance(interpretation, dict) or any(
        interpretation.get(key) is not False
        for key in ("trip_purpose_identified", "causal_policy_effect_identified", "interregional_gap_identified")
    ):
        raise ValueError("confirmatory interpretation safeguards changed")
    return profile


def load_confirmatory_config(repo_root: Path, year: int) -> dict[str, Any]:
    path = Path(repo_root) / "subway" / "config" / f"confirmatory_analysis_{year}.yaml"
    try:
        profile = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ValueError("confirmatory config unavailable or invalid") from exc
    return validate_confirmatory_config(profile, year)


def _daily_exposure(base: pd.DataFrame, config: dict[str, Any], year: int) -> pd.DataFrame:
    columns = [
        "date",
        config["hot_primary"]["variable"],
        config["cold_primary"]["variable"],
        config["hot_sensitivity"]["variable"],
        config["cold_sensitivity"]["variable"],
    ]
    columns = list(dict.fromkeys(columns))
    weather = base[columns].copy()
    if weather["date"].isna().any() or not pd.api.types.is_datetime64_any_dtype(weather["date"]):
        raise ValueError("confirmatory date must be normalized datetime")
    if not weather["date"].dt.year.eq(year).all() or not weather["date"].eq(weather["date"].dt.normalize()).all():
        raise ValueError("confirmatory date/year alignment failed")
    for column in columns[1:]:
        if weather[column].isna().any():
            raise ValueError(f"confirmatory weather missing: {column}")
        if weather.groupby("date", observed=True)[column].nunique(dropna=False).gt(1).any():
            raise ValueError(f"weather exposure varies within date: {column}")
    weather = weather.groupby("date", observed=True, as_index=False)[columns[1:]].first().sort_values("date")
    specs = (
        ("hot_primary", config["hot_primary"]),
        ("cold_primary", config["cold_primary"]),
        ("hot_sensitivity", config["hot_sensitivity"]),
        ("cold_sensitivity", config["cold_sensitivity"]),
    )
    for name, spec in specs:
        series = weather[spec["variable"]]
        if spec["operator"] == "ge":
            weather[name] = series.ge(float(spec["threshold_c"]))
        elif spec["operator"] == "le":
            weather[name] = series.le(float(spec["threshold_c"]))
        else:
            raise ValueError(f"unsupported extreme operator: {spec['operator']}")
    if (weather["hot_primary"] & weather["cold_primary"]).any():
        raise ValueError("primary hot/cold exposure overlap")
    if (weather["hot_sensitivity"] & weather["cold_sensitivity"]).any():
        raise ValueError("sensitivity hot/cold exposure overlap")
    weather["month"] = weather["date"].dt.month.astype("int64")
    weather["day_of_week"] = weather["date"].dt.dayofweek.astype("int64")
    return weather.reset_index(drop=True)


def _validate_base(base: pd.DataFrame, config: dict[str, Any], year: int) -> None:
    required = set(KEYS + [
        "senior",
        "non_senior",
        "age_comparison_valid",
        "daytime_10_16",
        config["hot_primary"]["variable"],
        config["cold_primary"]["variable"],
        config["hot_sensitivity"]["variable"],
        config["cold_sensitivity"]["variable"],
    ])
    if base.columns.duplicated().any() or not required.issubset(base.columns):
        raise ValueError("confirmatory analysis base schema mismatch")
    if base.duplicated(KEYS).any() or base[KEYS].isna().any().any():
        raise ValueError("confirmatory analysis base key invalid")
    if not pd.api.types.is_datetime64_any_dtype(base["date"]):
        raise ValueError("confirmatory date must be datetime")
    if not base["date"].dt.year.eq(year).all() or not base["date"].eq(base["date"].dt.normalize()).all():
        raise ValueError("confirmatory date/year alignment failed")
    if not set(base["boarding_type"].dropna().unique()).issubset(EVENTS):
        raise ValueError("unknown boarding_type")
    expected_daytime = base["hour_bin"].isin(config["daytime"]["bins"])
    if not base["daytime_10_16"].astype(bool).eq(expected_daytime).all():
        raise ValueError("daytime flag differs from frozen exact bins")
    valid = base["age_comparison_valid"].fillna(False).astype(bool)
    if base.loc[valid, ["senior", "non_senior"]].isna().any().any():
        raise ValueError("valid age-comparison rows require both age counts")
    if (base.loc[valid, ["senior", "non_senior"]] < 0).any().any():
        raise ValueError("negative confirmatory count")
    _daily_exposure(base, config, year)


def _to_age_long(wide: pd.DataFrame, id_columns: list[str]) -> pd.DataFrame:
    value_columns = ["senior", "non_senior"]
    long = wide.melt(
        id_vars=id_columns,
        value_vars=value_columns,
        var_name="age_group",
        value_name="count",
    )
    long["senior"] = long["age_group"].eq("senior").astype("int8")
    long["count"] = pd.to_numeric(long["count"], errors="raise")
    if long["count"].isna().any() or (long["count"] < 0).any():
        raise ValueError("invalid aggregated confirmatory count")
    return long


def build_confirmatory_tables(
    base: pd.DataFrame,
    config: dict[str, Any],
    year: int,
    *,
    event: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    """Aggregate common-valid station/hour cells to the daily exposure unit.

    The full Stage3A base is read-only. The same valid source cells contribute to
    senior and non-senior aggregates. No station/hour cell is treated as an
    independent weather exposure in the confirmatory tables.
    """
    validate_confirmatory_config(config, year)
    _validate_base(base, config, year)
    event = event or config["primary_event"]
    if event not in EVENTS:
        raise ValueError("unsupported confirmatory event")

    valid = base["age_comparison_valid"].fillna(False).astype(bool)
    selected = base.loc[valid & base["boarding_type"].eq(event)].copy()
    if selected.empty:
        raise ValueError("empty confirmatory event sample")
    exposure = _daily_exposure(base, config, year)

    h1_wide = selected.groupby("date", observed=True).agg(
        senior=("senior", "sum"),
        non_senior=("non_senior", "sum"),
        support_cells=("canonical_station_id", "size"),
    ).reset_index()
    h1_wide = h1_wide.merge(exposure, on="date", how="left", validate="one_to_one")
    h1 = _to_age_long(
        h1_wide,
        [
            "date", "support_cells", "temperature_max", "temperature_min",
            "hot_primary", "cold_primary", "hot_sensitivity", "cold_sensitivity",
            "month", "day_of_week",
        ],
    )
    if h1.groupby("date", observed=True)["age_group"].nunique().ne(2).any():
        raise ValueError("H1 requires exactly two age groups per date")

    h2_wide = selected.groupby(["date", "daytime_10_16"], observed=True).agg(
        senior=("senior", "sum"),
        non_senior=("non_senior", "sum"),
        support_cells=("canonical_station_id", "size"),
    ).reset_index()
    daytime_counts = h2_wide.groupby("date", observed=True)["daytime_10_16"].nunique()
    if daytime_counts.ne(2).any():
        raise ValueError("H2 requires daytime and non-daytime support on every date")
    h2_wide["daytime"] = h2_wide["daytime_10_16"].astype("int8")
    h2_wide = h2_wide.drop(columns="daytime_10_16").merge(exposure, on="date", how="left", validate="many_to_one")
    h2 = _to_age_long(
        h2_wide,
        [
            "date", "daytime", "support_cells", "temperature_max", "temperature_min",
            "hot_primary", "cold_primary", "hot_sensitivity", "cold_sensitivity",
            "month", "day_of_week",
        ],
    )
    if h2.groupby("date", observed=True).size().ne(4).any():
        raise ValueError("H2 requires four age/daytime rows per date")

    extreme = exposure[[
        "date", "temperature_max", "temperature_min",
        "hot_primary", "cold_primary", "hot_sensitivity", "cold_sensitivity",
        "month", "day_of_week",
    ]].copy()

    summary = {
        "year": year,
        "event": event,
        "dates": int(extreme["date"].nunique()),
        "h1_rows": int(len(h1)),
        "h2_rows": int(len(h2)),
        "source_valid_event_cells": int(len(selected)),
        "hot_primary_days": int(extreme["hot_primary"].sum()),
        "cold_primary_days": int(extreme["cold_primary"].sum()),
        "hot_sensitivity_days": int(extreme["hot_sensitivity"].sum()),
        "cold_sensitivity_days": int(extreme["cold_sensitivity"].sum()),
        "extreme_threshold_status": "FROZEN_PRE_FIT",
        "model_status": "NOT_FITTED",
    }
    return (
        h1.sort_values(["date", "age_group"]).reset_index(drop=True),
        h2.sort_values(["date", "daytime", "age_group"]).reset_index(drop=True),
        extreme.sort_values("date").reset_index(drop=True),
        summary,
    )

# ---- Gate B model design and inference. Frozen config values are validated above. ----

def _dummy_interactions(frame: pd.DataFrame, x: pd.Series, column: str, prefix: str) -> dict[str, pd.Series]:
    categories = sorted(pd.unique(frame[column]))
    if len(categories) < 2:
        raise ValueError(f"{column} requires at least two levels")
    out: dict[str, pd.Series] = {}
    for level in categories[1:]:
        dummy = frame[column].eq(level).astype(float)
        out[f"{prefix}_{level}"] = x.astype(float) * dummy
    return out


def _date_fe(frame: pd.DataFrame) -> pd.DataFrame:
    labels = frame["date"].dt.strftime("%Y-%m-%d")
    dummies = pd.get_dummies(labels, prefix="date", drop_first=True, dtype=float)
    return dummies


def design_h1(frame: pd.DataFrame, *, hot: str = "hot_primary", cold: str = "cold_primary") -> pd.DataFrame:
    required = {"date", "senior", "month", "day_of_week", hot, cold, "count"}
    if not required.issubset(frame):
        raise ValueError("H1 design schema mismatch")
    x = pd.DataFrame(index=frame.index)
    x["const"] = 1.0
    x = pd.concat([x, _date_fe(frame)], axis=1)
    senior = frame["senior"].astype(float)
    x["senior"] = senior
    for name, series in _dummy_interactions(frame, senior, "month", "senior_x_month").items():
        x[name] = series
    for name, series in _dummy_interactions(frame, senior, "day_of_week", "senior_x_dow").items():
        x[name] = series
    x["senior_x_hot"] = senior * frame[hot].astype(float)
    x["senior_x_cold"] = senior * frame[cold].astype(float)
    return x.astype(float)


def design_h2(frame: pd.DataFrame, *, hot: str = "hot_primary", cold: str = "cold_primary") -> pd.DataFrame:
    required = {"date", "senior", "daytime", "month", "day_of_week", hot, cold, "count"}
    if not required.issubset(frame):
        raise ValueError("H2 design schema mismatch")
    x = pd.DataFrame(index=frame.index)
    x["const"] = 1.0
    x = pd.concat([x, _date_fe(frame)], axis=1)
    senior = frame["senior"].astype(float)
    daytime = frame["daytime"].astype(float)
    x["senior"] = senior
    x["daytime"] = daytime
    x["senior_x_daytime"] = senior * daytime

    for column, short in (("month", "month"), ("day_of_week", "dow")):
        categories = sorted(pd.unique(frame[column]))
        if len(categories) < 2:
            raise ValueError(f"{column} requires at least two levels")
        for level in categories[1:]:
            dummy = frame[column].eq(level).astype(float)
            x[f"senior_x_{short}_{level}"] = senior * dummy
            x[f"daytime_x_{short}_{level}"] = daytime * dummy
            x[f"senior_x_daytime_x_{short}_{level}"] = senior * daytime * dummy

    for label, exposure in (("hot", frame[hot].astype(float)), ("cold", frame[cold].astype(float))):
        x[f"{label}_x_daytime"] = exposure * daytime
        x[f"senior_x_{label}"] = senior * exposure
        x[f"senior_x_{label}_x_daytime"] = senior * exposure * daytime
    return x.astype(float)


def ensure_full_rank(design: pd.DataFrame, name: str) -> None:
    import numpy as np
    matrix = design.to_numpy(dtype=float)
    if not np.isfinite(matrix).all():
        raise ValueError(f"{name} design contains nonfinite values")
    rank = int(np.linalg.matrix_rank(matrix))
    if rank != matrix.shape[1]:
        raise ValueError(f"{name} design rank deficient: rank={rank}, columns={matrix.shape[1]}")


def holm_adjust(pvalues: list[float]) -> list[float]:
    import numpy as np
    p = np.asarray(pvalues, dtype=float)
    if p.ndim != 1 or len(p) == 0 or not np.isfinite(p).all() or ((p < 0) | (p > 1)).any():
        raise ValueError("invalid p-values for Holm adjustment")
    order = np.argsort(p, kind="stable")
    adjusted = np.empty_like(p)
    running = 0.0
    m = len(p)
    for rank, index in enumerate(order):
        candidate = min(1.0, (m - rank) * float(p[index]))
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted.tolist()


def _fit_ppml(frame: pd.DataFrame, design: pd.DataFrame):
    import numpy as np
    import statsmodels.api as sm
    ensure_full_rank(design, "PPML")
    groups = frame["date"]
    if groups.nunique() < 30:
        raise ValueError("insufficient date clusters for confirmatory inference")
    result = sm.GLM(
        frame["count"].astype(float),
        design,
        family=sm.families.Poisson(),
    ).fit(cov_type="cluster", cov_kwds={"groups": groups}, maxiter=200)
    if not bool(getattr(result, "converged", False)):
        raise ValueError("PPML did not converge")
    values = np.r_[result.params.to_numpy(), result.bse.to_numpy(), result.pvalues.to_numpy()]
    if not np.isfinite(values).all():
        raise ValueError("PPML produced nonfinite estimate/covariance")
    return result


def _effect_row(result, term: str, hypothesis: str, model: str, event: str, threshold: str) -> dict[str, object]:
    import math
    if term not in result.params.index:
        raise ValueError(f"missing confirmatory term: {term}")
    estimate = float(result.params[term])
    se = float(result.bse[term])
    p = float(result.pvalues[term])
    low = estimate - 1.959963984540054 * se
    high = estimate + 1.959963984540054 * se
    irr = math.exp(estimate)
    return {
        "model": model,
        "event": event,
        "threshold": threshold,
        "hypothesis": hypothesis,
        "term": term,
        "estimate": estimate,
        "std_error": se,
        "ci95_low": low,
        "ci95_high": high,
        "p_value": p,
        "irr": irr,
        "relative_percent": 100.0 * (irr - 1.0),
        "irr_ci95_low": math.exp(low),
        "irr_ci95_high": math.exp(high),
    }


def _linear_contrast_row(result, terms: list[str], hypothesis: str, model: str, event: str, threshold: str) -> dict[str, object]:
    import math
    import numpy as np
    from scipy.stats import norm
    names = list(result.params.index)
    vector = np.zeros(len(names), dtype=float)
    for term in terms:
        if term not in names:
            raise ValueError(f"missing contrast term: {term}")
        vector[names.index(term)] += 1.0
    estimate = float(vector @ result.params.to_numpy())
    covariance = result.cov_params().to_numpy()
    variance = float(vector @ covariance @ vector)
    if not np.isfinite(variance) or variance < 0:
        raise ValueError("invalid contrast covariance")
    se = math.sqrt(variance)
    z = estimate / se if se > 0 else (math.inf if estimate > 0 else -math.inf if estimate < 0 else 0.0)
    p = float(2.0 * norm.sf(abs(z)))
    low = estimate - 1.959963984540054 * se
    high = estimate + 1.959963984540054 * se
    irr = math.exp(estimate)
    return {
        "model": model,
        "event": event,
        "threshold": threshold,
        "hypothesis": hypothesis,
        "term": " + ".join(terms),
        "estimate": estimate,
        "std_error": se,
        "ci95_low": low,
        "ci95_high": high,
        "p_value": p,
        "irr": irr,
        "relative_percent": 100.0 * (irr - 1.0),
        "irr_ci95_low": math.exp(low),
        "irr_ci95_high": math.exp(high),
    }


def fit_h1_ppml(frame: pd.DataFrame, *, event: str, threshold: str, hot: str, cold: str) -> tuple[pd.DataFrame, dict[str, object]]:
    design = design_h1(frame, hot=hot, cold=cold)
    result = _fit_ppml(frame, design)
    rows = [
        _effect_row(result, "senior_x_hot", "h1_hot_senior_differential", "H1_PPML", event, threshold),
        _effect_row(result, "senior_x_cold", "h1_cold_senior_differential", "H1_PPML", event, threshold),
    ]
    meta = {
        "converged": True,
        "nobs": int(result.nobs),
        "date_clusters": int(frame["date"].nunique()),
        "design_columns": int(design.shape[1]),
        "design_rank": int(__import__("numpy").linalg.matrix_rank(design.to_numpy(dtype=float))),
        "deviance": float(result.deviance),
    }
    return pd.DataFrame(rows), meta


def fit_h2_ppml(frame: pd.DataFrame, *, event: str, threshold: str, hot: str, cold: str) -> tuple[pd.DataFrame, dict[str, object]]:
    design = design_h2(frame, hot=hot, cold=cold)
    result = _fit_ppml(frame, design)
    rows = [
        _effect_row(result, "senior_x_hot_x_daytime", "h2_hot_daytime_amplification", "H2_PPML", event, threshold),
        _effect_row(result, "senior_x_cold_x_daytime", "h2_cold_daytime_amplification", "H2_PPML", event, threshold),
        _linear_contrast_row(
            result,
            ["senior_x_hot", "senior_x_hot_x_daytime"],
            "h2_hot_senior_differential_during_daytime",
            "H2_PPML",
            event,
            threshold,
        ),
        _linear_contrast_row(
            result,
            ["senior_x_cold", "senior_x_cold_x_daytime"],
            "h2_cold_senior_differential_during_daytime",
            "H2_PPML",
            event,
            threshold,
        ),
    ]
    meta = {
        "converged": True,
        "nobs": int(result.nobs),
        "date_clusters": int(frame["date"].nunique()),
        "design_columns": int(design.shape[1]),
        "design_rank": int(__import__("numpy").linalg.matrix_rank(design.to_numpy(dtype=float))),
        "deviance": float(result.deviance),
    }
    return pd.DataFrame(rows), meta


def _benchmark_design(frame: pd.DataFrame) -> pd.DataFrame:
    x = pd.DataFrame(index=frame.index)
    x["const"] = 1.0
    x["hot_primary"] = frame["hot_primary"].astype(float)
    x["cold_primary"] = frame["cold_primary"].astype(float)
    x = pd.concat(
        [
            x,
            pd.get_dummies(frame["month"], prefix="month", drop_first=True, dtype=float),
            pd.get_dummies(frame["day_of_week"], prefix="dow", drop_first=True, dtype=float),
        ],
        axis=1,
    )
    return x.astype(float)


def fit_hac_benchmarks(h1: pd.DataFrame, h2: pd.DataFrame, *, event: str) -> pd.DataFrame:
    import math
    import numpy as np
    import statsmodels.api as sm

    wide = h1.pivot(index="date", columns="age_group", values="count")
    if wide.isna().any().any() or (wide <= 0).any().any():
        raise ValueError("H1 HAC benchmark requires positive paired daily counts; no zero correction allowed")
    covars = h1.drop_duplicates("date").set_index("date")[["hot_primary", "cold_primary", "month", "day_of_week"]]
    h1_daily = covars.join(wide)
    h1_daily["outcome"] = np.log(h1_daily["senior"] / h1_daily["non_senior"])
    x1 = _benchmark_design(h1_daily.reset_index())
    ensure_full_rank(x1, "H1 HAC")
    r1 = sm.OLS(h1_daily["outcome"].to_numpy(dtype=float), x1).fit(cov_type="HAC", cov_kwds={"maxlags": 7})

    pivot = h2.pivot_table(index=["date", "daytime"], columns="age_group", values="count", aggfunc="first")
    if pivot.isna().any().any() or (pivot <= 0).any().any():
        raise ValueError("H2 HAC benchmark requires positive paired daily counts; no zero correction allowed")
    pivot["ratio"] = np.log(pivot["senior"] / pivot["non_senior"])
    delta = pivot["ratio"].unstack("daytime")
    if not {0, 1}.issubset(delta.columns):
        raise ValueError("H2 HAC benchmark missing daytime stratum")
    h2_daily = covars.join((delta[1] - delta[0]).rename("outcome"))
    x2 = _benchmark_design(h2_daily.reset_index())
    ensure_full_rank(x2, "H2 HAC")
    r2 = sm.OLS(h2_daily["outcome"].to_numpy(dtype=float), x2).fit(cov_type="HAC", cov_kwds={"maxlags": 7})

    rows = []
    for model, result in (("H1_HAC_LOG_RATIO", r1), ("H2_HAC_DELTA_LOG_RATIO", r2)):
        for term, hypothesis in (
            ("hot_primary", "hot_primary"),
            ("cold_primary", "cold_primary"),
        ):
            estimate = float(result.params[term])
            se = float(result.bse[term])
            low = estimate - 1.959963984540054 * se
            high = estimate + 1.959963984540054 * se
            rows.append(
                {
                    "model": model,
                    "event": event,
                    "threshold": "p90_p10",
                    "hypothesis": hypothesis,
                    "term": term,
                    "estimate": estimate,
                    "std_error": se,
                    "ci95_low": low,
                    "ci95_high": high,
                    "p_value": float(result.pvalues[term]),
                    "irr": math.exp(estimate),
                    "relative_percent": 100.0 * (math.exp(estimate) - 1.0),
                    "irr_ci95_low": math.exp(low),
                    "irr_ci95_high": math.exp(high),
                }
            )
    return pd.DataFrame(rows)


def fit_confirmatory_models(
    boarding_h1: pd.DataFrame,
    boarding_h2: pd.DataFrame,
    alighting_h1: pd.DataFrame,
    alighting_h2: pd.DataFrame,
) -> tuple[dict[str, pd.DataFrame], dict[str, object]]:
    h1_primary, h1_meta = fit_h1_ppml(
        boarding_h1, event="boarding", threshold="p90_p10", hot="hot_primary", cold="cold_primary"
    )
    h2_primary, h2_meta = fit_h2_ppml(
        boarding_h2, event="boarding", threshold="p90_p10", hot="hot_primary", cold="cold_primary"
    )

    h1_severe, h1_severe_meta = fit_h1_ppml(
        boarding_h1, event="boarding", threshold="p95_p05", hot="hot_sensitivity", cold="cold_sensitivity"
    )
    h2_severe, h2_severe_meta = fit_h2_ppml(
        boarding_h2, event="boarding", threshold="p95_p05", hot="hot_sensitivity", cold="cold_sensitivity"
    )
    h1_alighting, h1_alighting_meta = fit_h1_ppml(
        alighting_h1, event="alighting", threshold="p90_p10", hot="hot_primary", cold="cold_primary"
    )
    h2_alighting, h2_alighting_meta = fit_h2_ppml(
        alighting_h2, event="alighting", threshold="p90_p10", hot="hot_primary", cold="cold_primary"
    )
    hac = fit_hac_benchmarks(boarding_h1, boarding_h2, event="boarding")

    family_names = [
        "h1_hot_senior_differential",
        "h1_cold_senior_differential",
        "h2_hot_daytime_amplification",
        "h2_cold_daytime_amplification",
    ]
    primary_all = pd.concat([h1_primary, h2_primary], ignore_index=True)
    family = primary_all.loc[primary_all["hypothesis"].isin(family_names)].copy()
    family = family.set_index("hypothesis").loc[family_names].reset_index()
    family["holm_p_value"] = holm_adjust(family["p_value"].astype(float).tolist())
    family["alpha"] = 0.05
    family["holm_reject"] = family["holm_p_value"].le(0.05)

    sensitivities = pd.concat(
        [h1_severe, h2_severe, h1_alighting, h2_alighting, hac],
        ignore_index=True,
    )
    metadata = {
        "h1_primary": h1_meta,
        "h2_primary": h2_meta,
        "h1_p95_p05": h1_severe_meta,
        "h2_p95_p05": h2_severe_meta,
        "h1_alighting": h1_alighting_meta,
        "h2_alighting": h2_alighting_meta,
        "all_ppml_converged": all(
            item["converged"]
            for item in [
                h1_meta, h2_meta, h1_severe_meta, h2_severe_meta,
                h1_alighting_meta, h2_alighting_meta,
            ]
        ),
    }
    return {
        "h1_primary_results.csv": h1_primary,
        "h2_primary_results.csv": h2_primary,
        "confirmatory_sensitivity_results.csv": sensitivities,
        "confirmatory_test_family.csv": family,
    }, metadata
