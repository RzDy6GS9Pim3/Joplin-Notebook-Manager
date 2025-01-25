import difflib
import os
import getkey
import re
from joppy.client_api import ClientApi
from difflib import SequenceMatcher
from joplin_utils import setup_notebooks

def process_single_duplicate_notes(api):
    NOTEBOOK_ANALYZED = "Analized_notes"
    NOTEBOOK_TO_DELETE = "Notes_to_be_deleted"
    notebook_analyzed, notebook_to_delete = setup_notebooks(api, NOTEBOOK_ANALYZED, NOTEBOOK_TO_DELETE)

    # Get all notebooks (DataList)
    all_notebooks = api.get_notebooks(fields="id,title").items

    # Collect notes from non-excluded notebooks
    notes_to_process = []
    print("\n" + "="*40 + " NOTE COLLECTION " + "="*40)
    for notebook in all_notebooks:
            print(f"\nProcessing notebook: {notebook.title}")
            
            # Get notes as list (no .items needed)
            notes = api.get_all_notes(
                notebook_id=notebook.id,
                fields="id,title,body,parent_id"
            )
            
            print(f"Found {len(notes)} notes")
            notes_to_process.extend(notes)

    print(f"\nTotal notes to process: {len(notes_to_process)}")

    notebook_id_to_title = {nb.id: nb.title for nb in all_notebooks}

    # Track moved notes globally
    moved_notes = set()

    # Note processing logic
    for idx, note in enumerate(notes_to_process):
        if note.id in moved_notes:
            print(f"\nSkipping note {note.title} (already marked for deletion)")
            continue  # Skip processing if already moved
        
        print(f"\nProcessing note {idx+1}/{len(notes_to_process)}")
        print(f"Title: {note.title}")
        print(f"Parent notebook: {notebook_id_to_title.get(note.parent_id, 'Unknown')}")
        
        current_note_id = note.id
        current_notebook_id = note.parent_id

        # Generate search query from the lines
        body = note.body or ""  # Handle empty notes
        notelines = body.replace('(', ' ').replace(')', ' ')\
                       .replace('[', ' ').replace(']', ' ')\
                       .replace('"', ' ').replace('&', ' ')\
                       .replace('#', ' ').replace('%', ' ')\
                       .replace('.', ' ').split('\n')
        
        if not notelines:
            continue

        print(f"\nProcessing note: {note.title}")

        # Determine lines to use for queries
        if len(notelines) > 10:
            selected_lines = notelines[::2]  # Every alternate line
        else:
            selected_lines = notelines  # All lines

        # Generate queries from selected lines (strip and filter empty)
        queries = [f'"{line.strip()}"' for line in selected_lines if line.strip()]
        print(f"Generated {len(queries)} search queries")

        seen_duplicate_ids = set()
        duplicates = []

        # Process each query and collect duplicates
        for query in queries:
            print(f"Searching with query: {query}")
            search_results = api.search(query=query)
            
            # Filter valid duplicates
            for result in search_results.items:
                if (result.id != current_note_id 
                    # and result.parent_id != current_notebook_id 
                    and result.id not in seen_duplicate_ids):
                    
                    seen_duplicate_ids.add(result.id)
                    duplicates.append(result)

        if not duplicates:
            print("No duplicates found in other notebooks.")
            print("\n" + "-"*50)
            continue

        print(f"Found {len(duplicates)} potential duplicates")

        # Compare with each duplicate
        for duplicate in duplicates:
            if duplicate.id in moved_notes:
                print(f"Skipping duplicate {duplicate.id} (already deleted)")
                continue  # Skip already-moved duplicates
            duplicate_note = api.get_note(
                id_=duplicate.id,
                fields="id,title,body,parent_id"
            )

            print("\n" + "="*50)
            print(f"Original Note ({notebook_id_to_title.get(current_notebook_id, 'Unknown')}): {note.title}")
            print(f"Duplicate Note ({notebook_id_to_title.get(duplicate_note.parent_id, 'Unknown')}): {duplicate_note.title}")

            # Generate side-by-side diff
            print("\nSide-by-side comparison:")
            a = (note.body or "").splitlines()
            b = (duplicate_note.body or "").splitlines()
            
            # ANSI color codes
            RED = '\033[31m'
            GREEN = '\033[32m'
            RESET = '\033[0m'
            
            # Formatting parameters
            max_width = 80
            spacer = ' ' * 4  # Space between columns
            
            header_left = f"[Original] {notebook_id_to_title.get(current_notebook_id, 'Unknown')} › {note.title}"[:max_width]
            header_right = f"[Duplicate] {notebook_id_to_title.get(duplicate_note.parent_id, 'Unknown')} › {duplicate_note.title}"[:max_width]
            BLUE = '\033[34m'
            MAGENTA = '\033[35m'
            BOLD = '\033[1m'
            
            print(f"\n{BOLD}{BLUE}{header_left.ljust(max_width)}{RESET}{spacer}"
                  f"{BOLD}{MAGENTA}{header_right.ljust(max_width)}{RESET}")
            print(f"{'-'*max_width}{spacer}{'-'*max_width}")
            
            # Create comparison pairs
            sm = SequenceMatcher(None, a, b)
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == 'equal':
                    for line in a[i1:i2]:
                        left = line[:max_width].ljust(max_width)
                        right = line[:max_width].ljust(max_width)
                        print(f"{left}{spacer}{right}")
                elif tag == 'replace':
                    for line_a, line_b in zip(a[i1:i2], b[j1:j2]):
                        left = f"{RED}- {line_a[:max_width]}{RESET}".ljust(max_width + len(RED) + len(RESET))
                        right = f"{GREEN}+ {line_b[:max_width]}{RESET}".ljust(max_width + len(GREEN) + len(RESET))
                        print(f"{left}{spacer}{right}")
                elif tag == 'delete':
                    for line in a[i1:i2]:
                        left = f"{RED}- {line[:max_width]}{RESET}".ljust(max_width + len(RED) + len(RESET))
                        print(f"{left}{spacer}")
                elif tag == 'insert':
                    for line in b[j1:j2]:
                        right = f"{GREEN}+ {line[:max_width]}{RESET}".ljust(max_width + len(GREEN) + len(RESET))
                        print(f"{'':<{max_width}}{spacer}{right}")

            # User decision
            choice = None  # Track the choice outside the loop
            while True:
                print("\nChoose action:")
                print("1. Keep ORIGINAL, move duplicate to delete")
                print("2. Keep DUPLICATE, move original to delete")
                print("3. Skip both")
                print("4. Mark both for deletion")
                choice = getkey.getkey()

                if choice == '1':
                    api.modify_note(duplicate.id, parent_id=notebook_to_delete.id)
                    print(f"Moved duplicate to {NOTEBOOK_TO_DELETE}")
                    break
                elif choice == '2':
                    api.modify_note(current_note_id, parent_id=notebook_to_delete.id)
                    print(f"Moved original to {NOTEBOOK_TO_DELETE}")
                    break
                elif choice == '3':
                    print("Skipped both notes")
                    break
                elif choice == '4':
                    api.modify_note(duplicate.id, parent_id=notebook_to_delete.id)
                    api.modify_note(current_note_id, parent_id=notebook_to_delete.id)
                    print("Both notes moved to delete notebook")
                    break
                else:
                    print("Invalid choice. Try again.")
            print("\n" + "-"*50)
            
            # Only break the duplicates loop for choices 1 or 2
            if choice in ['1', '2']:
                break  # Exit the "for duplicate in duplicates" loop
            # For choices 3/4, continue to next duplicate (if any)

    print("\nProcessing complete!")
