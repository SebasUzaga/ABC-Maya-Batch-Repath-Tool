#repath_main.py
#script functional code


import os
import maya.standalone
import maya.cmds as cmds
from collections import defaultdict
from datetime import datetime
import argparse   

# === Parse CLI Arguments ===
parser = argparse.ArgumentParser(description="Batch Alembic repath tool")
parser.add_argument("--scenes", required=True, help="Folder with Maya scenes (.ma/.mb)")
parser.add_argument("--new", required=True, dest="new_alembics", help="Folder with new Alembic caches")
parser.add_argument("--overwrite", action="store_true", help="Overwrite scenes instead of saving copies")
parser.add_argument("--report", default=None, help="Optional: path for report file")
args = parser.parse_args()

SCENE_FOLDER = args.scenes
NEW_ABC_PATH = args.new_alembics.replace("\\", "/").rstrip("/")
OVERWRITE = args.overwrite

# Dictionary: { scene_path: [(node, new_path) }
UPDATED_NODES = defaultdict(list)

if args.report:
    if os.path.isdir(args.report):
        REPORT_FILE = os.path.join(args.report, "alembic_repath_report.txt")
    else:
        REPORT_FILE = args.report  
else:
    REPORT_FILE = os.path.join(SCENE_FOLDER, "alembic_repath_report.txt")

def fix_alembic_paths_in_scene(scene_path):
    print(f"\nOpening scene: {scene_path}")
    try:
        cmds.file(scene_path, open=True, force=True)
        abc_nodes = cmds.ls(type="AlembicNode")

        if not abc_nodes:
            print("  No Alembic nodes found.")
        else:
            for node in abc_nodes:
                current_path = cmds.getAttr(f"{node}.abc_File")
                if not current_path:
                    print(f"  {node}: Empty path, skipped.")
                    continue

                file_name = os.path.basename(current_path)
                new_path = f"{NEW_ABC_PATH}/{file_name}"

                if current_path != new_path:
                    cmds.setAttr(f"{node}.abc_File", new_path, type="string")
                    print(f"  {node}: Updated path to {new_path}")
                    UPDATED_NODES[scene_path].append((node, new_path))

        if OVERWRITE:
            cmds.file(save=True, force=True)
            print("  Scene saved.")
        else:
            base, ext = os.path.splitext(scene_path)
            new_path = base + "_fixed" + ext
            cmds.file(rename=new_path)
            cmds.file(save=True, force=True)
            print(f"  Scene saved as: {new_path}")

    except Exception as e:
        print(f"  Error processing scene: {e}")

def write_report():
    try:
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(f"Alembic Repath Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 70 + "\n\n")
            if UPDATED_NODES:
                for scene, nodes in UPDATED_NODES.items():
                    f.write(f"{os.path.basename(scene)}\n")
                    for node, new_path in nodes:
                        f.write(f"    {node} -> {new_path}\n")
                    f.write("\n")
            else:
                f.write("No Alembic paths were updated.\n")
            f.flush()  
            os.fsync(f.fileno()) 
        print(f"\nReport saved to: {REPORT_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to write report: {e}")

def main():
    maya.standalone.initialize(name='python')

    try:
        cmds.loadPlugin("AbcImport", quiet=True)
    except Exception as e:
        print(f"[WARN] Could not load Alembic plugin: {e}")

    for filename in os.listdir(SCENE_FOLDER):
        if filename.endswith(".ma") or filename.endswith(".mb"):
            scene_path = os.path.join(SCENE_FOLDER, filename)
            fix_alembic_paths_in_scene(scene_path)

    

    print("\n=== Batch process completed ===")
    if UPDATED_NODES:
        print("\nRepathed Alembic nodes:")
        for scene, nodes in UPDATED_NODES.items():
            print(f"{os.path.basename(scene)}")
            for node, new_path in nodes:
                print(f"    {node} -> {new_path}")
    else:
        print("No Alembic paths were updated.")

    write_report()

    try:
        maya.standalone.uninitialize()
    except Exception as e:
        print(f"[WARNING] Maya standalone shutdown issue: {e}")


if __name__ == "__main__":
    main()
