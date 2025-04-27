import os
import ast
import importlib.util
import re
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


def check_imports(imports):
    broken_imports = []
    for imp in imports:
        if not is_module_available(imp):
            broken_imports.append(imp)
    return broken_imports


def is_module_available(module_name):
    try:
        spec = importlib.util.find_spec(module_name)
        return spec is not None
    except (ModuleNotFoundError, ValueError):
        return False


def detect_circular_imports(local_import_graph):
    visited = set()
    stack = set()

    def visit(module):
        if module in stack:
            return True
        if module in visited:
            return False

        visited.add(module)
        stack.add(module)
        for neighbor in local_import_graph.get(module, []):
            if visit(neighbor):
                return True
        stack.remove(module)
        return False

    for module in local_import_graph:
        if visit(module):
            return True
    return False


def run_policy_checks(all_file_contents):
    policy_warnings = defaultdict(list)

    for filename, content in all_file_contents.items():
        # Check for hardcoded paths or numbers
        if re.search(r'("/|\\/|\.csv|\.json|\.pgn|\.txt")', content):
            policy_warnings['Config Usage'].append(f"[!] Hardcoded path or filetype found in {filename}")

        # Check for mixed date formats
        if re.search(r'(\d{2}/\d{2}/\d{4})', content):
            policy_warnings['Date Format'].append(f"[!] MM/DD/YYYY format found in {filename}")

        # Check for unsafe except blocks
        if re.search(r'except\s*:', content):
            policy_warnings['Error Handling'].append(f"[!] Bare except block found in {filename}")

        # Check for incorrect team_id casing
        if re.search(r'team_id\s*[!=]=\s*\".*\"', content):
            policy_warnings['Team ID Handling'].append(f"[!] Potential team_id casing inconsistency in {filename}")

        # Check if SynergyTracker is improperly forced
        if 'SynergyTracker' in content and 'SYNERGY_AVAILABLE' not in content:
            policy_warnings['Synergy Stub'].append(f"[!] SynergyTracker referenced without fallback check in {filename}")

    return policy_warnings


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

        collected_imports.extend(imports)

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

    # Duplicate class names
    report_lines.append("\nWarning: Duplicate Classes:")
    for cls, locations in all_classes.items():
        if len(locations) > 1:
            report_lines.append(f"  [!] Class '{cls}' found in: {locations}")

    # Duplicate function names
    report_lines.append("\nWarning: Duplicate Functions:")
    for func, locations in all_functions.items():
        if len(locations) > 1:
            report_lines.append(f"  [!] Function '{func}' found in: {[loc for loc, _ in locations]}")

    # Duplicate constants
    report_lines.append("\nWarning: Duplicate Constants:")
    for const, locations in all_constants.items():
        if len(locations) > 1:
            report_lines.append(f"  [!] Constant '{const}' found in: {locations}")

    # Broken imports
    report_lines.append("\nCritical: Broken Imports:")
    broken = check_imports(set(collected_imports))
    if broken:
        for imp in broken:
            report_lines.append(f"  [!] Import '{imp}' not found")
    else:
        report_lines.append("  None found.")

    # Missing function calls and argument mismatches
    report_lines.append("\nCritical: Missing Called Functions or Argument Mismatches:")
    function_signatures = {func: argc for func, locations in all_functions.items() for _, argc in locations}
    missing_calls = []
    arg_mismatches = []

    for call_name, argc in all_calls:
        if call_name not in function_signatures:
            missing_calls.append(call_name)
        else:
            expected_argc = function_signatures[call_name]
            if argc != expected_argc:
                arg_mismatches.append((call_name, expected_argc, argc))

    if missing_calls:
        for call in set(missing_calls):
            report_lines.append(f"  [!] Function call to '{call}' not defined anywhere")
    else:
        report_lines.append("  None found.")

    if arg_mismatches:
        for func, expected, actual in arg_mismatches:
            report_lines.append(f"  [!] Function '{func}' called with {actual} args but defined with {expected} args")

    # Missing attributes
    report_lines.append("\nCritical: Missing Attribute Calls:")
    attribute_names = set(all_functions.keys())
    missing_attrs = []
    for attr, _ in all_attributes:
        if attr not in attribute_names:
            missing_attrs.append(attr)

    if missing_attrs:
        for attr in set(missing_attrs):
            report_lines.append(f"  [!] Attribute call to '{attr}' not defined anywhere")
    else:
        report_lines.append("  None found.")

    # Circular imports
    report_lines.append("\nCritical: Circular Imports:")
    if detect_circular_imports(local_import_graph):
        report_lines.append("  [!] Circular import detected in local systems/utils modules")
    else:
        report_lines.append("  None found.")

    # Advanced Policy Validation
    report_lines.append("\n===== Policy Validation =====\n")
    policy_results = run_policy_checks(all_file_contents)
    if not policy_results:
        report_lines.append("  No policy violations found.")
    else:
        for policy, issues in policy_results.items():
            report_lines.append(f"{policy} Warnings:")
            for issue in issues:
                report_lines.append(f"  {issue}")

    report_lines.append("\n===== End of Report =====\n")

    # Print and save the report
    print("\n".join(report_lines))

    with open(REPORT_FILE, "w", encoding="utf-8") as report_file:
        report_file.write("\n".join(report_lines))

    print(f"\nValidation report saved to {REPORT_FILE}\n")


if __name__ == "__main__":
    main()