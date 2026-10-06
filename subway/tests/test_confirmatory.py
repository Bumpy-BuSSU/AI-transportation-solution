from pathlib import Path
from tempfile import TemporaryDirectory
import copy
import unittest

import numpy as np
import pandas as pd
import yaml

from subway.src.analysis.confirmatory import (
    DAYTIME_BINS,
    build_confirmatory_tables,
    load_confirmatory_config,
    validate_confirmatory_config,
)
from subway.src.transform.ridership import HOURS


ROOT = Path(__file__).resolve().parents[2]


def synthetic_base() -> pd.DataFrame:
    rows = []
    dates = [
        (pd.Timestamp("2024-01-01"), 34.0, 5.0),
        (pd.Timestamp("2024-01-02"), 5.0, -5.0),
    ]
    for date, tmax, tmin in dates:
        for station in ("s1", "s2"):
            for hour in HOURS:
                for event in ("boarding", "alighting"):
                    senior = 10
                    total = 100
                    valid = True
                    non_senior = 90.0
                    if (
                        date == pd.Timestamp("2024-01-01")
                        and station == "s1"
                        and hour == "10_11"
                        and event == "boarding"
                    ):
                        senior = 101
                        total = 100
                        valid = False
                        non_senior = np.nan
                    rows.append(
                        dict(
                            date=date,
                            canonical_station_id=station,
                            hour_bin=hour,
                            boarding_type=event,
                            senior=senior,
                            total=total,
                            non_senior=non_senior,
                            senior_share=(senior / total if valid and total else np.nan),
                            age_comparison_valid=valid,
                            daytime_10_16=hour in DAYTIME_BINS,
                            temperature_max=tmax,
                            temperature_min=tmin,
                        )
                    )
    return pd.DataFrame(rows)


class ConfirmatorySpecificationTests(unittest.TestCase):
    def setUp(self):
        self.config = load_confirmatory_config(ROOT, 2024)

    def test_frozen_config_exact_thresholds_event_and_daytime(self):
        self.assertEqual(self.config["primary_event"], "boarding")
        self.assertEqual(self.config["daytime"]["bins"], DAYTIME_BINS)
        self.assertEqual(self.config["hot_primary"]["threshold_c"], 32.75)
        self.assertEqual(self.config["cold_primary"]["threshold_c"], -3.05)
        self.assertEqual(self.config["hot_sensitivity"]["threshold_c"], 33.675)
        self.assertEqual(self.config["cold_sensitivity"]["threshold_c"], -4.8)
        self.assertEqual(self.config["multiple_testing"]["method"], "holm")

    def test_config_drift_fails_closed(self):
        changed = copy.deepcopy(self.config)
        changed["hot_primary"]["threshold_c"] = 33.0
        with self.assertRaises(ValueError):
            validate_confirmatory_config(changed, 2024)

    def test_primary_boarding_and_common_valid_support(self):
        base = synthetic_base()
        original = base.copy(deep=True)
        h1, h2, extreme, summary = build_confirmatory_tables(base, self.config, 2024)

        self.assertTrue(base.equals(original))
        self.assertEqual(summary["event"], "boarding")
        self.assertEqual(summary["dates"], 2)
        self.assertEqual(len(h1), 4)
        self.assertEqual(len(h2), 8)

        day1 = h1.loc[h1.date.eq(pd.Timestamp("2024-01-01"))].set_index("age_group")
        # 2 stations * 20 boarding intervals = 40 common cells, one invalid cell removed from BOTH groups.
        self.assertEqual(day1.loc["senior", "support_cells"], 39)
        self.assertEqual(day1.loc["non_senior", "support_cells"], 39)
        self.assertEqual(day1.loc["senior", "count"], 390)
        self.assertEqual(day1.loc["non_senior", "count"], 3510)

    def test_alighting_sensitivity_uses_same_frozen_rules(self):
        h1, h2, _, summary = build_confirmatory_tables(synthetic_base(), self.config, 2024, event="alighting")
        self.assertEqual(summary["event"], "alighting")
        self.assertEqual(len(h1), 4)
        self.assertEqual(len(h2), 8)
        day1 = h1.loc[h1.date.eq(pd.Timestamp("2024-01-01"))].set_index("age_group")
        self.assertEqual(day1.loc["senior", "count"], 400)
        self.assertEqual(day1.loc["non_senior", "count"], 3600)

    def test_extreme_flags_are_weather_only_and_nonoverlapping(self):
        _, _, extreme, summary = build_confirmatory_tables(synthetic_base(), self.config, 2024)
        self.assertEqual(summary["hot_primary_days"], 1)
        self.assertEqual(summary["cold_primary_days"], 1)
        self.assertFalse((extreme.hot_primary & extreme.cold_primary).any())
        self.assertTrue(extreme.loc[0, "hot_primary"])
        self.assertTrue(extreme.loc[1, "cold_primary"])

    def test_exact_daytime_flag_is_enforced(self):
        base = synthetic_base()
        index = base.index[base.hour_bin.eq("10_11")][0]
        base.loc[index, "daytime_10_16"] = False
        with self.assertRaises(ValueError):
            build_confirmatory_tables(base, self.config, 2024)

    def test_weather_must_be_constant_within_date(self):
        base = synthetic_base()
        base.loc[0, "temperature_max"] = 35.0
        with self.assertRaises(ValueError):
            build_confirmatory_tables(base, self.config, 2024)

    def test_unknown_event_rejected(self):
        with self.assertRaises(ValueError):
            build_confirmatory_tables(synthetic_base(), self.config, 2024, event="combined")


if __name__ == "__main__":
    unittest.main()
