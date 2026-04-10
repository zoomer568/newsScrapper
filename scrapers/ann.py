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

            for article in soup.select('.feed-category .news-title, .herald-news-block .news-title, .story .headline'):
                link = article.find('a') if article.name != 'a' else article
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = link.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not href:
                    continue
                if '/archive' in href:
                    continue
                if href.startswith('/'):
                    href = self.base_url + href

                if href in seen:
                    continue
                seen.add(href)

                img = ''
                if include_images:
                    parent = link.find_parent(['div', 'article', 'li'])
                    if parent:
                        img_elem = parent.select_one('img, .news-image img')
                        if img_elem:
                            img = img_elem.get('src', '') or img_elem.get('data-src', '')
                            if img and not img.startswith('http'):
                                img = self.base_url + img

                if not img:
                    img = self._extract_image_from_article(href)

                all_news.append({
                    'title': title,
                    'link': href,
                    'image': img,
                    'description': '',
                    'category': 'ANIME'
                })

                if len(all_news) >= 30:
                    break

            if len(all_news) < 10:
                seen.clear()
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

                    img = ''
                    if include_images:
                        img = self._extract_image_from_article(href)

                    all_news.append({
                        'title': title,
                        'link': href,
                        'image': img,
                        'description': '',
                        'category': 'ANIME'
                    })

                    if len(all_news) >= 30:
                        break

        except Exception as e:
            print(f"Error in ANN get_home_news: {e}")

        return all_news[:30]

    def _extract_image_from_article(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')

            img = ''
            og_image = soup.find('meta', property='og:image')
            if og_image:
                img = og_image.get('content', '')
                if img and not img.startswith('http'):
                    img = self.base_url + img
                return img

            img_elem = soup.select_one('.article-main-image img, .headline img, .main-image img')
            if img_elem:
                img = img_elem.get('src', '') or img_elem.get('data-src', '')
                if img and not img.startswith('http'):
                    img = self.base_url + img
                return img

            for img_tag in soup.find_all('img'):
                src = img_tag.get('src', '') or img_tag.get('data-src', '')
                if src and 'animenewsnetwork' in src.lower() and 'logo' not in src.lower():
                    if not src.startswith('http'):
                        src = self.base_url + src
                    return src

        except Exception as e:
            print(f"Error extracting image from ANN article: {e}")

        return ''

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
            article_body = soup.find('article') or soup.find('div', class_='article-body')
            if article_body:
                for p in article_body.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        article_content += f'<p>{text}</p>'

            if not article_content:
                text_divs = soup.select('.story-body, .article-content, .entry-content')
                for div in text_divs:
                    for p in div.find_all('p'):
                        text = p.get_text(strip=True)
                        if text and len(text) > 20:
                            article_content += f'<p>{text}</p>'

            img = ''
            og_image = soup.find('meta', property='og:image')
            if og_image:
                img = og_image.get('content', '')
                if img and not img.startswith('http'):
                    img = self.base_url + img

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

    def get_article_image(self, url):
        return self._extract_image_from_article(url)

    def get_capabilities(self):
        return {
            'has_images': True,
            'has_sections': False,
            'has_article_content': True,
            'has_related_news': True
        }


register_scraper('ann', AnimeNewsNetworkScraper)