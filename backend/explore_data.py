import nflreadpy as nfl
import pandas as pd

def view_final_ppr_data():
    print("Fetching the latest consensus rankings...")
    rankings_pl = nfl.load_ff_rankings()
    df = rankings_pl.to_pandas()
    
    # 1. Isolate all PPR scoring
    ppr_df = df[df['ecr_type'] == 'rp'].copy()
    
    # 2. Filter down to only the core offensive positions we care about
    core_pages = ['redraft-qb', 'redraft-rb', 'redraft-wr', 'redraft-te']
    ppr_core_df = ppr_df[ppr_df['page_type'].isin(core_pages)].copy()
    
    # 3. Sort by Expert Consensus Rank (ecr)
    ppr_core_df = ppr_core_df.sort_values(by='ecr').reset_index(drop=True)
    
    print(f"\n✅ Successfully built a master PPR list of {len(ppr_core_df)} players!")
    columns_to_view = ['player', 'pos', 'team', 'ecr', 'best', 'worst']
    
    print("\n--- Top 5 PPR Running Backs ---")
    rbs = ppr_core_df[ppr_core_df['pos'] == 'RB']
    print(rbs[columns_to_view].head())
    
    print("\n--- Top 5 PPR Wide Receivers ---")
    wrs = ppr_core_df[ppr_core_df['pos'] == 'WR']
    print(wrs[columns_to_view].head())

if __name__ == "__main__":
    view_final_ppr_data()