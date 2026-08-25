from pathlib import Path
from core.config_parser import (
    ScoringSettings, 
    RosterSettings, 
    LeagueConfig, 
    save_league_config,
    load_league_config,
    CONFIGS_DIR
)
from core.calculator import calculate_vorp, BiasSettings, get_draft_recommendations
import pandas as pd

def prompt_main_menu() -> str:
    print("\n" + "=" * 45)
    print("🏈🏈🏈 Welcome to Fantasy Football AI! 🏈🏈🏈")
    print("=" * 45)
    print(" 1 -> Add new league configuration")
    print(" 2 -> Draft existing league")
    print(" 3 -> Quit")
    print("-" * 45)
    return input("Please select an option (1-4): ").strip()

def run_league_wizard() -> Path:
    try:
        print("\n--- 🏈 League Configuration Setup ---")
        name = input("Enter League name (e.g., Weezer League): ").strip() or "Custom League"
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
        bench = int(input("Enter number of bench players (default 6): ") or 6)
        ir = int(input("Enter number of potential IR players (default 0): ") or 0)

        config = LeagueConfig(
            league_name=name,
            team_count=team_count,
            scoring=ScoringSettings(ppr=ppr, pass_td=pass_td, rush_td=rush_td, reception_td=reception_td),
            roster_limits=RosterSettings(qb=qb, rb=rb, wr=wr, te=te, flex=flex, dst=dst, k=k, bench=bench, ir=ir)
        )

        saved_path = save_league_config(config)
        print(f"\nConfiguration saved to {saved_path}\n")
        return saved_path
    except:
        print("Invalid input detected, please try again!")

def display_top_3_recommendations(recommendations: list[dict], current_round: int, total_rounds: int):
    """A 'dumb' UI function that purely handles rendering the data it receives."""
    print("\n" + "─" * 60)
    print(f"🎯 TOP 3 RECOMMENDED PICKS (Round {current_round}/{total_rounds})\n")
    
    for rank, rec in enumerate(recommendations, 1):
        # Attach the alert text if the engine provided one
        alert_text = f"  {rec['alert']}" if rec['alert'] else ""
        
        print(f" #{rank} -> {rec['player']} ({rec['pos']} - {rec['team']}){alert_text}")
        
        # Hide VORP if it's a kicker or defense
        if rec['pos'] in ['DST', 'K']:
            print(f"      📈 Positional Rank: #{rec['adjusted_ecr']}\n")
        else:
            print(f"      📈 Value Score: +{rec['vorp_value']}  |  Positional Rank: #{rec['adjusted_ecr']}\n")
            
    print("─" * 60)

def run_draft_session():
    print("\n--- Draft Session Setup ---")
    
    if not CONFIGS_DIR.exists() or not list(CONFIGS_DIR.glob("*.yaml")):
        print("No saved leagues found! Please use Option 1 to create one first.")
        return

    print("Available Leagues:")
    leagues = list(CONFIGS_DIR.glob("*.yaml"))
    for i, file_path in enumerate(leagues, 1):
        print(f" {i} -> {file_path.stem.replace('_', ' ').title()}")
        
    choice_input = input("\nSelect a league to draft (number or 'q' to quit): ").strip().lower()
    if choice_input == 'q':
        return
    league_choice = int(choice_input or 1)   

    selected_league_path = leagues[league_choice - 1]
    league_config = load_league_config(selected_league_path)
    
    # Draft Strategy Prompting
    print("\n--- Draft Strategy ---")
    print(" 1 -> Vanilla (Pure Consensus)")
    print(" 2 -> Zero-RB (Prioritize WR/TE early)")
    print(" 3 -> Hero-RB (Anchor with 1 elite RB)")
    print(" 4 -> Late-Round QB (Penalize early QBs)")
    strategy_choice = input("Choice (1-4) [Default 1]: ").strip() or "1"
    
    homer_team = input("\nEnter favorite NFL team for rank boost (or press Enter to skip): ").strip().upper() or None
    sleepers_in = input("Enter Sleepers to boost (comma-separated, or Enter to skip): ").strip()
    busts_in = input("Enter Busts to avoid (comma-separated, or Enter to skip): ").strip()
    
    sleepers = [p.strip() for p in sleepers_in.split(",")] if sleepers_in else []
    busts = [p.strip() for p in busts_in.split(",")] if busts_in else []
    
    strategy = BiasSettings(
        strategy=strategy_choice,
        homer_team=homer_team,
        sleepers=sleepers,
        busts=busts
    )
    
    # Total rounds calculation
    limits = league_config.roster_limits
    total_rounds = limits.qb + limits.rb + limits.wr + limits.te + limits.flex + limits.dst + limits.k + limits.bench
    
    # Initialize Engine
    draft_board, st_board, baselines, audit_logs = calculate_vorp(league_config, strategy)
    my_roster = []
    current_pick = 1
    
    print("\n" + "=" * 60)
    print(f"WAR ROOM ACTIVE: {league_config.league_name} ({total_rounds} Total Rounds)")
    print("=" * 60)

    # Print the Validation Audit Report
    print("\n📋 --- Applied Customizations & Validation ---")
    if not audit_logs:
        print(" (No custom biases applied)")
    for log in audit_logs:
        print(f" {log}")
    print("─" * 60)
    
    while current_pick <= (league_config.team_count * total_rounds):
        current_round = ((current_pick - 1) // league_config.team_count) + 1

        recs = get_draft_recommendations(draft_board, st_board, current_round, total_rounds, my_roster)
        
        display_top_3_recommendations(recs, current_round, total_rounds)
        
        print(f"Round {current_round} | Overall Pick #{current_pick}")
        print("Commands: [d <Player Name>] (Draft for My Team) | [t <Player Name>] (Taken by Opponent) | [r] (Roster) | [q] (Quit)")
        cmd = input("Enter command: ").strip()
        
        if not cmd:
            continue
            
        if cmd.lower() == 'q':
            print("\nExiting Draft Session...")
            break
            
        if cmd.lower() == 'r':
            print("\n --- My Current Roster ---")
            for p in my_roster:
                print(f"  • {p['player']} ({p['pos']} - {p['team']})")
            input("\nPress Enter to continue...")
            continue
            
        action = cmd[0].lower()
        target = cmd[1:].strip().lower()
        
        if not target:
            print("\nPlease provide a player name or number (e.g., 'd 1' or 't Bijan').")
            continue
            
        matched = pd.DataFrame()
        is_st = False
        
        # 1. Shortcut: Select by Recommendation Number (1, 2, or 3)
        if target in ['1', '2', '3']:
            idx = int(target) - 1
            has_dst = any(p['pos'] == 'DST' for p in my_roster)
            has_k = any(p['pos'] == 'K' for p in my_roster)
            
            # Check if we are in the late-round special teams phase
            if current_round >= (total_rounds - 1) and (not has_dst or not has_k):
                target_pos = 'DST' if not has_dst else 'K'
                matched = st_board[st_board['pos'] == target_pos].head(3).iloc[[idx]]
                is_st = True
            else:
                matched = draft_board.head(3).iloc[[idx]]
                
        # 2. Fuzzy Search: Partial Name Matching
        else:
            off_match = draft_board[draft_board['player'].str.lower().str.contains(target, na=False)]
            if not off_match.empty:
                matched = off_match.head(1)
            else:
                st_match = st_board[st_board['player'].str.lower().str.contains(target, na=False)]
                if not st_match.empty:
                    matched = st_match.head(1)
                    is_st = True
                    
        if matched.empty:
            print(f"\nPlayer matching '{target}' not found. Please check spelling.")
            continue
            
        player_row = matched.iloc[0]
        selected_name = player_row['player']
        selected_pos = player_row['pos']
        selected_team = player_row['team']
        
        if action == 'd':
            my_roster.append({'player': selected_name, 'pos': selected_pos, 'team': selected_team})
            print(f"\nDRAFTED TO YOUR TEAM: {selected_name} ({selected_pos} - {selected_team})")
        elif action == 't':
            print(f"\n MARKED AS TAKEN: {selected_name} ({selected_pos} - {selected_team})")
        else:
            print("\nUnknown command format. Use 'd Player Name' (or 'd 1') or 't Player Name'.")
            continue
            
        # Safely remove the matched player using their exact database name
        if not is_st:
            draft_board = draft_board[draft_board['player'] != selected_name].reset_index(drop=True)
        else:
            st_board = st_board[st_board['player'] != selected_name].reset_index(drop=True)
            
        current_pick += 1

    print("\n🏁 Draft complete! Here is your final drafted roster:")
    for p in my_roster:
        print(f"  • {p['pos']}: {p['player']} ({p['team']})")