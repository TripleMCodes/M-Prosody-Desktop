"""
updater.py — App update system for Lyrical Lab
================================================
Works alongside MigrationManager:
  1. This module handles fetching & installing new app versions.
  2. MigrationManager handles evolving the DB schema after an update.

Typical flow:
  - App launches → check for update → if found, download & install
  - On next launch, new binary runs → MigrationManager applies any new DB migrations

How to publish an update (your side as developer):
  - Host a `version.json` file at a stable URL (e.g. GitHub Releases or your own server)
  - Upload the new binary/zip to the URL listed in version.json
  - Users' apps will find it automatically on next launch

version.json shape (host this at VERSION_URL):
  {
    "version": "1.2.0",
    "download_url": "https://yoursite.com/releases/lyrical_lab_1.2.0.zip",
    "release_notes": "Bug fixes and new chord tools",
    "min_compatible_db_version": "1.1.0"   ← optional safety check
  }
"""

import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.DEBUG)

# ── Configuration ────────────────────────────────────────────────────────────

# URL where you host the latest version metadata (change to your own URL)
VERSION_URL = "https://yoursite.com/releases/version.json"

# Where the app lives on disk (adjust to your actual install path)
APP_DIR = Path(__file__).parent

# Current running version (bump this manually per release)
CURRENT_VERSION = "1.0.0"


# ── Version helpers ───────────────────────────────────────────────────────────

def parse_version(version_str: str) -> tuple[int, ...]:
    """'1.2.3' → (1, 2, 3) for easy comparison."""
    return tuple(int(x) for x in version_str.strip().split("."))


def is_newer(remote: str, local: str) -> bool:
    """Return True if remote version is strictly greater than local."""
    return parse_version(remote) > parse_version(local)


# ── Remote version check ──────────────────────────────────────────────────────

def fetch_version_info(url: str = VERSION_URL, timeout: int = 10) -> Optional[dict]:
    """
    Download version.json from your server.
    Returns parsed dict or None on any network/parse error.
    """
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode())
            logging.debug(f"Remote version info: {data}")
            return data
    except urllib.error.URLError as e:
        logging.warning(f"Could not reach update server: {e}")
        return None
    except json.JSONDecodeError as e:
        logging.error(f"Invalid version.json format: {e}")
        return None


# ── Download ──────────────────────────────────────────────────────────────────

def download_update(download_url: str, dest_dir: Path) -> Optional[Path]:
    """
    Download the update zip into a temp directory.
    Shows a simple progress log (swap for a GUI progress bar if you have one).
    Returns path to downloaded file, or None on failure.
    """
    filename = download_url.split("/")[-1]
    dest_path = dest_dir / filename

    logging.info(f"Downloading update from {download_url} …")

    try:
        def _log_progress(block_count, block_size, total_size):
            if total_size > 0:
                pct = min(block_count * block_size / total_size * 100, 100)
                # Replace with a real progress callback / GUI hook as needed
                print(f"\r  Downloading… {pct:.1f}%", end="", flush=True)

        urllib.request.urlretrieve(download_url, dest_path, reporthook=_log_progress)
        print()  # newline after progress
        logging.info(f"Download complete: {dest_path}")
        return dest_path

    except urllib.error.URLError as e:
        logging.error(f"Download failed: {e}")
        return None


# ── Install ───────────────────────────────────────────────────────────────────

def backup_current_app(app_dir: Path) -> Path:
    """Copy current app dir to a .bak sibling before overwriting."""
    backup_dir = app_dir.parent / (app_dir.name + ".bak")
    if backup_dir.exists():
        shutil.rmtree(backup_dir)
    shutil.copytree(app_dir, backup_dir)
    logging.info(f"App backed up to: {backup_dir}")
    return backup_dir


def install_update(zip_path: Path, app_dir: Path) -> bool:
    """
    Extract the downloaded zip over the app directory.

    Expected zip layout:
      lyrical_lab_1.2.0/
        main.py
        updater.py
        migration_manager.py
        assets/
        ...

    The top-level folder inside the zip is stripped so files land
    directly in app_dir.
    """
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            members = zf.namelist()

            # Detect and strip the top-level folder (if any)
            top_dirs = {m.split("/")[0] for m in members if "/" in m}
            strip_prefix = top_dirs.pop() + "/" if len(top_dirs) == 1 else ""

            for member in members:
                # Derive target path, stripping the prefix
                relative = member[len(strip_prefix):] if strip_prefix else member
                if not relative:
                    continue  # skip the root dir entry itself

                target = app_dir / relative

                if member.endswith("/"):
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, open(target, "wb") as dst:
                        shutil.copyfileobj(src, dst)

        logging.info("Update installed successfully.")
        return True

    except (zipfile.BadZipFile, OSError) as e:
        logging.error(f"Install failed: {e}")
        return False


def restore_backup(backup_dir: Path, app_dir: Path):
    """Roll back to the backup if installation went wrong."""
    if backup_dir.exists():
        shutil.rmtree(app_dir)
        shutil.copytree(backup_dir, app_dir)
        logging.warning("Rolled back to previous version.")


# ── Relaunch ──────────────────────────────────────────────────────────────────

def relaunch_app():
    """
    Restart the application after a successful update.
    Works for both .py scripts and frozen executables (PyInstaller).
    """
    if getattr(sys, "frozen", False):
        # Frozen PyInstaller executable
        executable = sys.executable
    else:
        # Running as plain Python script
        executable = sys.executable
        args = sys.argv[:]
        subprocess.Popen([executable] + args)
        sys.exit(0)

    os.execv(executable, [executable] + sys.argv[1:])


# ── Main entry point ──────────────────────────────────────────────────────────

def check_and_apply_update(
    current_version: str = CURRENT_VERSION,
    version_url: str = VERSION_URL,
    app_dir: Path = APP_DIR,
    auto_restart: bool = True,
) -> bool:
    """
    Full update flow. Call this near the top of your app's startup code.

    Returns True if an update was applied (app will restart if auto_restart=True),
    False if already up to date or if anything failed.

    Usage in your main.py:
        from updater import check_and_apply_update
        check_and_apply_update()   # silently skips if up to date
    """
    logging.info(f"Checking for updates (current: {current_version}) …")

    # 1. Fetch remote version metadata
    info = fetch_version_info(version_url)
    if not info:
        logging.info("Update check skipped (no network or bad response).")
        return False

    remote_version = info.get("version")
    download_url = info.get("download_url")

    if not remote_version or not download_url:
        logging.error("version.json is missing 'version' or 'download_url'.")
        return False

    # 2. Compare versions
    if not is_newer(remote_version, current_version):
        logging.info(f"Already up to date ({current_version}).")
        return False

    logging.info(f"New version available: {remote_version}")
    notes = info.get("release_notes", "")
    if notes:
        print(f"\n  What's new in {remote_version}: {notes}\n")

    # 3. Download into a temp dir (auto-cleaned up after)
    with tempfile.TemporaryDirectory() as tmp:
        zip_path = download_update(download_url, Path(tmp))
        if not zip_path:
            return False

        # 4. Back up current app
        backup_dir = backup_current_app(app_dir)

        # 5. Install
        success = install_update(zip_path, app_dir)

        if not success:
            restore_backup(backup_dir, app_dir)
            return False

    # 6. Relaunch so the new code takes effect
    if auto_restart:
        logging.info("Relaunching app with new version …")
        relaunch_app()

    return True


# ── Quick smoke-test ──────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Dry-run: just check what the remote server says, don't install anything
    info = fetch_version_info()
    if info:
        print("Remote version:", info.get("version"))
        print("Newer than local?", is_newer(info["version"], CURRENT_VERSION))
    else:
        print("Could not fetch version info.")