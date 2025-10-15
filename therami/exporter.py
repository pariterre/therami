import logging
from pathlib import Path

import pandas as pd

from .data import TheramiData, Side

_logger = logging.getLogger(__name__)


class Exporter:
    @staticmethod
    def to_csv(data: TheramiData, save_folder: Path):
        # Summary statistics
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

        summary_statistics_path = save_folder / "summary_statistics.csv"
        summary_statistics_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(summary_statistics_path, index=False)
        _logger.info(f"Saved CSV to {summary_statistics_path}")

        # Bimanual statistics
        header = [
            "Subject",
            "Activity",
            "Activity type",
            "Activity counts bimanual index",
        ]
        rows = []
        for keys in data:
            if keys["side"] != Side.HEMISIDE:
                continue
            tp_hemi = data[keys]
            keys["side"] = Side.HEALTHY
            tp_healthy = data[keys]
            row = [
                keys["subject"],
                keys["activity"],
                keys["activity_type"].graph_name,
                tp_hemi.activity_counts["activity_counts"].mean()
                / tp_healthy.activity_counts["activity_counts"].mean(),
            ]
            rows.append(row)
        df = pd.DataFrame(rows, columns=header)
        df = df.round(3)  # Precision to 1 decimal places

        bimanual_statistics_path = save_folder / "bimanual_statistics.csv"
        bimanual_statistics_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(bimanual_statistics_path, index=False)
        _logger.info(f"Saved CSV to {bimanual_statistics_path}")
