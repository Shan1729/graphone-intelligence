from pathlib import Path

import pytest

from graphone.acquisition.bulk import (
    download_bulk_file,
)


@pytest.mark.asyncio
async def test_download_bulk_file(tmp_path):
    source_url = (
        "https://raw.githubusercontent.com/"
        "octocat/Hello-World/master/README"
    )

    output_path = (
        tmp_path / "downloaded_readme.txt"
    )

    result = await download_bulk_file(
        source_url=source_url,
        output_path=output_path,
        timeout=60.0,
        max_retries=2,
        chunk_size=1024,
    )

    assert result.source_url == source_url
    assert result.output_path == output_path
    assert result.size_bytes > 0

    assert output_path.exists()

    content = output_path.read_bytes()

    assert len(content) > 0
    assert len(content) == result.size_bytes