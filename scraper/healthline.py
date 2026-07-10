from scraper.base import BaseScraper
from models.article import Article
from datetime import datetime
from urllib.parse import urljoin


class HealthlineScraper(BaseScraper):

    BASE_URL = "https://www.healthline.com"
    START_URL = "https://www.healthline.com/nutrition"

    def scrape(self):

        soup = self.get_soup(self.START_URL)

        print("=" * 60)
        print("HEALTHLINE SCRAPER")
        print("=" * 60)

        articles = []
        seen = set()

        links = soup.find_all("a")

        for link in links:

            href = link.get("href")
            title = link.get_text(" ", strip=True)

            # -----------------------------
            # 1. CLEAN VALIDATION
            # -----------------------------
            if not href or not title:
                continue

            title = " ".join(title.split())

            # skip junk titles
            if len(title) < 10:
                continue

            # -----------------------------
            # 2. FILTER ONLY NUTRITION ARTICLES
            # -----------------------------
            if "/nutrition/" not in href:
                continue

            # ignore category pages like /nutrition/food/
            if href.count("/") < 2:
                continue

            # -----------------------------
            # 3. BUILD FULL URL
            # -----------------------------
            url = urljoin(self.BASE_URL, href)

            # remove tracking junk
            url = url.split("?")[0]

            # -----------------------------
            # 4. REMOVE DUPLICATES
            # -----------------------------
            if url in seen:
                continue

            seen.add(url)

            print("=" * 50)
            print("TITLE:", title)
            print("URL  :", url)

            # -----------------------------
            # 5. CREATE ARTICLE OBJECT
            # -----------------------------
            articles.append(
                Article(
                    title=title,
                    url=url,
                    source="Healthline",
                    category="nutrition",
                    summary=None,
                    content=None,
                    author=None,
                    published_date=None,
                    scraped_date=datetime.now().isoformat()
                )
            )

        print(f"\nTotal Articles Found: {len(articles)}")

        return articles