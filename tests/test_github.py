from src.graphone.enrichment.github import parse_github_url


def test_parse_github_url():
    repo = parse_github_url("https://github.com/openai/gpt-5")

    assert repo.owner == "openai"
    assert repo.name == "gpt-5"
    assert repo.url == "https://github.com/openai/gpt-5"

def test_parse_github_url_invalid():
    import pytest

    with pytest.raises(ValueError):
        parse_github_url("https://example.com/repo")