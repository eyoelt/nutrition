from dataclasses import dataclass


@dataclass
class Article:
    title: str
    url: str
    source: str
    category: str = ""
    summary: str = ""
    content: str = ""
    author: str = ""
    published_date: str = ""
    scraped_date: str = ""