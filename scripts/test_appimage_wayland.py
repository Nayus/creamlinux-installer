"""Packaging regression fixtures; actual desktop execution is tested separately."""
from pathlib import Path
import tempfile
import unittest

from appimage_wayland import LIBRARIES, bundled_libraries, prepare


class WaylandPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "AppDir with spaces"
        (self.root / "usr/bin").mkdir(parents=True)
        (self.root / "usr/bin/creamlinux").write_bytes(b"app fixture")
        (self.root / "AppRun").write_text("original startup chain")

    def add_file(self, relative):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
        return path

    def test_nested_versions_removed_and_other_files_untouched(self):
        kept = [self.root / "AppRun", self.root / "usr/bin/creamlinux"]
        for relative in ["usr/lib/libwebkit2gtk-4.1.so.0", "usr/lib/libgtk-3.so.0",
                         "usr/lib/libgdk-3.so.0", "usr/lib/libglib-2.0.so.0",
                         "usr/lib/libjavascriptcoregtk-4.1.so.0", "usr/lib/libEGL.so.1",
                         "usr/lib/libwayland-client.software.so", "AppRun.wrapped",
                         "apprun-hooks/linuxdeploy-plugin-gtk.sh",
                         "usr/lib/aarch64-linux-gnu/webkit2gtk-4.1/WebKitWebProcess"]:
            kept.append(self.add_file(relative))
        before = {p: p.read_bytes() for p in kept}
        for directory in ["usr/lib", "usr/lib/aarch64-linux-gnu", "lib64"]:
            for library in LIBRARIES:
                real = self.add_file(f"{directory}/{library}.0.22.0")
                real.with_name(library + ".0").symlink_to(real.name)
                real.with_name(library).symlink_to(real.name)
        prepare(self.root)
        self.assertEqual(bundled_libraries(self.root), [])
        self.assertEqual(before, {p: p.read_bytes() for p in kept})

    def test_dangling_symlink_detected_and_removed(self):
        lib = self.root / "usr/lib/libwayland-client.so.0"
        lib.parent.mkdir(parents=True)
        lib.symlink_to("missing-wayland.so")
        with self.assertRaises(RuntimeError):
            prepare(self.root, check_only=True)
        prepare(self.root)
        self.assertFalse(lib.is_symlink())

    def test_unlink_does_not_touch_external_symlink_target(self):
        external = Path(self.temp.name) / "host-library"
        external.write_bytes(b"never delete host libraries")
        lib = self.root / "usr/lib/libwayland-client.so.0"
        lib.parent.mkdir(parents=True)
        lib.symlink_to(external)
        prepare(self.root)
        self.assertEqual(external.read_bytes(), b"never delete host libraries")

    def test_noop_when_host_wayland_already_used(self):
        prepare(self.root)
        prepare(self.root, check_only=True)

    def test_refuses_non_appdir(self):
        with self.assertRaises(ValueError):
            prepare(Path(self.temp.name))

    def test_refuses_library_directory_without_deleting_other_entries(self):
        candidate = self.root / "usr/lib/libwayland-client.so.0"
        candidate.mkdir(parents=True)
        with self.assertRaises(ValueError):
            prepare(self.root)
        self.assertTrue(candidate.is_dir())


if __name__ == "__main__":
    unittest.main()
