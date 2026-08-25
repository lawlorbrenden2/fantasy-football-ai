from pathlib import Path
from core.config_parser import (
    ScoringSettings, 
    RosterSettings, 
    LeagueConfig, 
    save_league_config
)

def create_league_config() -> Path:
    print("\n--- 🏈 League Configuration Setup ---")
    name = input("Enter League name (e.g., Weezer League): ".strip() or "Custom League")
    team_count = int(input("Enter number of teams (default 12): ") or 12)
    ppr = float(input("Enter PPR value (default 1.0): ") or 1.0)
    pass_td = int(input("Enter point value for a pass TD (default 4): ") or 4)
    rush_td = int(input("Enter point value for a rush TD (default 6): ") or 6)
    reception_td = int(input("Enter point value for a pass catch TD (default 6): ") or 6)

    qb = int(input("Enter number of starting QBs (default 1): ") or 1)
    rb = int(input("Enter number of starting RBs (default 2): ") or 2)
    wr = int(input("Enter number of starting WRs (default 2): ") or 2)
    te = int(input("Enter number of starting TEs (default 1): ") or 1)
    flex = int(input("Enter number of starting flex players (default 1): ") or 1)
    dst = int(input("Enter number of starting D/STs (default 1): ") or 1)
    k = int(input("Enter number of starting Kickers (default 1): ") or 1)
    bench = int(input("Enter number of bench players (default 6): ") or 7)
    ir = int(input("Enter number of potential IR players (default 0): ") or 0)

    config = LeagueConfig(
        league_name=name,
        team_count=team_count,
        scoring=ScoringSettings(ppr=ppr, pass_td=pass_td, rush_td=rush_td, reception_td=reception_td),
        roster_limits=RosterSettings(qb=qb, rb=rb, wr=wr, te=te, flex=flex, dst=dst, k=k, bench=bench, ir=ir)
    )

    saved_path = save_league_config(config)
    print(f"Configuration saved to {saved_path}")
    return saved_path