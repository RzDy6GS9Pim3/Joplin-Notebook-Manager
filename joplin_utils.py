# joplin_utils.py
import os
import getkey
from joppy.client_api import ClientApi

def get_api_client():
    """Get authenticated API client"""
    token = os.getenv("JOPLIN_TOKEN") or input("Enter your JOPLIN API token: ")
    return ClientApi(token=token)

def setup_notebooks(api, analyzed_name, delete_name):
    """Ensure required notebooks exist"""
    def get_or_create(name):
        notebooks = api.get_notebooks(fields="id,title").items
        for nb in notebooks:
            if nb.title == name:
                return nb
        new_id = api.add_notebook(title=name)
        return api.get_notebook(new_id)
    
    return (
        get_or_create(analyzed_name),
        get_or_create(delete_name)
    )

def confirm_action(prompt):
    """Get user confirmation with safety checks"""
    while True:
        response = input(f"{prompt} [y/N] ").lower()
        if response in ('y', 'n'):
            return response == 'y'
        print("Invalid input. Please enter 'y' or 'n'.")

def print_diff_header(note1, note2, max_width=80):
    """Print standardized diff header"""
    print("\n" + "="*(max_width*2 + 10))
    print(f"{'Original Note':^{max_width}} | {'Duplicate Note':^{max_width}}")
    print(f"{note1.title[:max_width]:^{max_width}} | {note2.title[:max_width]:^{max_width}}")
    print("="*(max_width*2 + 10))
