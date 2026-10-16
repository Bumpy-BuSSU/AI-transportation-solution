from dataclasses import dataclass

import pandas as pd

from subway.src.validate.raw_validation import Finding


@dataclass
class StageResult:
    frame: pd.DataFrame
    findings: list[Finding]
    exceptions: pd.DataFrame
