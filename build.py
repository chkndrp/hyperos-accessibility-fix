#!/usr/bin/env python3

"""Build script for the module/ directory"""

#  Stop HyperOS from randomly disabling accessibility services
#  Copyright (C) 2026 chkndrp
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License version 2 as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along
#  with this program; if not, see <https://www.gnu.org/licenses/>.

import re
import shutil
import tempfile
import zipfile

from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODULE_DIR = ROOT / "module"
PACKAGE_FILES = ("LICENSE", "README.md", "CHANGELOG.md", "update.json")

MODULE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
VERSION_PATTERN = re.compile(r"[0-9]+(?:\.[0-9]+)*\Z")


def read_module_metadata() -> tuple[str, str]:
    """Reads and validates the module ID & version from module.prop."""

    module_prop = MODULE_DIR / "module.prop"
    if not module_prop.is_file():
        raise FileNotFoundError(f"Missing {module_prop}")

    properties: dict[str, list[str]] = {"id": [], "version": []}
    for line in module_prop.read_text(encoding="utf-8").splitlines():
        key, separator, value = line.partition("=")
        key = key.strip()

        if separator and key in properties:
            properties[key].append(value.strip())

    module_ids = properties["id"]
    if len(module_ids) != 1 or not MODULE_ID_PATTERN.fullmatch(module_ids[0]):
        raise ValueError(f"Invalid or missing ID in {module_prop}")

    versions = properties["version"]
    if len(versions) != 1 or not VERSION_PATTERN.fullmatch(versions[0]):
        raise ValueError(f"Invalid or missing version in {module_prop}")

    return module_ids[0], versions[0]


def main() -> None:
    """Builds a zip archive of the module directory."""

    module_id, version = read_module_metadata()

    required_files = [ROOT / name for name in PACKAGE_FILES]
    missing_files = [path for path in required_files if not path.is_file()]

    if missing_files:
        missing = ", ".join(str(path) for path in missing_files)
        raise FileNotFoundError(f"Missing package file(s): {missing}")

    build_dir = ROOT / "build"
    build_dir.mkdir(exist_ok=True)

    archive_path = build_dir / f"{module_id}-{version}.zip"
    permalink_path = build_dir / "hyperos-accessibility-fix.zip"

    with tempfile.TemporaryDirectory(prefix=f"{module_id}-") as temp:
        temp_dir = Path(temp)

        for item in MODULE_DIR.iterdir():
            destination = temp_dir / item.name

            if item.is_dir():
                shutil.copytree(item, destination)
            else:
                shutil.copy2(item, destination)

        for source in required_files:
            shutil.copy2(source, temp_dir / source.name)

        with zipfile.ZipFile(archive_path,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
        ) as archive:
            for path in sorted(temp_dir.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(temp_dir).as_posix())
                elif not any(path.iterdir()):
                    archive.write(path, path.relative_to(temp_dir).as_posix() + "/")

    shutil.copy2(archive_path, permalink_path)

    print(f"Created {archive_path}")
    print(f"Created {permalink_path} (for permalink purposes)")


if __name__ == "__main__":
    main()
