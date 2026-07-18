# Curvature Console

Curvature Console is a standalone internal development application for Project Curvature.

It coordinates three permanent and equal departments:

- Curvature Project
- Curvature Core
- Curvature Research

The application is separate from Curvature Platform, World Core, Chronicle Client and gameplay.

## Current state

ASSISTANT-001B1 — Repository and Application Foundation is complete and verified.

Verified:

- standalone repository created
- dedicated Conda environment created
- package installs in editable mode
- PySide6 desktop application launches
- automated tests pass
- application entry point works

## Environment rule

PySide6 and its Qt runtime must be installed through Conda Forge.

Do not install PySide6 through pip in this environment.

The working Linux configuration is:

```text
Conda:
- Python
- PySide6
- PyYAML
- pytest

pip:
- Curvature Console package only, editable and without dependencies
```

This avoids mixing pip-provided Qt binaries with Conda-provided XCB libraries.

## Create the environment

```bash
conda env create -f environment.yml
conda activate curvature-console
```

## Repair or update an existing environment

```bash
conda activate curvature-console

conda install -c conda-forge   pyside6   pyyaml   pytest   xcb-util-cursor   libxcb   xorg-libxcursor   -y

python -m pip install -e . --no-deps
```

## Run

```bash
python -m curvature_console.main
```

or:

```bash
curvature-console
```

## Test

```bash
python -m pytest -v
```

Expected current result:

```text
2 passed
```

## Project repository

The initial Project Curvature repository is:

```text
~/Curvature
```

Repository access remains read-only during the MVP.

## Next milestone

ASSISTANT-001B2 — Three-Panel Desktop Shell
