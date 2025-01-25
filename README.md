# Joplin Notebook Manager

A powerful toolkit for managing Joplin notebooks and notes, featuring duplicate detection, hierarchical merging, and cleanup utilities.

![Joplin Logo](https://raw.githubusercontent.com/laurent22/joplin/dev/Assets/LinuxIcons/256x256.png)

## Features

- 🗑️ Delete duplicate notes with side-by-side comparison
- 📚 Merge duplicate notebook hierarchies
- 🧹 Clean empty notebooks
- 🌳 Visualize notebook hierarchy
- 🔍 Find similar notebooks by name
- 🛡️ Safety confirmations for destructive operations

## Installation

**Prerequisites:**
- Python 3+
- [Joplin](https://joplinapp.org/) installed and running
- Joplin Web Clipper enabled

## Clone repository
    git clone https://github.com/yourusername/joplin-notebook-manager.git
    cd joplin-notebook-manager

## Create virtual environment (recommended)
    python -m venv venv

## Activate environment
### Linux/macOS:
    source venv/bin/activate
### Windows:
    .\venv\Scripts\activate

## Install dependencies
    pip install -r requirements.txt

## Configuration

1. Enable Web Clipper in Joplin:
  Go to Tools > Web Clipper Options
    Enable Web Clipper and note the authorization token

## Usage
    python main.py

## Safety Features

  🔄 Multiple confirmation prompts for destructive operations

  🗂️ Moves items to "Google_keep_to_be_deleted" before deletion

  👁️ Visual previews before making changes

  ⏮️ Undo capability through Joplin's trash system

  🔒 Token is never stored - set it each session or use environment variables

## Screenshots:

### Example of '1. Find & Manage Duplicate Notes'
![Screenshot from 2025-01-25 23-59-14](https://github.com/user-attachments/assets/db323743-8921-419b-8575-dc6e68ff62d5)

### Example of '2. Find & Merge Duplicate Notebooks '
![Screenshot from 2025-01-25 23-51-49](https://github.com/user-attachments/assets/53904044-38a9-4561-a1b3-8f53106c4503)

![Screenshot from 2025-01-26 00-27-36](https://github.com/user-attachments/assets/65811635-a4d4-463c-9309-40c854260245)

### Example of '3. Find & Delete Empty Notebooks'

![Screenshot from 2025-01-26 00-00-50](https://github.com/user-attachments/assets/29629f2c-173c-4e5e-8ae2-2316e7000a0f)

### Example of '5. View Notebook Hierarchy'

![Screenshot from 2025-01-26 00-05-02](https://github.com/user-attachments/assets/2c6fa9e5-0422-475c-95d3-37724823d559)
