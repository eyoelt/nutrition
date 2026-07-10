from scraper.base import BaseScraper
from models.article import Article
from datetime import datetime


class WHOScraper(BaseScraper):

    BASE_URL = "https://www.who.int"
    NEWS_PAGE = "https://www.who.int/news"

    def scrape(self):

        soup = self.get_soup(self.NEWS_PAGE)

        print("=" * 60)
        print("WHO SCRAPER")
        print("=" * 60)

        links = soup.find_all("a")

        articles = []
        seen_urls = set()

        for link in links:

            href = link.get("href", "")
            title = link.get_text(" ", strip=True)

            if not title:
                continue

            # Filter WHO news links
            if "/news/" in href or "/news-room/" in href:

                # Fix relative URLs
                if href.startswith("/"):
                    url = self.BASE_URL + href
                else:
                    url = href

                if url in seen_urls:
                    continue

                seen_urls.add(url)

                print("=" * 50)
                print("TITLE:", title)
                print("URL  :", url)

                article = Article(
                    title=title,
                    url=url,
                    source="WHO",
                    category=None,
                    summary=None,
                    content=None,
                    author=None,
                    published_date=None,
                    scraped_date=datetime.now().isoformat()
                )

                articles.append(article)

        print(f"\nTotal Articles Found: {len(articles)}")

        return articles