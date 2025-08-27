from enum import Enum
import json
import logging
from pathlib import Path
from typing import Iterable, Iterator

import pandas as pd

from .utils import staticproperty


_logger = logging.getLogger(__name__)


class Side(Enum):
    LEFT = "L"
    RIGHT = "R"
    HEMISIDE = "Hemiside"
    HEALTHY = "Healthy"

    @staticproperty
    def sided_names() -> tuple["Side"]:
        return (Side.LEFT, Side.RIGHT)

    @staticproperty
    def condition_names() -> tuple["Side"]:
        return (Side.HEMISIDE, Side.HEALTHY)

    @classmethod
    def from_string(cls, label: str) -> "Side":
        for side in Side:
            if side.value == label:
                return side
        raise ValueError(f"Unknown side: {label}")

    @property
    def graph_color_qualifier(self) -> str:
        qualifiers = {
            Side.LEFT: "dark",
            Side.RIGHT: "light",
            Side.HEMISIDE: "dark",
            Side.HEALTHY: "light",
        }
        return qualifiers.get(self)

    @property
    def graph_name(self) -> str:
        names = {
            Side.LEFT: "Left",
            Side.RIGHT: "Right",
            Side.HEMISIDE: "Hemiside",
            Side.HEALTHY: "Healthy",
        }
        return names.get(self)


class ActivityType(Enum):
    AVG = "AVG"
    TRADITIONAL = "Trad"

    @classmethod
    def from_string(cls, label: str) -> "ActivityType":
        for activity_type in cls:
            if activity_type.value == label:
                return activity_type
        raise ValueError(f"Unknown activity type: {label}")

    @property
    def graph_color(self) -> str:
        colors = {
            ActivityType.AVG: "blue",
            ActivityType.TRADITIONAL: "green",
        }
        return colors.get(self)

    @property
    def graph_name(self) -> str:
        names = {
            ActivityType.AVG: "AVG",
            ActivityType.TRADITIONAL: "Traditionnel",
        }
        return names.get(self)


def _read_file(
    folder: Path,
    file_type: str,
) -> pd.DataFrame:
    # Find the full file path collapsing the wildcard
    file_path = list(folder.glob(f"*_{file_type}.csv"))
    if not file_path:
        message = f"No files found for pattern: {file_type}"
        _logger.error(message)
        raise FileNotFoundError(message)
    if len(file_path) > 1:
        message = f"Multiple files found for pattern: {file_type}"
        _logger.error(message)
        raise FileExistsError(message)

    return pd.read_csv(file_path[0])


class Data:
    def __init__(self, data_folder: Path, timings: list[tuple[str]]):
        # Read all the relevant data files
        self._activity_counts = _read_file(folder=data_folder, file_type="activity-counts")
        self._pulse_rate = _read_file(folder=data_folder, file_type="pulse-rate")

        # Find the rows to keep
        self._mask = self._activity_counts["timestamp_unix"] < 0  # Set all to False
        for timing in timings:
            start, end = timing
            self._mask |= (self._activity_counts["timestamp_unix"] >= start) & (
                self._activity_counts["timestamp_unix"] <= end
            )

    @property
    def activity_counts(self) -> pd.DataFrame:
        return self._activity_counts.loc[self._mask, ["timestamp_unix", "activity_counts"]]

    @property
    def pulse_rate(self) -> pd.DataFrame:
        return self._pulse_rate.loc[self._mask, ["timestamp_unix", "pulse_rate_bpm"]]


class TheramiData:
    def __init__(self, data: dict):
        self._data = data

    @classmethod
    def from_json(cls, file_dispatcher_path: Path) -> "TheramiData":
        base_data_folder = file_dispatcher_path.parent
        with open(file_dispatcher_path) as f:
            subjects: dict[str, dict] = json.load(f)

        activity_names: list[str] = None
        data = {}
        for subject_name in subjects.keys():
            _logger.info(f"Processing subject: {subject_name}")
            subject = subjects[subject_name]

            data[subject_name] = {}
            hemiside = subject["hemiside"]
            if hemiside not in ("L", "R"):
                message = f"Invalid hemiside value for subject: {subject_name}"
                _logger.error(message)
                raise ValueError(message)

            for side in Side:
                _logger.debug(f"  Processing side: {side}")
                data[subject_name][side] = {}

                activities: dict[str, dict] = subject["activities"]
                if activity_names is None:
                    activity_names = sorted(list(activities.keys()))
                else:
                    if activity_names != sorted(list(activities.keys())):
                        message = f"Activity names do not match for subject: {subject_name}, side: {side}"
                        _logger.error(message)
                        raise ValueError(message)

                for activity in activities.keys():
                    _logger.debug(f"    Processing activity: {activity}")
                    data[subject_name][side][activity] = {}

                    activity_types: dict[str, dict] = activities[activity]
                    if sorted(activity_types.keys()) != sorted([activity.value for activity in ActivityType]):
                        _logger.error(
                            f"Activity types do not match for subject: {subject_name}, side: {side}, activity: {activity}"
                        )

                    for activity_type in activity_types.keys():
                        _logger.debug(f"      Processing activity type: {activity_type}")
                        activity_metadata = activity_types[activity_type]

                        activity_type = ActivityType.from_string(activity_type)
                        side_value = side.value
                        if side == Side.HEMISIDE:
                            side_value = hemiside
                        elif side == Side.HEALTHY:
                            side_value = "R" if hemiside == "L" else "L"

                        data_folder: Path = base_data_folder / activity_metadata["data_folder"].replace("*", side_value)
                        if not data_folder.exists():
                            message = f"Data folder does not exist: {data_folder}"
                            _logger.error(message)
                            raise FileNotFoundError(message)

                        # Extract the date from the file_path which is the last folder in data_folder
                        date = data_folder.name
                        timings = []
                        for timing in activity_metadata["data"]:
                            start = f"{date}T{timing['start'].replace('::', ':')}Z"
                            start = pd.to_datetime(start).value // 10**6
                            end = f"{date}T{timing['end'].replace('::', ':')}Z"
                            end = pd.to_datetime(end).value // 10**6
                            timings.append((start, end))

                        data[subject_name][side][activity][activity_type] = Data(
                            data_folder=data_folder, timings=timings
                        )
        return cls(data=data)

    @property
    def subjects(self) -> tuple[str, ...]:
        return tuple(self._data.keys())

    @property
    def sides(self) -> tuple[Side, ...]:
        return tuple(self._data[self.subjects[0]].keys())

    @property
    def activities(self) -> tuple[str, ...]:
        return tuple(self._data[self.subjects[0]][self.sides[0]].keys())

    @property
    def activity_types(self) -> tuple[ActivityType, ...]:
        return tuple(self._data[self.subjects[0]][self.sides[0]][self.activities[0]].keys())

    def filter(
        self,
        subjects: str | Iterable[str] = None,
        sides: Side | Iterable[Side] = None,
        activities: str | Iterable[str] = None,
        activity_types: ActivityType | Iterable[ActivityType] = None,
    ) -> "TheramiData":
        if isinstance(subjects, str):
            subjects = [subjects]
        if isinstance(sides, Side):
            sides = [sides]
        if isinstance(activities, str):
            activities = [activities]
        if isinstance(activity_types, ActivityType):
            activity_types = [activity_types]

        data = {}
        for subject_name in self.subjects if subjects is None else subjects:
            data[subject_name] = {}
            for side in self.sides if sides is None else sides:
                data[subject_name][side] = {}
                for activity in self.activities if activities is None else activities:
                    data[subject_name][side][activity] = {}
                    for activity_type in self.activity_types if activity_types is None else activity_types:
                        data[subject_name][side][activity][activity_type] = self._data[subject_name][side][activity][
                            activity_type
                        ]
        return TheramiData(data=data)

    def __getitem__(self, keys: dict[str, Side, str, ActivityType]) -> Data:
        subject = keys["subject"]
        side = keys["side"]
        activity = keys["activity"]
        activity_type = keys["activity_type"]
        return self._data[subject][side][activity][activity_type]

    def get(self, subject: str, side: Side, activity: str, activity_type: ActivityType) -> Data:
        return self[{"subject": subject, "side": side, "activity": activity, "activity_type": activity_type}]

    # Implement the for loop on the class
    def __iter__(self) -> Iterator[dict]:
        for subject in self.subjects:
            for side in self.sides:
                for activity in self.activities:
                    for activity_type in self.activity_types:
                        yield {
                            "subject": subject,
                            "side": side,
                            "activity": activity,
                            "activity_type": activity_type,
                        }

    def activity_counts_boxplot(self, save_path: Path | None):
        from .plotter import Plotter

        Plotter.activity_counts_boxplot(data=self, save_path=save_path)

    def to_csv(self, save_path: Path) -> None:
        from .exporter import Exporter

        Exporter.to_csv(data=self, save_path=save_path)
