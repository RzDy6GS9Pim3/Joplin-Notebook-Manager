# main.py
import os
import sys
import getkey
from typing import List
from joppy.client_api import ClientApi

# Import your modules
from deleteDuplicateNotes import process_duplicate_notes
from deleteEmptyNotebooksAndMerge import (
    find_empty_notebooks,
    confirm_and_delete,
    merge_duplicate_notebooks_interactive,
    print_notebook_tree4Printing
)
from NotSoUsefulNotebookMerger import merge_notebooks
from only1duplicateNote4eachNote import process_single_duplicate_notes

# Configuration
NOTEBOOK_ANALYZED = "Analized_notes"
NOTEBOOK_TO_DELETE = "Notes_to_be_deleted"

def get_api_client() -> ClientApi:
    """Get authenticated API client"""
    token = os.getenv("JOPLIN_TOKEN") or input("Enter your JOPLIN API token: ")
    return ClientApi(token=token)

def print_header(title: str) -> None:
    """Print formatted header"""
    print(f"\n{'='*40}")
    print(f"{' '*10}{title.upper()}{' '*10}")
    print(f"{'='*40}\n")

def main_menu() -> None:
    """Main interactive menu"""
    api = get_api_client()
    
    while True:
        print_header("joplin notebook manager")
        choices = [
            "1. Find & Manage Duplicate Notes",
            "2. Find & Merge Duplicate Notebooks",
            "3. Find & Delete Empty Notebooks",
            "4. Merge Similar Notebooks by Name",
            "5. View Notebook Hierarchy",
            "6. Exit"
        ]
        
        print("\n".join(choices))
        choice = input("\nChoose an operation (1-6): ")

        try:
            if choice == '1':
                print_header("duplicate note management")
                process_duplicate_notes(api)
                
            elif choice == '2':
                print_header("notebook merging")
                merge_duplicate_notebooks_interactive(api)
                print("\n\n\n")
                print("=== The Notebook from which everything was moved must be Empty now. Kindly Use the 'Find & Delete Empty Notebooks' Feature ===")
                
            elif choice == '3':
                print_header("empty notebook cleanup")
                all_notebooks = api.get_notebooks(fields="id,parent_id,title").items
                empty_nbs = find_empty_notebooks(api)
                confirm_and_delete(api,empty_nbs, all_notebooks)
                
            elif choice == '4':
                print_header("name-based notebook merging")
                print('This part of the program is buggy')
                #merge_notebooks(api)
                
            elif choice == '5':
                print_header("notebook hierarchy visualization")
                print_notebook_tree4Printing(api)
                
            elif choice == '6':
                print("\nGoodbye!")
                sys.exit(0)
                
            else:
                print("\nInvalid choice. Please try again.")
                
            input("\nPress Enter to continue...")
            os.system('cls' if os.name == 'nt' else 'clear')
            
        except KeyboardInterrupt:
            print("\nOperation cancelled by user.")
            sys.exit(1)
        except Exception as e:
            print(f"\nError: {str(e)}")
            sys.exit(1)

if __name__ == "__main__":
    main_menu()
