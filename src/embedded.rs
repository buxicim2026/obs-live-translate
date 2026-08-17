//! Compile-time embedded assets. We embed the entire `dist/` directory
//! (overlay, admin, default config, launchers) into the binary so the
//! final distributable is a SINGLE file. End users do not need to copy
//! any folder or install any extra files.
//!
//! At runtime we prefer the on-disk `dist/` if the user has put one next
//! to the binary (so they can customise HTML/CSS/JS), and fall back to
//! the embedded version otherwise.

use include_dir::{include_dir, Dir};

/// The default `config.toml` template.
pub const DEFAULT_CONFIG: &str = include_str!("../dist/config.toml");

/// The bundled HTML/CSS/JS for the admin panel and the browser-source
/// overlay. Served at /, /admin, /overlay, /admin-assets/*, /overlay-assets/*.
pub static DIST: Dir<'_> = include_dir!("$CARGO_MANIFEST_DIR/dist");

/// Read an embedded file as bytes.
pub fn read(path: &str) -> Option<&'static [u8]> {
    DIST.get_file(path).map(|f| f.contents())
}

/// Read an embedded file as UTF-8 text.
pub fn read_str(path: &str) -> Option<&'static str> {
    DIST.get_file(path).and_then(|f| f.contents_utf8())
}
