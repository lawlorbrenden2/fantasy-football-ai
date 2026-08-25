from cli import prompt_main_menu, run_league_wizard, run_draft_session

def main():
    while True:
        choice = prompt_main_menu()
        
        if choice == "1":
            run_league_wizard()
        elif choice == "2":
            run_draft_session()
        elif choice == "3" or choice == "quit" or choice == "q":
            print("\nExiting Fantasy Football AI. Good luck!\n")
            break
        else:
            pass

if __name__ == "__main__":
    main()