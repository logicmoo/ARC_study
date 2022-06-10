import dataclasses


@dataclasses.dataclass
class Settings:
    N: int = 400
    folder: str = "data/training"
    pickle_id: str = "demo_run"
    grid_width: int = 10
