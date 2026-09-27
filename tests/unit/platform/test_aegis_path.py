import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

# chmod cannot deny root, so the unwritable cases prove nothing there.
needs_unprivileged = pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0, reason="requires a non-root user"
)

from core.config import state_dir_status, aegis_path


@pytest.fixture
def home(tmp_path):
    with patch.object(Path, "home", return_value=tmp_path):
        yield tmp_path


@pytest.mark.unit
def test_read_prefers_aegis_dir(home):
    (home / ".aegis").mkdir()
    (home / ".deeptempo").mkdir()
    (home / ".aegis" / "a.json").write_text("{}")
    (home / ".deeptempo" / "a.json").write_text("{}")
    assert aegis_path("a.json") == home / ".aegis" / "a.json"


@pytest.mark.unit
def test_read_falls_back_to_legacy_dir(home):
    # The compatibility guarantee: an install whose data only exists under
    # ~/.deeptempo keeps reading it, with no migration step.
    (home / ".deeptempo").mkdir()
    legacy = home / ".deeptempo" / "integrations_config.json"
    legacy.write_text(json.dumps({"enabled_integrations": ["vstrike"]}))
    assert aegis_path("integrations_config.json") == legacy


@pytest.mark.unit
def test_read_of_missing_file_points_at_aegis_dir(home):
    assert aegis_path("nope.json") == home / ".aegis" / "nope.json"


@pytest.mark.unit
def test_write_always_targets_aegis_dir_even_when_legacy_exists(home):
    (home / ".deeptempo").mkdir()
    (home / ".deeptempo" / "theme_config.json").write_text("{}")
    target = aegis_path("theme_config.json", write=True)
    assert target == home / ".aegis" / "theme_config.json"
    assert target.parent.is_dir()


@pytest.mark.unit
def test_write_with_no_parts_creates_the_directory_itself(home):
    assert aegis_path(write=True) == home / ".aegis"
    assert (home / ".aegis").is_dir()


@pytest.mark.unit
def test_aegis_dir_overrides_home(tmp_path, monkeypatch):
    custom = tmp_path / "state"
    monkeypatch.setenv("AEGIS_DIR", str(custom))
    assert aegis_path("a.json") == custom / "a.json"
    assert aegis_path("a.json", write=True) == custom / "a.json"
    assert custom.is_dir()


@pytest.mark.unit
def test_aegis_dir_has_no_legacy_fallback(home, tmp_path, monkeypatch):
    # An explicit override means exactly that directory.
    (home / ".deeptempo").mkdir()
    (home / ".deeptempo" / "a.json").write_text("{}")
    custom = tmp_path / "state"
    monkeypatch.setenv("AEGIS_DIR", str(custom))
    assert aegis_path("a.json") == custom / "a.json"


@pytest.mark.unit
@needs_unprivileged
def test_write_failure_raises_rather_than_relocating(home):
    # A silent /tmp relocation applied to writes only, so the save looked fine
    # and the value was gone. Callers that want to degrade catch this themselves.
    home.chmod(0o500)
    try:
        with pytest.raises(OSError):
            aegis_path("a.json", write=True)
    finally:
        home.chmod(0o700)


@pytest.mark.unit
def test_state_dir_status_reports_path_and_writability(home):
    status = state_dir_status()
    assert status == {"path": str(home / ".aegis"), "exists": False, "writable": True}
    (home / ".aegis").mkdir()
    assert state_dir_status()["exists"] is True


@pytest.mark.unit
@needs_unprivileged
def test_state_dir_status_reports_unwritable_without_raising(home):
    home.chmod(0o500)
    try:
        status = state_dir_status()
        assert status["writable"] is False
        assert status["path"] == str(home / ".aegis")
    finally:
        home.chmod(0o700)


@pytest.mark.unit
def test_bare_directory_never_resolves_to_legacy(home):
    # The secrets backend asks for the directory itself; answering ~/.deeptempo
    # would send every credential written after it there.
    (home / ".deeptempo").mkdir()
    assert aegis_path() == home / ".aegis"


@pytest.mark.unit
def test_bare_directory_is_not_created_on_read(home):
    assert not (home / ".aegis").exists()
    aegis_path()
    state_dir_status()
    assert not (home / ".aegis").exists()


@pytest.mark.unit
def test_root_home_falls_back_to_safe_directory(monkeypatch):
    monkeypatch.delenv("AEGIS_DIR", raising=False)
    with patch.object(Path, "home", return_value=Path("/")):
        target = aegis_path("test.json")
        assert target != Path("/.aegis/test.json")
        assert target.name == "test.json"
        assert target.parent.name == ".aegis"
        assert str(target).startswith("/home/aegis") or str(target).startswith("/tmp")


@pytest.mark.unit
def test_root_home_safe_write(monkeypatch, tmp_path):
    monkeypatch.delenv("AEGIS_DIR", raising=False)
    with patch.object(Path, "home", return_value=Path("/")):
        with patch("core.config._safe_home", return_value=tmp_path):
            target = aegis_path("test.json", write=True)
            assert target == tmp_path / ".aegis" / "test.json"
            assert (tmp_path / ".aegis").is_dir()

