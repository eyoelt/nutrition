from scraper.who import WHOScraper


class ScraperManager:

    def __init__(self):

        self.scrapers = [
            WHOScraper()
        ]

    def run(self):

        all_articles = []

        for scraper in self.scrapers:

            articles = scraper.scrape()

            all_articles.extend(articles)

        return all_articles