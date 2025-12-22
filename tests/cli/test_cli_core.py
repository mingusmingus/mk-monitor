
import os
import pytest
from cli.core import load_or_create_env, save_key_to_env
from backend.app.config import Config

@pytest.fixture
def clean_env(tmp_path):
    """
    Creates a temporary directory for .env testing.
    Patches load_or_create_env to return a path in this temp directory.
    """
    env_file = tmp_path / ".env"

    # We patch the function in cli.core
    original_func = load_or_create_env

    def mock_load_or_create_env():
        return str(env_file)

    import cli.core
    cli.core.load_or_create_env = mock_load_or_create_env

    yield env_file

    # Restore
    cli.core.load_or_create_env = original_func

def test_save_key_to_env_creates_file(clean_env):
    """Test that save_key_to_env creates the file if it doesn't exist."""
    key = "TEST_KEY"
    value = "test_value"

    save_key_to_env(key, value)

    assert clean_env.exists()
    content = clean_env.read_text()
    assert f"{key}={value}\n" in content
    assert os.environ[key] == value
    assert getattr(Config, key) == value

def test_save_key_to_env_updates_existing(clean_env):
    """Test that save_key_to_env updates an existing key."""
    key = "TEST_KEY"
    value1 = "value1"
    value2 = "value2"

    # Create initial file
    clean_env.write_text(f"OTHER=foo\n{key}={value1}\n")

    save_key_to_env(key, value2)

    content = clean_env.read_text()
    assert f"{key}={value2}\n" in content
    assert f"{key}={value1}" not in content
    assert "OTHER=foo\n" in content

def test_save_key_to_env_appends_new(clean_env):
    """Test that save_key_to_env appends a new key preserving existing ones."""
    clean_env.write_text("EXISTING=foo\n")

    key = "NEW_KEY"
    value = "bar"

    save_key_to_env(key, value)

    content = clean_env.read_text()
    assert "EXISTING=foo\n" in content
    assert f"{key}={value}\n" in content

def test_save_key_to_env_handles_no_newline(clean_env):
    """Test that it adds a newline if the last line doesn't have one."""
    clean_env.write_text("EXISTING=foo") # No newline

    key = "NEW_KEY"
    value = "bar"

    save_key_to_env(key, value)

    content = clean_env.read_text()
    lines = content.splitlines(keepends=True)
    assert lines[0] == "EXISTING=foo\n"
    assert lines[1] == f"{key}={value}\n"
