"""Tests for the GitHub integration preset."""

import json
import sys

import pytest


@pytest.fixture()
def integrations_mod(tmp_path, monkeypatch):
    """Import src.integrations with data file redirected to tmp."""
    monkeypatch.setenv("ODYSSEUS_ENCRYPTION_KEY", "test-key-0123456789abcdef")
    sys.modules.pop("src.integrations", None)
    from src import integrations  # noqa: WPS433

    monkeypatch.setattr(integrations, "DATA_FILE", str(tmp_path / "integrations.json"))
    return integrations


# ------------------------------------------------------------------
# Preset existence & structure
# ------------------------------------------------------------------

def test_github_preset_exists():
    from src.integrations import INTEGRATION_PRESETS

    assert "github" in INTEGRATION_PRESETS


def test_github_preset_has_required_fields():
    from src.integrations import INTEGRATION_PRESETS

    preset = INTEGRATION_PRESETS["github"]
    assert preset["name"] == "GitHub"
    assert preset["auth_type"] == "header"
    assert preset["auth_header"] == "Authorization"
    assert isinstance(preset["description"], str)
    assert len(preset["description"]) > 0


# ------------------------------------------------------------------
# Endpoint coverage in the description
# ------------------------------------------------------------------

_EXPECTED_ENDPOINTS = [
    "/repos/{owner}/{repo}/pulls",
    "/repos/{owner}/{repo}/pulls/{pull_number}",
    "/repos/{owner}/{repo}/pulls/{pull_number}/files",
    "/repos/{owner}/{repo}/pulls/{pull_number}/reviews",
    "/repos/{owner}/{repo}/pulls/{pull_number}/merge",
    "/repos/{owner}/{repo}/issues",
    "/repos/{owner}/{repo}/commits",
    "/repos/{owner}/{repo}/branches",
    "/repos/{owner}/{repo}/contents/",
    "/repos/{owner}/{repo}/actions/runs",
    "/user/repos",
]


@pytest.mark.parametrize("endpoint", _EXPECTED_ENDPOINTS)
def test_github_preset_documents_endpoint(endpoint):
    from src.integrations import INTEGRATION_PRESETS

    desc = INTEGRATION_PRESETS["github"]["description"]
    assert endpoint in desc, f"Missing endpoint {endpoint} in GitHub preset description"


# ------------------------------------------------------------------
# PR-specific endpoint coverage
# ------------------------------------------------------------------

def test_github_preset_covers_pr_create():
    from src.integrations import INTEGRATION_PRESETS

    desc = INTEGRATION_PRESETS["github"]["description"]
    assert "POST" in desc and "create PR" in desc.lower() or '"head"' in desc


def test_github_preset_covers_pr_merge():
    from src.integrations import INTEGRATION_PRESETS

    desc = INTEGRATION_PRESETS["github"]["description"]
    assert "merge" in desc.lower()
    assert "squash" in desc.lower() or "merge_method" in desc


# ------------------------------------------------------------------
# add_integration with github preset
# ------------------------------------------------------------------

def test_add_integration_from_github_preset(integrations_mod):
    result = integrations_mod.add_integration({
        "preset": "github",
        "base_url": "https://api.github.com",
        "api_key": "ghp_testtoken1234567890",
    })

    assert result["name"] == "GitHub"
    assert result["auth_type"] == "header"
    assert result["auth_header"] == "Authorization"
    assert result["base_url"] == "https://api.github.com"
    assert result["preset"] == "github"
    assert result.get("id"), "Integration should receive an auto-generated id"


def test_github_integration_roundtrips_through_save_load(integrations_mod):
    integrations_mod.add_integration({
        "preset": "github",
        "base_url": "https://api.github.com",
        "api_key": "ghp_roundtrip_test_key",
    })

    loaded = integrations_mod.load_integrations()
    assert len(loaded) == 1
    assert loaded[0]["name"] == "GitHub"
    assert loaded[0]["api_key"] == "ghp_roundtrip_test_key"


def test_github_integration_api_key_masked(integrations_mod):
    result = integrations_mod.add_integration({
        "preset": "github",
        "api_key": "ghp_secret_token",
    })

    masked = integrations_mod.mask_integration_secret(result)
    assert masked["api_key"] == "ghp_****"
    assert "secret_token" not in masked["api_key"]
