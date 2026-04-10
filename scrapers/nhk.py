import requests
from bs4 import BeautifulSoup
from scrapers import BaseScraper, register_scraper


class NHKScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www3.nhk.or.jp/news'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()
        try:
            resp = requests.get(self.base_url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for article in soup.select('.content .item, .news-list .item, .top-news .item'):
                link = article.find('a')
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = link.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not href:
                    continue

                if href.startswith('/'):
                    href = 'https://www3.nhk.or.jp' + href
                elif not href.startswith('http'):
                    href = 'https://www3.nhk.or.jp/' + href

                if href in seen:
                    continue
                seen.add(href)

                img = ''
                if include_images:
                    img_elem = article.select_one('img')
                    if img_elem:
                        img = img_elem.get('src', '') or img_elem.get('data-src', '')

                category = ''
                cat_elem = article.select_one('.category, .label')
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
            'society': 'https://www3.nhk.or.jp/newsweb/genre/society',
            'politics': 'https://www3.nhk.or.jp/newsweb/genre/politics',
            'economy': 'https://www3.nhk.or.jp/newsweb/genre/business',
            'disaster': 'https://www3.nhk.or.jp/newsweb/genre/disaster',
            'international': 'https://www3.nhk.or.jp/newsweb/genre/international',
            'science': 'https://www3.nhk.or.jp/newsweb/genre/science-culture',
            'sports': 'https://www3.nhk.or.jp/newsweb/genre/sports',
            'life': 'https://www3.nhk.or.jp/newsweb/genre/life',
        }

        url = section_urls.get(section, f'{self.base_url}')
        section_name = section.upper()

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for article in soup.select('.content .item, .news-list .item'):
                link = article.find('a')
                if not link:
                    continue

                title = link.get_text(strip=True)
                href = link.get('href', '')

                if not title or len(title) < 10:
                    continue
                if not href:
                    continue

                if href.startswith('/'):
                    href = 'https://www3.nhk.or.jp' + href
                elif not href.startswith('http'):
                    href = 'https://www3.nhk.or.jp/' + href

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
                    'category': section_name
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

            topic_elem = soup.select_one('.topic-link, .category')
            topic = ''
            if topic_elem:
                topic = topic_elem.get_text(strip=True).lower()

            related_section = soup.select('.related-news li a, .link-list a')
            for a in related_section[:10]:
                href = a.get('href', '')
                if not href:
                    continue

                if href.startswith('/'):
                    href = 'https://www3.nhk.or.jp' + href
                elif not href.startswith('http'):
                    href = 'https://www3.nhk.or.jp/' + href

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
            related_section = 'international'
            if 'society' in topic:
                related_section = 'society'
            elif 'politics' in topic:
                related_section = 'politics'
            elif 'economy' in topic or 'business' in topic:
                related_section = 'economy'
            related_news.extend(self.get_section_news(related_section)[:6])

        return related_news[:6]

    def get_sections(self):
        return [
            {'id': 'home', 'name': 'Home', 'default': True},
            {'id': 'society', 'name': 'Society'},
            {'id': 'politics', 'name': 'Politics'},
            {'id': 'economy', 'name': 'Economy'},
            {'id': 'international', 'name': 'International'},
            {'id': 'science', 'name': 'Science'},
            {'id': 'disaster', 'name': 'Weather'},
            {'id': 'sports', 'name': 'Sports'},
            {'id': 'life', 'name': 'Life'},
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
            article_body = soup.find('div', class_='article-body') or soup.find('article')
            if article_body:
                for p in article_body.find_all('p'):
                    text = p.get_text(strip=True)
                    if text and len(text) > 10:
                        article_content += f'<p>{text}</p>'

            if not article_content:
                main_content = soup.find('main') or soup.find('div', class_='content')
                if main_content:
                    for p in main_content.find_all('p'):
                        text = p.get_text(strip=True)
                        if text and len(text) > 10:
                            article_content += f'<p>{text}</p>'

            img = ''
            og_image = soup.find('meta', property='og:image')
            if og_image:
                img = og_image.get('content', '')

            if not img:
                img_elem = soup.select_one('.article-image img')
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


register_scraper('nhk', NHKScraper)