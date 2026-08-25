import yaml
from pathlib import Path
from pydantic import BaseModel

class ScoringSettings(BaseModel):
    ppr: float = 1.0
    pass_td: int = 4
    rush_td: int = 6
    reception_td: int = 6

class RosterSettings(BaseModel):
    qb: int = 1
    rb: int = 2
    wr: int = 2
    te: int = 1
    flex: int = 1
    dst: int = 1
    k: int = 1
    bench: int = 7
    ir: int = 0

class LeagueConfig(BaseModel):
    league_name: str
    team_count: int = 12
    scoring: ScoringSettings = ScoringSettings()
    roster_limits: RosterSettings = RosterSettings()

def load_league_config(filepath: str) -> LeagueConfig:
    with open(filepath, 'r') as f:
        raw_data =  yaml.safe_load(f)
    return LeagueConfig(**raw_data)

def save_league_config(config: LeagueConfig, output_dir: str | Path = 'backend/configs') -> Path:
    output_path = Path(output_dir) / f"{config.league_name.lower().replace(' ', '_')}.yaml"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        yaml.safe_dump(config.model_dump(), f, sort_keys=False)

    return output_path