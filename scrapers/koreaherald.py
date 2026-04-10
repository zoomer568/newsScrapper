import requests
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()
from scrapers import BaseScraper, register_scraper


class KoreaHeraldScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.koreaherald.com'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for a in soup.find_all('a', href=True):
                title = a.get_text(strip=True)
                href = a.get('href', '')

                if not title or len(title) < 15:
                    continue
                if not href or href in ['#', '/']:
                    continue
                if '/author/' in href or '/tag/' in href:
                    continue

                if not href.startswith('http'):
                    href = self.base_url + href

                if href in seen:
                    continue
                seen.add(href)

                all_news.append({
                    'title': title,
                    'link': href,
                    'image': '',
                    'description': '',
                    'category': 'KOREA'
                })

                if len(all_news) >= 30:
                    break
        except Exception as e:
            print(f"Error in KoreaHerald get_home_news: {e}")

        if not all_news:
            all_news = [
                {'title': 'Korea Herald News', 'link': 'https://www.koreaherald.com', 'image': '', 'description': 'Visit Korea Herald', 'category': 'NEWS'},
            ]

        return all_news[:30]

    def get_rss_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            import xml.etree.ElementTree as ET
            resp = requests.get('https://www.koreaherald.com/rss/rss.xml', headers=self.headers, timeout=15, verify=False)
            root = ET.fromstring(resp.content)

            for item in root.findall('.//item')[:30]:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''

                if not title or not link:
                    continue
                if link in seen:
                    continue
                seen.add(link)

                all_news.append({
                    'title': title,
                    'link': link,
                    'image': '',
                    'description': '',
                    'category': 'KOREA'
                })
        except Exception as e:
            print(f"Error fetching RSS: {e}")

        return all_news

    def get_section_news(self, section, include_images=True):
        return self.get_home_news(include_images)

    def get_related_news(self, url):
        return self.get_home_news()[:6]

    def get_sections(self):
        return [
            {'id': 'home', 'name': 'Home', 'default': True},
            {'id': 'politics', 'name': 'Politics'},
            {'id': 'economy', 'name': 'Economy'},
            {'id': 'national', 'name': 'National'},
            {'id': 'world', 'name': 'World'},
            {'id': 'kpop', 'name': 'K-Pop'},
        ]

    def get_article(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=15, verify=False)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = ''
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)

            if not title:
                og_title = soup.find('meta', property='og:title')
                title = og_title.get('content', '') if og_title else ''

            article_content = ''
            article_body = soup.find('article') or soup.find('div', class_='article_view')
            if article_body:
                for p in article_body.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        article_content += f'<p>{text}</p>'

            img = ''
            og_image = soup.find('meta', property='og:image')
            if og_image:
                img = og_image.get('content', '')

            if not img:
                img_elem = soup.select_one('.news_img img')
                if img_elem:
                    img = img_elem.get('src', '')

            if not article_content:
                article_content = '<p>Could not load article content.</p>'

            related_news = self.get_related_news(url)
            if len(related_news) < 3:
                related_news = self.get_home_news()[:6]

            return {
                'title': title,
                'content': article_content,
                'image': img,
                'related_news': related_news[:6]
            }
        except Exception as e:
            return {
                'title': 'Error',
                'content': f'Error loading article: {str(e)}',
                'image': '',
                'related_news': []
            }

    def get_capabilities(self):
        return {
            'has_images': False,
            'has_sections': True,
            'has_article_content': True,
            'has_related_news': True
        }


register_scraper('koreaherald', KoreaHeraldScraper)
