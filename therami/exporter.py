import logging
from pathlib import Path

import pandas as pd

from .data import TheramiData

_logger = logging.getLogger(__name__)


class Exporter:
    @staticmethod
    def to_csv(data: TheramiData, save_path: Path):
        header = [
            "Subject",
            "Side",
            "Activity",
            "Activity type",
            "Activity counts mean",
            "Activity counts std",
            "Pulse rate mean",
            "Pulse rate std",
        ]

        rows = []
        for keys in data:
            tp = data[keys]
            row = [
                keys["subject"],
                keys["side"].graph_name,
                keys["activity"],
                keys["activity_type"].graph_name,
                tp.activity_counts["activity_counts"].mean(),
                tp.activity_counts["activity_counts"].std(),
                tp.pulse_rate["pulse_rate_bpm"].mean(),
                tp.pulse_rate["pulse_rate_bpm"].std(),
            ]
            rows.append(row)
        df = pd.DataFrame(rows, columns=header)
        df = df.round(1)  # Precision to 1 decimal places

        save_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(save_path, index=False)

        _logger.info(f"Saved CSV to {save_path}")
