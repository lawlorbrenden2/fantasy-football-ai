from core.config_parser import load_league_config

def test_pydantic_defaults():
    my_league = load_league_config("configs/weezer_league.yml")

    assert my_league.league_name == "Weezer League"
    assert my_league.team_count == 14
    assert my_league.scoring.ppr == 1.0

    assert my_league.scoring.pass_td == 4
    assert my_league.roster_limits.qb == 1
    assert my_league.roster_limits.wr == 2
    assert my_league.roster_limits.flex == 1