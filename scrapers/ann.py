import requests
from bs4 import BeautifulSoup
from scrapers import BaseScraper, register_scraper


class AnimeNewsNetworkScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.animenewsnetwork.com'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for link in soup.select('a[href*="/news/202"]'):
                title = link.get_text(strip=True)
                href = link.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not href or '/archive' in href:
                    continue
                if href.startswith('/'):
                    href = self.base_url + href

                if href in seen:
                    continue
                seen.add(href)

                all_news.append({
                    'title': title,
                    'link': href,
                    'image': '',
                    'description': '',
                    'category': 'ANIME'
                })

                if len(all_news) >= 30:
                    break
        except Exception as e:
            print(f"Error in ANN get_home_news: {e}")

        return all_news[:30]

    def get_section_news(self, section, include_images=True):
        if section == 'home':
            return self.get_home_news(include_images)
        return self.get_home_news(include_images)

    def get_related_news(self, url):
        return self.get_home_news()[:6]

    def get_sections(self):
        return [
            {'id': 'home', 'name': 'Home', 'default': True},
        ]

    def get_article(self, url):
        return {
            'title': 'Article',
            'content': '<p>Article content</p>',
            'image': '',
            'related_news': []
        }


register_scraper('ann', AnimeNewsNetworkScraper)