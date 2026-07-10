from scraper.sources import SOURCES
from scraper.rss_reader import RSSReader

from services.article_service import article_service


class ScraperManager:

    def __init__(self):

        self.reader = RSSReader()

    def run(self):

        all_articles = []

        for source in SOURCES:

            articles = self.reader.read(source)

            all_articles.extend(articles)

        print(f"\nSaving {len(all_articles)} articles...")

        article_service.save_articles(all_articles)

        return all_articles