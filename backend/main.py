from cli import prompt_main_menu, run_league_wizard, run_draft_session

options_text = """
--- Main Menu ---
1 -> Add new league
2 -> Draft existing league
3 -> Quit
4 -> See Options
"""

def main():
    print(options_text)
    while True:
        choice = prompt_main_menu()
        
        if choice == "1":
            run_league_wizard()
        elif choice == "2":
            run_draft_session()
        elif choice == "3":
            print("\nExiting Fantasy Football AI. Good luck!\n")
            break
        else:
            print(options_text)

if __name__ == "__main__":
    main()