import logging
import os
from pathlib import Path

import therami


def main():
    logging.basicConfig(level=logging.INFO)

    data_folder = os.getenv("THERAMI_DATA_FOLDER")
    if data_folder is None:
        raise ValueError("THERAMI_DATA_FOLDER environment variable is not set")
    data_folder = Path(data_folder)

    data = therami.TheramiData.from_json(file_dispatcher_path=data_folder / "all_data.json")
    data.to_csv(save_path=Path("results/all_data.csv"))
    data.filter(sides=therami.Side.sided_names).activity_counts_boxplot(save_path=Path("results/activity_counts.png"))


if __name__ == "__main__":
    main()
