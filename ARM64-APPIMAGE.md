# ARM64 AppImage: host Wayland / bundled WebKit

Run the manual **Build and Release (ARM64)** workflow. Keep `bundle-webkit=true`
(the default). Both values of `inject-dmabuf-disable` apply the Wayland fix.

## Why the packaging differs from upstream

On Fedora-based Armada with Mesa 26.2.4 / Wayland 1.26, the Ubuntu-built
AppImage's old Wayland client overrides the host library through
`LD_LIBRARY_PATH`. Loading the host EGL driver then fails with:

```text
libEGL_mesa.so.0: undefined symbol: wl_fixes_interface
Could not create default EGL display: EGL_BAD_PARAMETER. Aborting...
```

The GTK window stays open, but its WebKit page subprocess aborts, leaving a
blank window. Disabling DMA-BUF alone does not resolve this library conflict.
Host EGL and the actual application GUI were confirmed to work when the host
Wayland client was used instead of the bundled copy.

The workflow now always removes **only** bundled shared libraries in these
four families, including versioned files and symlinks in multiarch folders:

- `libwayland-client.so*`
- `libwayland-server.so*`
- `libwayland-cursor.so*`
- `libwayland-egl.so*`

It keeps WebKitGTK/JSC, GTK/GDK, GLib, WebKit helpers, the original AppRun chain
and GTK hooks. The AppImage uses host Wayland libraries naturally; no external
`LD_PRELOAD`, absolute Fedora library path, or compatibility launcher is needed.
This assumes the host provides the Wayland libraries alongside its graphics
stack. It does **not** make the AppImage compatible with every Linux system.

## Checks and reproducibility

- Fixture tests check narrow removal, symlinks, non-Wayland preservation and
  path safety; final-image checks reject remaining Wayland entries, even
  dangling symlinks.
- Extraction/repacking preserves the original AppImage runtime. Launcher and
  hook comparisons detect startup-chain changes.
- The default bundled mode verifies that GTK/GDK/WebKit/JSC/GLib and AArch64
  helpers still exist. These CI checks are structural, not a desktop GUI test.
- Releases include `SHA256SUMS` and `ARM64-BUILD.txt` with the exact commit and
  Actions run. Same-version rebuilds replace existing release attachments;
  download them again and check the hash instead of reusing an old copy.

Run the downloaded AppImage directly:

```bash
chmod +x Creamlinux_1.7.1_aarch64.AppImage
./Creamlinux_1.7.1_aarch64.AppImage
```

The optional `bundle-webkit=false` mode still strips much more and requires
matching host GTK/WebKit dependencies. It is not the intended solution here.
RPM and DEB packaging is unchanged by this AppImage-specific fix.
