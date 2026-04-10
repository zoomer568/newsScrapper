import requests
from bs4 import BeautifulSoup
from scrapers import BaseScraper, register_scraper


class WIONScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.wionews.com'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for article in soup.select('.views-row, .article-item, .news-item, .story-item'):
                link = article.find('a')
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = link.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not href:
                    continue

                if not href.startswith('http'):
                    href = self.base_url + href

                if href in seen:
                    continue
                seen.add(href)

                img = ''
                if include_images:
                    img_elem = article.select_one('img')
                    if img_elem:
                        img = img_elem.get('src', '') or img_elem.get('data-src', '')

                category = ''
                cat_elem = article.select_one('.category, .section, .topic')
                if cat_elem:
                    category = cat_elem.get_text(strip=True)

                all_news.append({
                    'title': title,
                    'link': href,
                    'image': img,
                    'description': '',
                    'category': category.upper() if category else 'NEWS'
                })
        except Exception as e:
            print(f"Error in get_home_news: {e}")

        return all_news[:30]

    def get_section_news(self, section, include_images=True):
        all_news = []
        seen = set()

        if section == 'home':
            return self.get_home_news(include_images)

        section_urls = {
            'world': f'{self.base_url}/world-news',
            'india': f'{self.base_url}/india-news',
            'science': f'{self.base_url}/science',
            'business': f'{self.base_url}/business',
            'sports': f'{self.base_url}/sports',
            'opinion': f'{self.base_url}/opinion',
            'videos': f'{self.base_url}/videos',
        }

        url = section_urls.get(section, f'{self.base_url}')

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for article in soup.select('.views-row, .article-item, .news-item'):
                link = article.find('a')
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = link.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not href:
                    continue
                if not href.startswith('http'):
                    href = self.base_url + href

                if href in seen:
                    continue
                seen.add(href)

                img = ''
                if include_images:
                    img_elem = article.select_one('img')
                    if img_elem:
                        img = img_elem.get('src', '') or img_elem.get('data-src', '')

                all_news.append({
                    'title': title,
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

            related_section = soup.select('.related-articles a, .more-news a, .recommended a')
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
            related_news.extend(self.get_home_news()[:6])

        return related_news[:6]

    def get_sections(self):
        return [
            {'id': 'home', 'name': 'Home', 'default': True},
            {'id': 'world', 'name': 'World'},
            {'id': 'india', 'name': 'India'},
            {'id': 'business', 'name': 'Business'},
            {'id': 'science', 'name': 'Science'},
            {'id': 'sports', 'name': 'Sports'},
            {'id': 'opinion', 'name': 'Opinion'},
            {'id': 'videos', 'name': 'Videos'},
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

            img = ''
            og_image = soup.find('meta', property='og:image')
            if og_image:
                img = og_image.get('content', '')

            if not img:
                img_elem = soup.select_one('.article-image img, .featured-image img')
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


register_scraper('wion', WIONScraper)