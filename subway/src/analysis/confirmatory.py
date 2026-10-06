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
