#README
# Finds notebooks starting from the same word. Deletes all notes (only notes, no subnotebooks are deleted) under both notebooks. Creates a New Notebook under Root Level, and pastes all the notes here.

import difflib
import hashlib
import re
from joppy.client_api import ClientApi
import getkey
from joplin_utils import setup_notebooks

def get_note_hash(note_body):
    """Create hash for full note comparison"""
    return hashlib.sha256(note_body.encode()).hexdigest()

    # Collect all notes from non-excluded notebooks
    all_notes = []
    for notebook in api.get_notebooks().items:
        if notebook.id not in excluded_ids:
        # Get notes as list (no .items needed)
            notes = api.get_all_notes(
                notebook_id=notebook.id,
                fields="id,title,body,parent_id"
            )
            print(f"\nProcessing notebook: {notebook.title}")
            print(f"Found {len(notes)} notes")
            all_notes.extend(notes)

    # Create hash map for duplicate detection
    note_hashes = {}
    for note in all_notes:
        clean_body = (note.body or "").strip()
        if not clean_body:
            continue
        note_hash = get_note_hash(clean_body)
        if note_hash in note_hashes:
            note_hashes[note_hash].append(note)
        else:
            note_hashes[note_hash] = [note]

    def compare_notes_side_by_side(note1, note2):
        """Display notes in side-by-side format with titles"""
        lines1 = (note1.body or "").splitlines()
        lines2 = (note2.body or "").splitlines()
        
        # Header with titles and IDs
        print("\n" + "="*80)
        print(f"{'Note 1: ' + note1.title[:30] + ('...' if len(note1.title)>30 else '') :<40}{'Note 2: ' + note2.title[:30] + ('...' if len(note2.title)>30 else '')}")
        print(f"{'ID: ' + note1.id :<40}{'ID: ' + note2.id}")
        print("-"*80)
        
        # Pad shorter list with empty strings
        max_lines = max(len(lines1), len(lines2))
        lines1 += [''] * (max_lines - len(lines1))
        lines2 += [''] * (max_lines - len(lines2))
        
        # Compare line by line
        for i, (line1, line2) in enumerate(zip(lines1, lines2)):
            marker = " " if line1 == line2 else "|"
            print(f"{i+1:03d} {line1[:60]:<65} {marker} {line2[:60]}")
        
        print("="*80 + "\n")

    # Process duplicates
    for hash_val, notes in note_hashes.items():
        if len(notes) < 2:
            continue
        
        print(f"\nFound {len(notes)} potential duplicates:")
        for note in notes:
            print(f"- {note.title} ({note.id})")

        # Compare all pairs
        for i in range(len(notes)):
            for j in range(i+1, len(notes)):
                note1 = notes[i]
                note2 = notes[j]
                
                print("\n" + "="*80)
                print(f"Comparing:\n1. {note1.title}\n2. {note2.title}")
                
                # In your comparison block, replace the diff section with:
                print("\n" + "="*80)
                compare_notes_side_by_side(note1, note2)
                
                # User decision
                while True:
                    print("\nChoose action:")
                    print("1. Keep note 1, delete note 2")
                    print("2. Keep note 2, delete note 1")
                    print("3. Keep both")
                    print("4. Delete both")
                    choice = getkey.getkey()
                    
                    if choice == '1':
                        api.modify_note(note2.id, parent_id=notebook_to_delete.id)
                        break
                    elif choice == '2':
                        api.modify_note(note1.id, parent_id=notebook_to_delete.id)
                        break
                    elif choice == '3':
                        break
                    elif choice == '4':
                        api.modify_note(note1.id, parent_id=notebook_to_delete.id)
                        api.modify_note(note2.id, parent_id=notebook_to_delete.id)
                        break
                    else:
                        print("Invalid choice")

    print("\nDuplicate processing complete!")

#----------------------------------------------------
def get_base_name(notebook_title):
    """Extract base name before first hyphen or space"""
    # Split on first non-alphanumeric character
    match = re.match(r"^([\w]+)[\W]?", notebook_title)
    return match.group(1).lower() if match else notebook_title.lower()

def merge_notebooks(api):
    NOTEBOOK_ANALYZED = "Analized_notes"
    NOTEBOOK_TO_DELETE = "Notes_to_be_deleted"
    notebook_analyzed, notebook_to_delete = setup_notebooks(api, NOTEBOOK_ANALIZYED, NOTEBOOK_TO_DELETE)
    excluded_ids = {notebook_analyzed.id, notebook_to_delete.id}

    """Find and merge notebooks with same base name"""
    all_notebooks = [nb for nb in api.get_notebooks().items 
                    if nb.id not in excluded_ids]
    
    # Group notebooks by base name
    notebook_groups = {}
    for nb in all_notebooks:
        base = get_base_name(nb.title)
        if base not in notebook_groups:
            notebook_groups[base] = []
        notebook_groups[base].append(nb)
    
    # Process groups with potential merges
    for base, notebooks in notebook_groups.items():
        if len(notebooks) < 2:
            continue
            
        print(f"\nFound {len(notebooks)} notebooks starting with '{base}':")
        for i, nb in enumerate(notebooks, 1):
            print(f"{i}. {nb.title} (Notes: {len(api.get_all_notes(notebook_id=nb.id))})")
        
        while True:
            choice = input(f"\nMerge these '{base}' notebooks? (y/n/q) ").lower()
            if choice == 'q':
                return
            if choice in ('y', 'n'):
                break
        
        if choice == 'n':
            continue
            
        # Create target notebook
        target_name = base.capitalize()
        target_nb = get_or_create_notebook(target_name)
        
        # Move notes from all notebooks to target
        for nb in notebooks:
            if nb.id == target_nb.id:
                continue  # Skip target notebook itself
                
            print(f"\nMoving notes from {nb.title} to {target_name}:")
            notes = api.get_all_notes(notebook_id=nb.id)
            for note in notes:
                try:
                    api.modify_note(note.id, parent_id=target_nb.id)
                    print(f"✓ Moved: {note.title}")
                except Exception as e:
                    print(f"× Failed to move {note.title}: {str(e)}")
