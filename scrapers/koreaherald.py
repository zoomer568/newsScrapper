import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from scrapers import BaseScraper, register_scraper


class KoreaHeraldScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.koreaherald.com'
        self.rss_url = 'https://www.koreaherald.com/rss/newsAll'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for article in soup.select('.headline_item a, .news_list a, .div_item a, .article-item'):
                title = article.get_text(strip=True)
                href = article.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not href:
                    continue

                if not href.startswith('http'):
                    href = self.base_url + href

                if href in seen or '/article/' not in href:
                    continue
                seen.add(href)

                img = ''
                if include_images:
                    parent = article.find_parent(['div', 'li', 'article'])
                    if parent:
                        img_elem = parent.select_one('img')
                        if img_elem:
                            img = img_elem.get('src', '') or img_elem.get('data-src', '')

                category = ''
                cat_elem = article.select_one('.category, .section')
                if cat_elem:
                    category = cat_elem.get_text(strip=True)

                all_news.append({
                    'title': title[:100],
                    'link': href,
                    'image': img,
                    'description': '',
                    'category': category.upper() if category else 'NEWS'
                })
        except Exception as e:
            print(f"Error in get_home_news: {e}")

        if not all_news:
            return self.get_rss_news(include_images)

        return all_news[:30]

    def get_rss_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.rss_url, headers=self.headers, timeout=15)
            root = ET.fromstring(resp.content)

            for item in root.findall('.//item')[:30]:
                title = item.find('title').text if item.find('title') is not None else ''
                link = item.find('link').text if item.find('link') is not None else ''
                desc = item.find('description').text if item.find('description') is not None else ''

                if not title or not link:
                    continue
                if link in seen:
                    continue
                seen.add(link)

                import re
                desc = re.sub('<[^>]+>', '', desc) if desc else ''

                all_news.append({
                    'title': title,
                    'link': link,
                    'image': '',
                    'description': desc[:200],
                    'category': 'NEWS'
                })
        except Exception as e:
            print(f"Error fetching RSS: {e}")

        return all_news

    def get_section_news(self, section, include_images=True):
        all_news = []
        seen = set()

        if section == 'home':
            return self.get_home_news(include_images)

        section_urls = {
            'national': f'{self.base_url}/National',
            'business': f'{self.base_url}/Business',
            'world': f'{self.base_url}/World',
            'sports': f'{self.base_url}/Sports',
            'life': f'{self.base_url}/life',
            'opinion': f'{self.base_url}/Opinion',
            'kpop': f'{self.base_url}/kpop',
        }

        url = section_urls.get(section, f'{self.base_url}')

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for article in soup.select('.headline_item a, .news_list a, .article-item'):
                title = article.get_text(strip=True)
                href = article.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not href:
                    continue
                if not href.startswith('http'):
                    href = self.base_url + href
                if '/article/' not in href:
                    continue

                if href in seen:
                    continue
                seen.add(href)

                img = ''
                if include_images:
                    parent = article.find_parent(['div', 'li', 'article'])
                    if parent:
                        img_elem = parent.select_one('img')
                        if img_elem:
                            img = img_elem.get('src', '')

                all_news.append({
                    'title': title[:100],
                    'link': href,
                    'image': img,
                    'description': '',
                    'category': section.upper()
                })

                if len(all_news) >= 30:
                    break

        except Exception as e:
            print(f"Error fetching section {section}: {e}")

        return all_news

    def get_related_news(self, url):
        related_news = []
        seen = set()

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            topic_elem = soup.select_one('.category, .section')
            topic = ''
            if topic_elem:
                topic = topic_elem.get_text(strip=True).lower()

            related_section = soup.select('.related-articles a, .related-list a, .recommend-articles a')
            for a in related_section[:10]:
                href = a.get('href', '')
                if not href:
                    continue

                if not href.startswith('http'):
                    href = self.base_url + href

                if href in seen or href == url:
                    continue
                seen.add(href)

                title = a.get_text(strip=True)
                if title and len(title) > 10:
                    related_news.append({
                        'title': title,
                        'link': href,
                        'image': '',
                        'category': 'RELATED'
                    })

                if len(related_news) >= 6:
                    break
        except Exception as e:
            print(f"Error getting related news: {e}")

        if len(related_news) < 3:
            related_section = 'national'
            if 'business' in topic:
                related_section = 'business'
            elif 'world' in topic:
                related_section = 'world'
            related_news.extend(self.get_section_news(related_section)[:6])

        return related_news[:6]

    def get_sections(self):
        return [
            {'id': 'home', 'name': 'Home', 'default': True},
            {'id': 'national', 'name': 'National'},
            {'id': 'business', 'name': 'Business'},
            {'id': 'world', 'name': 'World'},
            {'id': 'sports', 'name': 'Sports'},
            {'id': 'life', 'name': 'Life'},
            {'id': 'opinion', 'name': 'Opinion'},
            {'id': 'kpop', 'name': 'K-Pop'},
        ]

    def get_article(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
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


register_scraper('koreaherald', KoreaHeraldScraper)