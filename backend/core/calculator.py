import pandas as pd
import nflreadpy as nfl
from core.config_parser import LeagueConfig
from pydantic import BaseModel, Field

class BiasSettings(BaseModel):
    strategy: str = "1"
    homer_team: str | None = None
    sleepers: list[str] = Field(default_factory=list)
    busts: list[str] = Field(default_factory=list)
    enable_stacking: bool = False

def apply_draft_strategy(df: pd.DataFrame, settings: BiasSettings) -> pd.DataFrame:
    """Injects custom positional strategies, team biases, and specific player adjustments."""
    df['adjusted_ecr'] = df['ecr']

    if settings.homer_team:
        df.loc[df['team'] == settings.homer_team, 'adjusted_ecr'] -= 3.0

    if settings.sleepers:
        df.loc[df['player'].isin(settings.sleepers), 'adjusted_ecr'] -= 15.0

    if settings.busts:
        df.loc[df['player'].isin(settings.busts), 'adjusted_ecr'] += 30.0

    if settings.strategy == "2":  # Zero-RB
        df.loc[(df['pos'] == 'RB') & (df['ecr'] <= 25), 'adjusted_ecr'] += 40.0
        df.loc[df['pos'].isin(['WR', 'TE']), 'adjusted_ecr'] -= 3.0
    elif settings.strategy == "3":  # Hero-RB
        df.loc[(df['pos'] == 'RB') & (df['ecr'] <= 7), 'adjusted_ecr'] -= 3.0
        df.loc[(df['pos'] == 'RB') & (df['ecr'] > 10) & (df['ecr'] <= 30), 'adjusted_ecr'] += 25.0
    elif settings.strategy == "4":  # Late-Round QB
        df.loc[(df['pos'] == 'QB') & (df['ecr'] <= 12), 'adjusted_ecr'] += 25.0

    return df.sort_values(by='adjusted_ecr').reset_index(drop=True)

def apply_stacking_bias(df: pd.DataFrame, my_roster: list[dict], stack_boost: float = 6.0) -> pd.DataFrame:
    """Dynamically boosts teammates of players already on your roster."""
    if not my_roster:
        return df

    # Find the teams of players you've already drafted
    my_qb_teams = {p['team'] for p in my_roster if p['pos'] == 'QB'}
    my_pass_catcher_teams = {p['team'] for p in my_roster if p['pos'] in ['WR', 'TE']}

    # If we have a QB, boost all their pass-catchers
    for team in my_qb_teams:
        mask = (df['team'] == team) & (df['pos'].isin(['WR', 'TE']))
        df.loc[mask, 'adjusted_ecr'] -= stack_boost

    # If we don't have a QB yet, boost QBs that stack with our WRs/TEs
    if not my_qb_teams:
        for team in my_pass_catcher_teams:
            mask = (df['team'] == team) & (df['pos'] == 'QB')
            df.loc[mask, 'adjusted_ecr'] -= stack_boost

    return df.sort_values(by='adjusted_ecr').reset_index(drop=True)

def fetch_and_clean_rankings() -> pd.DataFrame:
    """Fetches and isolates the PPR positional consensus sheets."""
    print("Downloading latest nflverse rankings...")
    rankings_pl = nfl.load_ff_rankings()
    df = rankings_pl.to_pandas()
    
    ppr_df = df[df['ecr_type'] == 'rp'].copy()
    core_pages = ['redraft-qb', 'redraft-rb', 'redraft-wr', 'redraft-te']
    ppr_core_df = ppr_df[ppr_df['page_type'].isin(core_pages)].copy()
    
    return ppr_core_df.dropna(subset=['ecr'])

def calculate_vorp(config: LeagueConfig, strategy: BiasSettings) -> pd.DataFrame:
    """Calculates Value Over Replacement Rank (VORR)."""
    df = fetch_and_clean_rankings()
    df = apply_draft_strategy(df, strategy)
    
    teams = config.team_count
    limits = config.roster_limits
    
    # Estimate FLEX split (assuming 50/50 RB/WR)
    flex_rb = int(limits.flex / 2)
    flex_wr = limits.flex - flex_rb
    
    starters = {
        'QB': teams * limits.qb,
        'RB': teams * (limits.rb + flex_rb),
        'WR': teams * (limits.wr + flex_wr),
        'TE': teams * limits.te
    }
    
    # Find baseline replacement player
    baselines = {}
    for pos, count in starters.items():
        pos_df = df[df['pos'] == pos]
        if len(pos_df) > count:
            replacement_ecr = pos_df.iloc[count]['adjusted_ecr']
        else:
            replacement_ecr = pos_df['adjusted_ecr'].max()
        baselines[pos] = replacement_ecr
        
    # VORP Formula: Baseline Rank - Player Rank
    df['vorp_value'] = df.apply(lambda row: baselines[row['pos']] - row['adjusted_ecr'], axis=1)
    
    return df.sort_values(by='vorp_value', ascending=False).reset_index(drop=True)