from dataclasses import dataclass


@dataclass(frozen=True)
class NewsJobItem:
    title: str
    url: str
    source: str
    published_at: str
    item_type: str

    def __post_init__(self):
        if self.item_type not in {"news", "job"}:
            raise ValueError("item_type must be 'news' or 'job'")