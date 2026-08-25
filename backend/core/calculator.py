import pandas as pd
import nflreadpy as nfl
from pydantic import BaseModel, Field
from core.config_parser import LeagueConfig

class BiasSettings(BaseModel):
    strategy: str = "1"
    homer_team: str | None = None
    sleepers: list[str] = Field(default_factory=list)
    busts: list[str] = Field(default_factory=list)
    enable_stacking: bool = False

# Map common non-standard abbreviations to official nflverse codes
TEAM_ALIASES = {
    'AZ': 'ARI',
    'ARZ': 'ARI',
    'WSH': 'WAS',
    'OAK': 'LV',
    'SD': 'LAC',
    'JAX': 'JAC',
    'GBP': 'GB',
    'KCC': 'KC',
    'NEP': 'NE',
    'NOS': 'NO',
    'SFO': 'SF',
    'TBB': 'TB'
}

def apply_draft_strategy(df: pd.DataFrame, settings: BiasSettings) -> tuple[pd.DataFrame, list[str]]:
    """
    Injects custom strategies and biases, returning both the adjusted DataFrame 
    and an audit log confirming what matched or failed.
    """
    df['adjusted_ecr'] = df['ecr'].astype(float)
    audit_logs = []
    
    # Clean available lists
    db_players_lower = {p.lower(): p for p in df['player'].dropna().unique()}
    valid_teams = set(df['team'].dropna().unique())
    
    # 1. Homer Team Bias
    if settings.homer_team:
        team_clean = settings.homer_team.strip().upper()
        resolved_team = TEAM_ALIASES.get(team_clean, team_clean)
        
        if resolved_team in valid_teams:
            mask = df['team'] == resolved_team
            count = mask.sum()
            df.loc[mask, 'adjusted_ecr'] -= 3.0
            alias_note = f" (mapped from '{team_clean}')" if team_clean != resolved_team else ""
            audit_logs.append(f"✅ Team Boost: Applied -3.0 rank boost to {count} players on {resolved_team}{alias_note}")
        else:
            audit_logs.append(f"⚠️ Team Warning: '{team_clean}' not found in database. No team boost applied.")

    # 2. Sleepers (Case-Insensitive Match)
    clean_sleepers = [s.strip() for s in settings.sleepers if s.strip()]
    for sleeper in clean_sleepers:
        match_key = sleeper.lower()
        if match_key in db_players_lower:
            actual_name = db_players_lower[match_key]
            orig_ecr = df.loc[df['player'] == actual_name, 'adjusted_ecr'].values[0]
            df.loc[df['player'] == actual_name, 'adjusted_ecr'] -= 15.0
            new_ecr = df.loc[df['player'] == actual_name, 'adjusted_ecr'].values[0]
            audit_logs.append(f"Sleeper Boost: {actual_name} shifted #{orig_ecr:.1f} ➔ #{new_ecr:.1f}")
        else:
            audit_logs.append(f"Sleeper Warning: Player '{sleeper}' not found in rankings.")

    # 3. Busts (Case-Insensitive Match)
    clean_busts = [b.strip() for b in settings.busts if b.strip()]
    for bust in clean_busts:
        match_key = bust.lower()
        if match_key in db_players_lower:
            actual_name = db_players_lower[match_key]
            orig_ecr = df.loc[df['player'] == actual_name, 'adjusted_ecr'].values[0]
            df.loc[df['player'] == actual_name, 'adjusted_ecr'] += 30.0
            new_ecr = df.loc[df['player'] == actual_name, 'adjusted_ecr'].values[0]
            audit_logs.append(f"🔻 Bust Penalty: {actual_name} shifted #{orig_ecr:.1f} ➔ #{new_ecr:.1f}")
        else:
            audit_logs.append(f"⚠️ Bust Warning: Player '{bust}' not found in rankings.")

    # 4. Strategy Rules
    if settings.strategy == "2":  # Zero-RB
        df.loc[(df['pos'] == 'RB') & (df['ecr'] <= 25), 'adjusted_ecr'] += 40.0
        df.loc[df['pos'].isin(['WR', 'TE']), 'adjusted_ecr'] -= 3.0
        audit_logs.append("⚙️ Strategy: Zero-RB applied (Top 25 RBs penalized +40, WR/TE boosted -3)")
    elif settings.strategy == "3":  # Hero-RB
        df.loc[(df['pos'] == 'RB') & (df['ecr'] <= 7), 'adjusted_ecr'] -= 3.0
        df.loc[(df['pos'] == 'RB') & (df['ecr'] > 10) & (df['ecr'] <= 30), 'adjusted_ecr'] += 25.0
        audit_logs.append("⚙️ Strategy: Hero-RB applied (Tier-1 RBs boosted -3, RB Dead Zone penalized +25)")
    elif settings.strategy == "4":  # Late-Round QB
        df.loc[(df['pos'] == 'QB') & (df['ecr'] <= 12), 'adjusted_ecr'] += 25.0
        audit_logs.append("⚙️ Strategy: Late-Round QB applied (Top 12 QBs penalized +25)")

    return df.sort_values(by='adjusted_ecr').reset_index(drop=True), audit_logs

def fetch_and_clean_rankings() -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fetches consensus rankings.
    Returns:
      - offensive_df: QB, RB, WR, TE rankings
      - special_teams_df: DST and K rankings
    """
    print("Downloading latest nflverse rankings...")
    rankings_pl = nfl.load_ff_rankings()
    df = rankings_pl.to_pandas()
    
    ppr_df = df[df['ecr_type'] == 'rp'].copy()
    
    # Core offensive skill positions
    core_pages = ['redraft-qb', 'redraft-rb', 'redraft-wr', 'redraft-te']
    offensive_df = ppr_df[ppr_df['page_type'].isin(core_pages)].dropna(subset=['ecr']).copy()
    
    # D/ST
    st_pages = ['redraft-dst', 'redraft-k']
    special_teams_df = ppr_df[ppr_df['page_type'].isin(st_pages)].dropna(subset=['ecr']).copy()
    
    return offensive_df, special_teams_df

def calculate_vorp(config: LeagueConfig, strategy: BiasSettings) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Calculates VORP factoring in starters, 3-way FLEX, and bench depth."""
    offensive_df, st_df = fetch_and_clean_rankings()
    df, audit_logs = apply_draft_strategy(offensive_df, strategy)
    
    teams = config.team_count
    limits = config.roster_limits
    
    # 1. 3-Way FLEX Split (55% WR, 40% RB, 5% TE)
    flex_total = limits.flex * teams
    flex_rb = int(round(flex_total * 0.40))
    flex_te = int(round(flex_total * 0.05))
    flex_wr = flex_total - flex_rb - flex_te
    
    # 2. Bench Depth Distribution (45% RB, 45% WR, 5% QB, 5% TE)
    bench_total = limits.bench * teams
    bench_rb = int(round(bench_total * 0.45))
    bench_wr = int(round(bench_total * 0.45))
    bench_qb = int(round(bench_total * 0.05))
    bench_te = bench_total - bench_rb - bench_wr - bench_qb
    
    # 3. Total Player Demand
    drafted_demand = {
        'QB': (teams * limits.qb) + bench_qb,
        'RB': (teams * limits.rb) + flex_rb + bench_rb,
        'WR': (teams * limits.wr) + flex_wr + bench_wr,
        'TE': (teams * limits.te) + flex_te + bench_te
    }
    
    # 4. Replacement Baselines
    baselines = {}
    for pos, count in drafted_demand.items():
        pos_df = df[df['pos'] == pos]
        if len(pos_df) > count:
            replacement_ecr = pos_df.iloc[count]['adjusted_ecr']
        else:
            replacement_ecr = pos_df['adjusted_ecr'].max()
        baselines[pos] = replacement_ecr
        
    # 5. VORP Calculation
    df['vorp_value'] = df.apply(lambda row: round(baselines[row['pos']] - row['adjusted_ecr'], 2), axis=1)
    df = df.sort_values(by='vorp_value', ascending=False).reset_index(drop=True)
    
    return df, st_df, baselines, audit_logs

def get_draft_recommendations(
    board: pd.DataFrame, 
    st_board: pd.DataFrame, 
    current_round: int, 
    total_rounds: int,
    my_roster: list[dict]
) -> list[dict]:
    """Evaluates the board and roster, returning exactly 3 recommended players."""
    has_dst = any(p['pos'] == 'DST' for p in my_roster)
    has_k = any(p['pos'] == 'K' for p in my_roster)
    
    recommendations = []
    
    # 1. Late Round Automation (Special Teams)
    if current_round >= (total_rounds - 1) and (not has_dst or not has_k):
        target_pos = 'DST' if not has_dst else 'K'
        available_st = st_board[st_board['pos'] == target_pos].head(3)
        
        for _, row in available_st.iterrows():
            recommendations.append({
                "player": row['player'],
                "pos": row['pos'],
                "team": row['team'],
                "vorp_value": 0.0,  # N/A for Kickers/Defense
                "adjusted_ecr": row['ecr'],
                "alert": f"LATE-ROUND AUTOMATION: Lock in starting {target_pos}"
            })
        return recommendations

    # 2. Evaluate Roster Needs (The "Panic" Button)
    has_qb = any(p['pos'] == 'QB' for p in my_roster)
    has_te = any(p['pos'] == 'TE' for p in my_roster)
    
    top_3_df = board.head(3).copy()
    alerts = {} 
    
    PANIC_ROUND = 7
    if current_round >= PANIC_ROUND:
        missing_pos = []
        if not has_qb: missing_pos.append('QB')
        if not has_te: missing_pos.append('TE')
        
        for pos in missing_pos:
            if pos not in top_3_df['pos'].values:
                best_available = board[board['pos'] == pos]
                if not best_available.empty:
                    forced_player = best_available.iloc[0:1].copy()
                    
                    # Drop the lowest current recommendation to make room
                    top_3_df = top_3_df.iloc[:-1] 
                    
                    # Add the forced player
                    top_3_df = pd.concat([forced_player, top_3_df], ignore_index=True)
                    alerts[forced_player.iloc[0]['player']] = f"ROSTER NEED: Consider drafting starting {pos}"

    top_3_df = top_3_df.sort_values(by='vorp_value', ascending=False).reset_index(drop=True)
    
    # 3. Format the standard output
    for _, row in top_3_df.iterrows():
        recommendations.append({
            "player": row['player'],
            "pos": row['pos'],
            "team": row['team'],
            "vorp_value": round(row['vorp_value'], 1),
            "adjusted_ecr": round(row['adjusted_ecr'], 1),
            "alert": alerts.get(row['player'], "")
        })
        
    return recommendations