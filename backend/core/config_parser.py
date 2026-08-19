import yaml
from pydantic import BaseModel

class ScoringSettings(BaseModel):
    ppr: float = 1.0
    pass_td: int = 4
    rush_td: int = 6

class RosterSettings(BaseModel):
    qb: int = 1
    rb: int = 2
    wr: int = 2
    te: int = 1
    flex: int = 1
    dst: int = 1
    k: int = 1
    bench: int = 6
    ir: int = 1

class LeagueConfig(BaseModel):
    league_name: str
    team_count: int = 12
    scoring: ScoringSettings = ScoringSettings()
    roster_limits: RosterSettings = RosterSettings()

def load_league_config(filepath: str) -> LeagueConfig:
    with open(filepath, 'r') as f:
        raw_data =  yaml.safe_load(f)
    return LeagueConfig(**raw_data)