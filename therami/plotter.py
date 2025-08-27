from itertools import product
import logging
from pathlib import Path
from typing import Callable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data import TheramiData, Side, Data

_logger = logging.getLogger(__name__)


class Plotter:
    @staticmethod
    def activity_counts_boxplot(data: TheramiData, save_path: Path | None):
        fig = Plotter._boxplot(
            data=data,
            extract_data_callback=lambda activity_data: [
                data.activity_counts["activity_counts"] for data in activity_data
            ],
            title="Activity counts",
        )
        if save_path is not None:
            fig.savefig(save_path)
            _logger.info(f"Saved activity counts boxplot to {save_path}")
        plt.show()

    @staticmethod
    def pulse_rate_boxplot(data: TheramiData, save_path: Path | None):
        fig = Plotter._boxplot(
            data=data,
            extract_data_callback=lambda activity_data: [data.pulse_rate["pulse_rate_bpm"] for data in activity_data],
            title="Pulse rate",
        )
        if save_path is not None:
            fig.savefig(save_path)
            _logger.info(f"Saved pulse rate boxplot to {save_path}")
        plt.show()

    @staticmethod
    def _boxplot(data: TheramiData, extract_data_callback: Callable[[list[Data]], list[pd.DataFrame]], title: str):
        if len(data.subjects) > 1:
            raise NotImplementedError("Box plot for multiple subjects is not implemented yet.")
        subject = data.subjects[0]

        groups = tuple(product(data.activity_types, data.sides))
        group_count = len(groups)
        activity_count = len(data.activities)

        if Side.LEFT in data.sides or Side.RIGHT in data.sides:
            if Side.HEMISIDE in data.sides or Side.HEALTHY in data.sides:
                message = "Cannot mix LEFT/RIGHT with HEMISIDE/HEALTHY sides."
                _logger.error(message)
                raise ValueError(message)
        if Side.HEMISIDE in data.sides or Side.HEALTHY in data.sides:
            if Side.LEFT in data.sides or Side.RIGHT in data.sides:
                message = "Cannot mix HEMISIDE/HEALTHY with LEFT/RIGHT sides."
                _logger.error(message)
                raise ValueError(message)

        # --- Plot setup ---
        fig, ax = plt.subplots(figsize=(10 * 1.5, 6 * 1.5))

        # Get the data for all combinations of sides and activity_types
        horizontal_spacing = 0.6
        boxplots = []
        boxplot_names = []
        for i, (activity_type, side) in enumerate(groups):
            group_positions = np.arange(activity_count) * group_count + i * horizontal_spacing

            activity_data = [
                data.get(subject=subject, side=side, activity=act, activity_type=activity_type)
                for act in data.activities
            ]
            boxplots.append(
                ax.boxplot(
                    extract_data_callback(activity_data),
                    positions=group_positions,
                    widths=0.5,
                    patch_artist=True,
                    boxprops=dict(facecolor=f"{side.graph_color_qualifier}{activity_type.graph_color}"),
                )
            )
            boxplot_names.append(f"{side.graph_name} {activity_type.graph_name}")

        # x-ticks in the middle of each pair
        ax.set_xticks(group_positions)
        ax.set_xticklabels(data.activities, rotation=-10)

        # Labels, legend, title
        ax.set_ylabel(title)
        ax.set_title(f"{title} by activity type and side")
        ax.legend([bp["boxes"][0] for bp in boxplots], boxplot_names, loc="lower right")

        plt.tight_layout()
        return fig
