from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubRepo:
    owner: str
    name: str
    url: str


def parse_github_url(url: str) -> GitHubRepo:
    parts = url.rstrip("/").split("/")

    if len(parts) < 2 or parts[-3] != "github.com":
        raise ValueError("Invalid GitHub repository URL")

    owner = parts[-2]
    name = parts[-1]

    return GitHubRepo(
        owner=owner,
        name=name,
        url=f"https://github.com/{owner}/{name}",
    )