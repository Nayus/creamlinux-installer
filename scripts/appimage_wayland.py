#!/usr/bin/env python3
"""Use host Wayland libraries with host Mesa, without stripping WebKit/GTK.

Bundled Ubuntu Wayland can lack symbols (e.g. wl_fixes_interface) required
by newer host EGL drivers. Never mix that old client with the host driver.
"""
import argparse
from pathlib import Path

LIBRARIES = tuple(f"libwayland-{name}.so" for name in ("client", "server", "cursor", "egl"))


def bundled_libraries(root):
    """Find only the four Wayland shared libraries, including symlinks."""
    return sorted(
        path for path in root.rglob("libwayland-*.so*")
        if any(path.name == name or path.name.startswith(name + ".") for name in LIBRARIES)
    )


def prepare(root, check_only=False):
    root = root.resolve(strict=True)
    if root == Path(root.anchor) or not (root / "AppRun").exists() or not (root / "usr/bin/creamlinux").is_file():
        raise ValueError(f"Not a Creamlinux AppDir: {root}")
    paths = bundled_libraries(root)
    if check_only:
        if paths:
            raise RuntimeError(f"Bundled Wayland would override host Mesa dependencies: {paths}")
        print(f"Verified host Wayland policy: {root}")
        return
    # Validate every unlink location first. Unlink a symlink itself, never its
    # target; do not follow a directory symlink outside the explicit AppDir.
    for path in paths:
        if not path.parent.resolve(strict=True).is_relative_to(root) or path.is_dir():
            raise ValueError(f"Unsafe Wayland removal location: {path}")
    for path in paths:
        print(f"Remove bundled Wayland entry: {path.absolute()}")
        path.unlink()
    prepare(root, check_only=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("strip", "check"))
    parser.add_argument("appdir", type=Path)
    args = parser.parse_args()
    prepare(args.appdir, check_only=args.action == "check")
