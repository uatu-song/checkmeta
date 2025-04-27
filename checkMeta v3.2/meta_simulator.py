import os
import ast
import importlib.util
import re
import copy
import statistics
from collections import defaultdict

# CONFIGURATION
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SYSTEMS_DIR = os.path.join(BASE_DIR, "systems")
UTILS_DIR = os.path.join(BASE_DIR, "utils")
MAIN_SIMULATOR = os.path.join(BASE_DIR, "meta_simulator.py")
REPORTS_DIR = os.path.join(BASE_DIR, "build", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)
REPORT_FILE = os.path.join(REPORTS_DIR, "validation_report.txt")

# FILES TO ANALYZE
analysis_files = [
    MAIN_SIMULATOR,
] + sorted(
    [os.path.join(SYSTEMS_DIR, f) for f in os.listdir(SYSTEMS_DIR) if f.endswith(".py")]
) + sorted(
    [os.path.join(UTILS_DIR, f) for f in os.listdir(UTILS_DIR) if f.endswith(".py")]
)

def collect_info(file_path):
    imports = []
    classes = []
    functions = []
    constants = []
    calls = []
    attributes = []
    local_imports = []
    file_content = ""

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            node = ast.parse(file_content, filename=file_path)
    except (SyntaxError, IndentationError) as e:
        return None, str(e), file_content

    for n in ast.walk(node):
        if isinstance(n, ast.Import) or isinstance(n, ast.ImportFrom):
            for alias in n.names:
                imports.append(alias.name)
            if isinstance(n, ast.ImportFrom) and n.module and (n.module.startswith("systems") or n.module.startswith("utils")):
                local_imports.append(n.module)
        elif isinstance(n, ast.ClassDef):
            classes.append(n.name)
        elif isinstance(n, ast.FunctionDef):
            arg_count = len(n.args.args) - 1 if n.args.args and n.args.args[0].arg == 'self' else len(n.args.args)
            functions.append((n.name, arg_count))
        elif isinstance(n, ast.Assign):
            for target in n.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    constants.append(target.id)
        elif isinstance(n, ast.Call):
            if isinstance(n.func, ast.Name):
                calls.append((n.func.id, len(n.args)))
            elif isinstance(n.func, ast.Attribute):
                attributes.append((n.func.attr, len(n.args)))

    return (imports, classes, functions, constants, calls, attributes, local_imports), None, file_content


def main():
    all_imports = defaultdict(list)
    all_classes = defaultdict(list)
    all_functions = defaultdict(list)
    all_constants = defaultdict(list)
    all_calls = []
    all_attributes = []
    collected_imports = []
    syntax_errors = []
    local_import_graph = defaultdict(list)
    all_file_contents = {}
    report_lines = []

    print("Analyzing files:\n")

    for file_path in analysis_files:
        module_name = os.path.relpath(file_path, BASE_DIR).replace(os.sep, ".").replace(".py", "")
        print(f"- {module_name}")
        result, error, content = collect_info(file_path)

        if error:
            syntax_errors.append((module_name, error))
            continue

        imports, classes, functions, constants, calls, attributes, local_imports = result
        all_file_contents[module_name] = content

        for item in imports:
            all_imports[item].append(module_name)
        for item in classes:
            all_classes[item].append(module_name)
        for func, argc in functions:
            all_functions[func].append((module_name, argc))
        for item in constants:
            all_constants[item].append(module_name)
        all_calls.extend(calls)
        all_attributes.extend(attributes)
        for local_import in local_imports:
            local_import_graph[module_name].append(local_import)

    report_lines.append("===== Validation Report =====\n")

    # Syntax errors
    report_lines.append("Critical: Syntax or Indentation Errors:")
    if syntax_errors:
        for module_name, error in syntax_errors:
            report_lines.append(f"  [!] {module_name}: {error}")
    else:
        report_lines.append("  None found.")

    # Duplicate class/function/constant checks
    report_lines.append("\nWarning: Duplicate Classes:")
    for cls, locations in all_classes.items():
        if len(locations) > 1:
            report_lines.append(f"  [!] Class '{cls}' found in: {locations}")

    report_lines.append("\nWarning: Duplicate Functions:")
    for func, locations in all_functions.items():
        if len(locations) > 1:
            report_lines.append(f"  [!] Function '{func}' found in: {[loc for loc, _ in locations]}")

    report_lines.append("\nWarning: Duplicate Constants:")
    for const, locations in all_constants.items():
        if len(locations) > 1:
            report_lines.append(f"  [!] Constant '{const}' found in: {locations}")

    # Save report
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    print("\nValidation completed.")
    print(f"Validation report saved at {REPORT_FILE}\n")


if __name__ == "__main__":
    main()
