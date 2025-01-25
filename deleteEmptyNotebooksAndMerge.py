from joppy.client_api import ClientApi
import re
from collections import defaultdict

def print_notebook_tree4Printing(api):
    """Print hierarchy starting from true root notebooks (parent_id='')"""
    print("\n=== NOTEBOOK NETWORK MAP ===")
    
    all_notebooks = api.get_notebooks(fields="id,parent_id,title").items
    notebook_map = {nb.id: nb for nb in all_notebooks}
    parent_map = {}
    
    # Build parent-child relationships
    for nb in all_notebooks:
        if nb.parent_id not in parent_map:
            parent_map[nb.parent_id] = []
        parent_map[nb.parent_id].append(nb)

    # Print recursive tree with proper root handling
    def print_children(parent_id, level=0, visited=None):
        if visited is None:
            visited = set()
        if parent_id in visited:
            print("  " * level + "⚠️ CIRCULAR REFERENCE!")
            return
        visited.add(parent_id)

        for child in parent_map.get(parent_id, []):
            # Get child status
            notes = len(api.get_notes(notebook_id=child.id).items)
            subs = len(parent_map.get(child.id, []))
            
            # Print with different root indicators
            if parent_id == '':
                prefix = "🌳 ROOT: "
            else:
                prefix = "📂 "
            
            print("      " * level + 
                 f"{prefix}{child.title} [notes: {notes}, subs: {subs}] "
                 )
            
            print_children(child.id, level + 1, visited.copy())

    # Start with true roots (parent_id='')
    print("\nMAIN HIERARCHY (parent_id=''):")
    if '' in parent_map:
        print_children('')
    else:
        print("No root notebooks found!")
    
    # Find orphan hierarchies (parent IDs that don't exist)
    orphan_parents = [pid for pid in parent_map 
                     if pid != '' and pid not in notebook_map]
    
    if orphan_parents:
        print("\nORPHANED HIERARCHIES (invalid parent references):")
        for pid in orphan_parents:
            print(f"\n🚨 Orphan group (parent_id={pid}):")
            print_children(pid)

#----------------------------Find Empty Notebooks-----------------------------------------------
def find_empty_notebooks(api):
    """Find notebooks with no subnotebooks and no notes."""
    all_notebooks = api.get_notebooks(fields="id,parent_id,title").items
    notebook_parent_map = {}
    empty_notebooks = []

    # Build parent-child relationships
    for nb in all_notebooks:
        if nb.parent_id not in notebook_parent_map:
            notebook_parent_map[nb.parent_id] = []
        notebook_parent_map[nb.parent_id].append(nb.id)

    # Check each notebook
    for nb in all_notebooks:
        # Check for subnotebooks
        has_children = nb.id in notebook_parent_map
        
        # Check for notes
        notes = api.get_notes(notebook_id=nb.id, fields="id")
        has_notes = len(notes.items) > 0

        if not has_children and not has_notes:
            empty_notebooks.append(nb)

    return empty_notebooks

def parse_selection(input_str, max_index):
    """Parse user input into valid notebook indices."""
    selected = set()
    parts = input_str.split(',')
    
    for part in parts:
        part = part.strip()
        if '-' in part:
            try:
                start, end = map(int, part.split('-'))
                for num in range(start, end+1):
                    if 1 <= num <= max_index:
                        selected.add(num-1)
            except ValueError:
                continue
        else:
            try:
                num = int(part)
                if 1 <= num <= max_index:
                    selected.add(num-1)
            except ValueError:
                continue
    return sorted(selected)

def get_notebook_hierarchy(notebook_id, all_notebooks):
    """Return hierarchy path as 'Grandparent > Parent > Notebook'"""
    hierarchy = []
    current_id = notebook_id
    notebook_map = {nb.id: nb for nb in all_notebooks}
    
    while current_id in notebook_map:
        current_nb = notebook_map[current_id]
        hierarchy.append(current_nb.title)
        current_id = current_nb.parent_id
        
    return ' > '.join(reversed(hierarchy))

#----------------------------Delete Empty Notebooks-----------------------------------------------
def confirm_and_delete(api, notebooks, all_notebooks):  # Added all_notebooks parameter
    """Show hierarchy in notebook list"""
    if not notebooks:
        print("No empty notebooks found!")
        return

    print("\nEmpty notebooks found:")
    for i, nb in enumerate(notebooks, 1):
        hierarchy_path = get_notebook_hierarchy(nb.id, all_notebooks)
        print(f"{i}. {hierarchy_path}")

    # First confirmation: Delete all?
    choice = input("\nDelete ALL these notebooks? [y/N] ").lower()
    if choice == 'y':
        for nb in notebooks:
            try:
                api.delete_notebook(nb.id)
                print(f"Deleted: {nb.title}")
            except Exception as e:
                print(f"Failed to delete {nb.title}: {str(e)}")
        return

    # Second confirmation: Delete some?
    choice = input("\nWould you like to delete specific notebooks instead? [y/N] ").lower()
    if choice != 'y':
        print("Aborted.")
        return

    # Show list again for selection
    print("\nAvailable notebooks:")
    for i, nb in enumerate(notebooks, 1):
        print(f"{i}. {nb.title} (ID: {nb.id})")
    
    # Get and validate selection
    selection = input("\nEnter notebooks to delete (e.g. 1,3 or 2-5): ")
    selected_indices = parse_selection(selection, len(notebooks))
    
    if not selected_indices:
        print("No valid selection made. Aborting.")
        return

    # Show selected notebooks
    print("\nSelected for deletion:")
    for idx in selected_indices:
        nb = notebooks[idx]
        print(f"- {nb.title} (ID: {nb.id})")
    
    # Final confirmation
    choice = input("\nConfirm deletion of these notebooks? [y/N] ").lower()
    if choice != 'y':
        print("Aborted.")
        return
    
    # Perform deletion
    for idx in selected_indices:
        nb = notebooks[idx]
        try:
            api.delete_notebook(nb.id)
            print(f"Deleted: {nb.title}")
        except Exception as e:
            print(f"Failed to delete {nb.title}: {str(e)}")

#----------------------------Duplicate NoteBook Merge-----------------------------------------------
def get_hierarchy_path(notebook_id, notebook_map):
    """Get hierarchy path with numeric suffix removal"""
    path = []
    current_id = notebook_id
    while current_id in notebook_map:
        nb = notebook_map[current_id]
        # Remove trailing "(1)"-style suffixes
        clean_title = re.sub(r'\s+\(\d+\)$', '', nb.title)
        path.append(clean_title)
        current_id = nb.parent_id
    return ' > '.join(reversed(path))

def find_duplicate_notebooks(all_notebooks):
    """Find duplicates ignoring numeric suffixes"""
    notebook_map = {nb.id: nb for nb in all_notebooks}
    hierarchy_map = {}

    for nb in all_notebooks:
        path = get_hierarchy_path(nb.id, notebook_map)
        # Clean current notebook title too
        clean_title = re.sub(r'\s+\(\d+\)$', '', nb.title)
        key = f"{path}::{clean_title}".lower()
        hierarchy_map.setdefault(key, []).append(nb)

    return {k: v for k, v in hierarchy_map.items() if len(v) > 1}

def merge_duplicate_notebooks_interactive(api):
    """Interactive merge using pre-built hierarchy data"""
    # Build hierarchy data once
    all_notebooks = api.get_notebooks(fields="id,parent_id,title").items
    notebook_map = {nb.id: nb for nb in all_notebooks}
    parent_map = defaultdict(list)
    notes_count_map = defaultdict(int)
    
    # Populate maps
    for nb in all_notebooks:
        parent_map[nb.parent_id].append(nb)
        notes_count_map[nb.id] = len(api.get_notes(notebook_id=nb.id).items)

    duplicates = find_duplicate_notebooks(all_notebooks)

    if not duplicates:
        print("No duplicate notebook hierarchies found.")
        return

    print("\n=== Potential Duplicates ===")
    for key, notebooks in duplicates.items():
        print(f"\nDuplicate Group: {key.split('::')[0]}")
        for nb in notebooks:
            subs_count = len(parent_map.get(nb.id, []))
            notes_count = notes_count_map[nb.id]
            print(f"  {nb.title} (ID: {nb.id}) [{notes_count} notes, {subs_count} subs]")

    for key, notebooks in duplicates.items():
        print(f"\nProcessing duplicates for: {key.split('::')[0]}")
        
        # Use hierarchy data for preview
        print("\nAffected Notebook Structure:")
        print_notebook_tree(api, notebook_map, parent_map, notes_count_map, highlight_ids=[nb.id for nb in notebooks])

        # Selection and merging logic using hierarchy data
        target = select_target_notebook(notebooks)
        sources = [nb for nb in notebooks if nb.id != target.id]

        # Preview using our maps
        print("\nMerge Preview:")
        total_notes = sum(notes_count_map[nb.id] for nb in sources)
        total_subs = sum(len(parent_map[nb.id]) for nb in sources)
        print(f"Will move from {len(sources)} sources:")
        print(f"- {total_notes} notes")
        print(f"- {total_subs} subnotebooks (with their hierarchies)")
        
        if confirm_action("Confirm merge?"):
            # Perform merge using our hierarchy-aware function
            moved_count = hierarchy_aware_merge(
                api, sources, target, 
                parent_map, notes_count_map
            )
            
            # Update our maps after merge
            update_hierarchy_maps(
                sources, target, 
                parent_map, notes_count_map, 
                moved_count
            )
            
            print(f"Moved {moved_count} items. Updated hierarchy:")
            print_notebook_tree(api, notebook_map, parent_map, notes_count_map)

def hierarchy_aware_merge(api, sources, target, parent_map, notes_count_map):
    """Merge using hierarchy data without redundant API calls"""
    moved_count = 0
    
    for source in sources:
        # Move subnotebooks using our parent_map
        for sub_nb in parent_map.get(source.id, []):
            try:
                api.modify_notebook(sub_nb.id, parent_id=target.id)
                moved_count += 1
                # Update maps immediately
                parent_map[target.id].append(sub_nb)
                parent_map[source.id].remove(sub_nb)
                print(f"Moved subnotebook: {sub_nb.title}")
            except Exception as e:
                print(f"Failed to move subnotebook {sub_nb.title}: {str(e)}")

        # Move notes using proper paginated API calls
        if notes_count_map[source.id] > 0:
            notes = []
            page = 1
            while True:
                notes_batch = api.get_notes(
                    notebook_id=source.id,
                    fields="id,parent_id,title",
                    page=page
                ).items
                if not notes_batch:
                    break
                notes.extend(notes_batch)
                page += 1

            for note in notes:
                try:
                    api.modify_note(note.id, parent_id=target.id)
                    moved_count += 1
                    # Update notes count
                    notes_count_map[source.id] -= 1
                    notes_count_map[target.id] += 1
                except Exception as e:
                    print(f"Failed to move note {note.title}: {str(e)}")

    return moved_count
            
    
def update_hierarchy_maps(sources, target, parent_map, notes_count_map, moved_count):
    """Update our local hierarchy maps after merge operations"""
    # Remove sources from parent_map
    for source in sources:
        # Remove from parent's children list
        if source.parent_id in parent_map:
            parent_map[source.parent_id] = [
                nb for nb in parent_map[source.parent_id] 
                if nb.id != source.id
            ]
        
        # Move children to target
        if source.id in parent_map:
            target_children = parent_map.get(target.id, [])
            target_children.extend(parent_map[source.id])
            parent_map[target.id] = target_children
            del parent_map[source.id]

    # Update notes count for target
    target_notes = sum(notes_count_map.pop(src.id, 0) for src in sources)
    notes_count_map[target.id] += target_notes

def print_notebook_tree(api, notebook_map, parent_map, notes_count_map, highlight_ids=None, parent_id='', level=0):
    """Print hierarchy tree using our local maps with merge highlights"""
    if highlight_ids is None:
        highlight_ids = []
    
    for nb in parent_map.get(parent_id, []):
        is_highlighted = nb.id in highlight_ids
        note_count = notes_count_map.get(nb.id, 0)
        sub_count = len(parent_map.get(nb.id, []))
        
        # Color codes for highlighting
        color_start = "\033[33m" if is_highlighted else ""
        color_end = "\033[0m" if is_highlighted else ""
        
        print(f"{'  ' * level}"
              f"{color_start}📂 {nb.title} "
              f"[notes: {note_count}, subs: {sub_count}]"
              f"{color_end}"
              f" {'-'*10}"
              f"{nb.id}"
              )
        
        print_notebook_tree(api, notebook_map, parent_map, notes_count_map, 
                           highlight_ids, nb.id, level + 1)

def select_target_notebook(notebooks):
    """Interactive target selection with hierarchy preview"""
    print("\nSelect target notebook to keep:")
    
    for i, nb in enumerate(notebooks, 1):
        print(f"{i}. {nb.title} (ID: {nb.id})")
    
    while True:
        try:
            choice = int(input("Enter choice (1-{}): ".format(len(notebooks))))
            if 1 <= choice <= len(notebooks):
                return notebooks[choice-1]
        except ValueError:
            print("Invalid input. Please enter a number.")

def confirm_action(prompt):
    """Get user confirmation with safety checks"""
    response = input(f"{prompt} [y/N] ").lower()
    return response == 'y'

def main_merge_flow(api):
    """Complete merge workflow entry point"""
    # Initial data loading
    all_notebooks = api.get_notebooks(fields="id,parent_id,title").items
    notebook_map = {nb.id: nb for nb in all_notebooks}
    
    # Build hierarchy maps
    parent_map = defaultdict(list)
    notes_count_map = {}
    for nb in all_notebooks:
        parent_map[nb.parent_id].append(nb)
        notes_count_map[nb.id] = len(api.get_notes(notebook_id=nb.id).items)
    
    duplicates = find_duplicate_notebooks(all_notebooks)
    
    if not duplicates:
        print("No duplicates found!")
        return
    
    # Interactive merge process
    for key, notebooks in duplicates.items():
        print(f"\n=== Processing duplicate group: {key.split('::')[0]} ===")
        print_notebook_tree(api, notebook_map, parent_map, notes_count_map, 
                           highlight_ids=[nb.id for nb in notebooks])
        
        if confirm_action("Process this duplicate group?"):
            target = select_target_notebook(notebooks)
            sources = [nb for nb in notebooks if nb.id != target.id]
            
            # Show detailed preview using our maps
            total_notes = sum(notes_count_map[nb.id] for nb in sources)
            total_subs = sum(len(parent_map[nb.id]) for nb in sources)
            print(f"\nMerge will affect:")
            print(f"- {total_notes} notes across {len(sources)} notebooks")
            print(f"- {total_subs} subnotebook hierarchies")
            
            if confirm_action("Confirm merge"):
                moved_count = hierarchy_aware_merge(
                    api, sources, target, parent_map, notes_count_map
                )
                update_hierarchy_maps(sources, target, parent_map, notes_count_map, moved_count)
                print("\nUpdated hierarchy:")
                print_notebook_tree(api, notebook_map, parent_map, notes_count_map)
