# Batch Alembic Repath – Maya Tool

## Overview
This tool automates the process of fixing broken Alembic file paths in Autodesk Maya.  
When moving projects between machines or directories, Alembic caches often break.  
Instead of reconnecting them manually, this tool provides a simple UI to batch-repath all Alembics automatically.

## Features
- Simple PySide/PyQt-based UI.
- Select scenes folder, new Alembics folder, and output report file.
- Option to overwrite original scenes or create fixed copies.
- Logs process output in real time.
- Generates a text report of fixed paths.
- Runs through **mayapy** for batch automation.

## Requirements
- Maya with `mayapy` (tested with Maya 2022+).
- Python 3.x (bundled with Maya).
- PySide6, PySide2, or PyQt5 (the tool picks whichever is available).

## Installation
1. Clone or download this repository.
2. Place the `repath_ui.py` and `repath.py` in the same folder.
3. Optional: Add this folder to your Maya scripts path.

## Usage
1. Run UI launcher file `Launch_Batch_Alembic_Repath_tool.bat`
2. Tool runs through bash
