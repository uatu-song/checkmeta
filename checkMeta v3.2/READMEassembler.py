README for Build System (assembler.py)
Build System for checkMeta v3.2+
This repository includes a build system designed to:

Assemble all core modules (systems/, utils/, meta_simulator.py) into a single, full simulator script (meta_simulator_full.py).

Auto-format the assembled output to meet clean PEP8 style (indentation, spacing, etc.).

Run static analysis (pylint) to catch broken imports, bad calls, code smells.

Run type checking (mypy) to ensure type correctness across all modules.

How It Works
Assembler:

Combines meta_simulator.py + systems/*.py + utils/*.py into a single file.

Inserts clear module separators.

Formatter:

Formats the output using black for style consistency.

Static Analyzers:

Runs pylint and mypy on the full script to catch issues automatically.

Setup
Install required tools if you don't have them yet:

bash
Copy
Edit
pip install black pylint mypy
Usage
From the project root, simply run:

bash
Copy
Edit
python assembler.py
This will:

Assemble all modules.

Format meta_simulator_full.py.

Validate it with pylint and mypy.

Output
Assembled file: meta_simulator_full.py

Logs printed in terminal for formatting, linting, type checking.

Notes
Assembler is non-destructive: it does not modify your source modules.

Static analyzers may show warnings — not every warning is critical, but fix all errors before production deployment.

Planned future upgrades include optional test automation and build version tagging.

