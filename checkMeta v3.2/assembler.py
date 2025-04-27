import os
import glob
import subprocess

# CONFIGURATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEMS_DIR = os.path.join(BASE_DIR, "systems")
UTILS_DIR = os.path.join(BASE_DIR, "utils")
MAIN_SIMULATOR = os.path.join(BASE_DIR, "meta_simulator.py")
OUTPUT_FILE = os.path.join(BASE_DIR, "meta_simulator_full.py")

# ORDER MATTERS - DEFINE THE FILES TO ASSEMBLE IN SEQUENCE
assembly_order = [
    MAIN_SIMULATOR,
] + sorted(glob.glob(os.path.join(SYSTEMS_DIR, "*.py"))) + sorted(glob.glob(os.path.join(UTILS_DIR, "*.py")))


def assemble_modules(output_path, files_to_assemble):
    with open(output_path, "w", encoding="utf-8") as outfile:
        for file_path in files_to_assemble:
            module_name = os.path.relpath(file_path, BASE_DIR)
            outfile.write(f"\n\n# ==== MODULE: {module_name} ====" + "\n\n")
            with open(file_path, "r", encoding="utf-8") as infile:
                content = infile.read()
                outfile.write(content)
                outfile.write("\n\n")
    print(f"Successfully assembled {len(files_to_assemble)} modules into {output_path}")


def format_with_black(file_path):
    try:
        subprocess.run(["black", file_path], check=True)
        print(f"Formatted {file_path} with black.")
    except Exception as e:
        print(f"Formatting failed: {e}")


def run_static_analysis(file_path):
    print("\nRunning pylint...")
    try:
        subprocess.run(["pylint", file_path], check=True)
    except subprocess.CalledProcessError:
        print("pylint found issues.")

    print("\nRunning mypy...")
    try:
        subprocess.run(["mypy", file_path], check=True)
    except subprocess.CalledProcessError:
        print("mypy found issues.")


if __name__ == "__main__":
    assemble_modules(OUTPUT_FILE, assembly_order)
    format_with_black(OUTPUT_FILE)
    run_static_analysis(OUTPUT_FILE)
