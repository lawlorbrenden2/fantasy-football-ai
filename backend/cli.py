from pathlib import Path
from core.config_parser import (
    ScoringSettings, 
    RosterSettings, 
    LeagueConfig, 
    save_league_config
)
from core.config_parser import load_league_config
from core.calculator import calculate_vorp, BiasSettings

def prompt_main_menu():
    print("🏈🏈🏈 Welcome to the Fantasy Football AI! 🏈🏈🏈")
    user_action = input("Please input what you would like to do: ")
    return user_action.strip()

def run_league_wizard() -> Path:
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
    k = int(input("Enter number of starting kickers (default 1): ") or 1)
    bench = int(input("Enter number of bench players (default 7): ") or 7)
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

def run_draft_session():
    print("\n--- Draft Session Setup ---")
    
    config_dir = Path("configs")
    if not config_dir.exists() or not list(config_dir.glob("*.yaml")):
        print("No saved leagues found. Please use Option 1 to create one first.")
        return

    print("Available Leagues:")
    leagues = list(config_dir.glob("*.yaml"))
    for i, file_path in enumerate(leagues, 1):
        print(f" {i} -> {file_path.stem.replace('_', ' ').title()}")
        
    league_choice = int(input("\nSelect a league to draft (number): ") or 1)
    selected_league_path = leagues[league_choice - 1]
    
    print(f"\nLoading configuration for: {selected_league_path.stem}...")
    
    print("\n--- Draft Strategy Settings---")
    print("Press Enter to leave an option blank (Vanilla behavior).")
    
    # 1. Positional Strategy
    print("\nSelect a Core Positional Strategy:")
    print(" 1 -> Vanilla (Pure Consensus)")
    print(" 2 -> Zero-RB (Prioritize WR/TE)")
    print(" 3 -> Hero-RB (Anchor with 1 RB, then WR)")
    print(" 4 -> Late-Round QB (Penalize early QBs)")
    strategy_choice = input("Choice (1-4) [Default 1]: ").strip() or "1"
    
    # 2. Team Bias
    homer_team = input("\nEnter favorite NFL team for a rank boost (e.g., DET, SF, KC) or leave blank: ").strip().upper()
    
    # 3. Specific Player Boosts ("My Guys")
    sleepers_input = input("Enter any potential sleepers to heavily boost, comma-separated (e.g., Christian McCaffrey, Brock Bowers) or leave blank:\n> ").strip()

    # 4. Specific Player Penalties ("Busts")
    busts_input = input("Enter any potential busts you'd like to heavily penalize, comma-separated (e.g., Christian McCaffrey, Brock Bowers) or leave blank:\n> ").strip()

    busts_input = input("Enter any potential busts you'd like to heavily avoid, comma-separated:\n> ").strip()
    
    # 5. The Stacking Toggle
    print("\nDo you want to enable Dynamic Stacking?")
    print("(This automatically boosts QBs/Receivers if you draft their teammates to maximize weekly ceiling.)")
    stack_input = input("Enable Stacking? (y/n) [Default n]: ").strip().lower()
    enable_stacking = True if stack_input == 'y' else False
    
    # Convert the comma string into a clean Python list
    if sleepers_input:
        sleepers = [player.strip() for player in sleepers_input.split(",")]
    else:
        sleepers = []

    if busts_input:
        busts = [player.strip() for player in busts_input.split(",")]
    else:
        busts = []
        
    # Summarize the loadout for the user
    print("\n🚪 Initializing Draft Board with your custom loadout:")
    print(f" - Strategy: {strategy_choice}")
    print(f" - Homer Bias: {homer_team if homer_team else 'None'}")
    print(f" - Sleepers to boost: {', '.join(sleepers) if sleepers else 'None'}")
    print(f" - Busts to avoid: {', '.join(busts) if busts else 'None'}")
    print(f" - Dynamic Stacking: {'ON' if enable_stacking else 'OFF'}")
    print("\nEntering the War Room...")
    
    league_config = load_league_config(selected_league_path)
    bias_settings = BiasSettings(
        strategy=strategy_choice,
        homer_team=homer_team,
        sleepers=sleepers,
        busts=busts
    )
    
    # 2. Run the math engine
    draft_board = calculate_vorp(league_config, bias_settings)
    
    # 3. Display the optimized results
    print("\n --- TOP 20 DRAFT BOARD --- ")
    columns_to_show = ['player', 'pos', 'team', 'ecr', 'adjusted_ecr', 'vorp_value']
    print(draft_board[columns_to_show].head(20).to_string(index=False))
    
    input("\nDraft paused. Press Enter to return to main menu...")
    