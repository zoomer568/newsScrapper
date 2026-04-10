import re
import requests
from bs4 import BeautifulSoup
from scrapers import BaseScraper, register_scraper


class BBCScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www.bbc.com'

    def get_home_news(self, include_images=True):
        all_news = []
        seen = set()

        try:
            resp = requests.get(f'{self.base_url}/news', headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            for h2 in soup.find_all('h2'):
                title = h2.get_text(strip=True)
                if not title or len(title) < 15:
                    continue

                link = ''
                parent_a = h2.find_parent('a')
                if parent_a and parent_a.get('href'):
                    link = parent_a.get('href')
                    if not link.startswith('http'):
                        link = self.base_url + link

                if not link or link in [f'{self.base_url}/news', f'{self.base_url}/news/']:
                    continue

                img = ''
                if include_images:
                    if parent_a:
                        for img_elem in parent_a.find_all('img'):
                            src = img_elem.get('src') or img_elem.get('data-src') or ''
                            if src and 'ichef' in src:
                                img = 'https:' + src if src.startswith('//') else src
                                break

                    if not img and link:
                        try:
                            art_resp = requests.get(link, headers=self.headers, timeout=10)
                            art_soup = BeautifulSoup(art_resp.text, 'html.parser')
                            for img_elem in art_soup.find_all('img'):
                                src = img_elem.get('src') or img_elem.get('data-src') or ''
                                if src and 'ichef' in src:
                                    img = 'https:' + src if src.startswith('//') else src
                                    break
                        except:
                            pass

                desc = ''
                tags = []
                parent_div = h2.find_parent('div')
                if parent_div:
                    for p in parent_div.find_all('p')[:2]:
                        text = p.get_text(strip=True)
                        if text and len(text) > 40 and not text.startswith('BBC'):
                            desc = text
                            break
                    tag_elements = parent_div.find_all(['span', 'a'], class_=lambda x: x and ('tag' in str(x).lower() or 'label' in str(x).lower() or 'category' in str(x).lower()) if x else False)
                    for tag in tag_elements[:3]:
                        tag_text = tag.get_text(strip=True)
                        if tag_text and len(tag_text) < 20:
                            tags.append(tag_text)

                if '/news/technology' in link or '/tech' in link:
                    tags.append('TECH')
                elif '/news/science' in link or '/science' in link:
                    tags.append('SCIENCE')
                elif '/news/business' in link:
                    tags.append('BUSINESS')
                elif '/news/politics' in link:
                    tags.append('POLITICS')
                elif '/sport' in link:
                    tags.append('SPORT')
                elif '/news/entertainment' in link or '/news/arts' in link:
                    tags.append('ARTS')

                if title not in seen:
                    seen.add(title)
                    all_news.append({
                        'title': title,
                        'link': link,
                        'image': img,
                        'description': desc[:200] if desc else '',
                        'category': ', '.join(tags) if tags else 'Home'
                    })
        except Exception as e:
            print(f"Error in get_home_news: {e}")

        return all_news[:30]

    def get_section_news(self, section, include_images=True):
        all_news = []
        seen = set()

        if section == 'sport':
            return self._get_sport_news(include_images)
        if section == 'culture':
            return self._get_culture_news(include_images)

        section_urls = {
            'technology': f'{self.base_url}/news/technology',
            'science_and_environment': f'{self.base_url}/news/science_and_environment',
            'business': f'{self.base_url}/news/business',
            'politics': f'{self.base_url}/news/politics',
        }

        url = section_urls.get(section)
        if not url:
            return []

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            links = soup.find_all('a', href=lambda x: x and 'articles' in str(x))

            for a in links:
                href = a.get('href', '')
                if not href:
                    continue
                if '/news/' not in href:
                    continue
                if not href.startswith('http'):
                    href = self.base_url + href
                if href in seen:
                    continue
                seen.add(href)

                title = a.get_text(strip=True)
                if not title or len(title) < 15:
                    continue

                img = ''
                if include_images:
                    parent = a.find_parent(['div', 'li', 'article'])
                    if parent:
                        for img_elem in parent.find_all('img'):
                            src = img_elem.get('src') or img_elem.get('data-src') or ''
                            if src and 'ichef' in src:
                                img = src
                                break

                    if img and img.startswith('//'):
                        img = 'https:' + img

                    if not img and href:
                        try:
                            art_resp = requests.get(href, headers=self.headers, timeout=10)
                            art_soup = BeautifulSoup(art_resp.text, 'html.parser')
                            for img_elem in art_soup.find_all('img'):
                                src = img_elem.get('src') or img_elem.get('data-src') or ''
                                if src and 'ichef' in src:
                                    img = 'https:' + src if src.startswith('//') else src
                                    break
                        except:
                            pass

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
            print(f"Error: {e}")

        return all_news

    def _get_sport_news(self, include_images=True):
        all_news = []
        seen = set()

        try:
            resp = requests.get('https://feeds.bbci.co.uk/sport/rss.xml', headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for item in soup.find_all('item')[:30]:
                title = item.find('title')
                if title:
                    title_text = title.get_text(strip=True)
                else:
                    continue

                item_str = str(item)
                link_match = re.search(r'https://www\.bbc\.com/sport/[^<\s]+', item_str)
                if link_match:
                    href = link_match.group(0)
                else:
                    continue

                if not title_text or len(title_text) < 15:
                    continue
                if href in seen:
                    continue
                seen.add(href)

                img = ''
                if include_images:
                    thumb_match = re.search(r'url="(https://ichef[^"]+)"', item_str)
                    if thumb_match:
                        img = thumb_match.group(1)

                all_news.append({
                    'title': title_text,
                    'link': href,
                    'image': img,
                    'description': '',
                    'category': 'SPORT'
                })
        except Exception as e:
            print(f"Error fetching sport RSS: {e}")
        return all_news

    def _get_culture_news(self, include_images=True):
        all_news = []
        seen = set()

        try:
            resp = requests.get(f'{self.base_url}/culture', headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
            links = soup.find_all('a', href=lambda x: x and '/culture/article/' in str(x))
            for a in links:
                href = a.get('href', '')
                if not href:
                    continue
                if not href.startswith('http'):
                    href = self.base_url + href
                if href in seen:
                    continue
                seen.add(href)
                title = a.get_text(strip=True)
                if not title or len(title) < 15:
                    continue

                img = ''
                if include_images:
                    parent = a.find_parent(['div', 'li', 'article'])
                    if parent:
                        for img_elem in parent.find_all('img'):
                            src = img_elem.get('src') or img_elem.get('data-src') or ''
                            if src and 'ichef' in src:
                                img = 'https:' + src if src.startswith('//') else src
                                break

                    if not img and href:
                        try:
                            art_resp = requests.get(href, headers=self.headers, timeout=10)
                            art_soup = BeautifulSoup(art_resp.text, 'html.parser')
                            for img_elem in art_soup.find_all('img'):
                                src = img_elem.get('src') or img_elem.get('data-src') or ''
                                if src and 'ichef' in src:
                                    img = 'https:' + src if src.startswith('//') else src
                                    break
                        except:
                            pass

                all_news.append({
                    'title': title,
                    'link': href,
                    'image': img,
                    'description': '',
                    'category': 'CULTURE'
                })
                if len(all_news) >= 30:
                    break
        except Exception as e:
            print(f"Error fetching culture: {e}")
        return all_news

    def get_related_news(self, url):
        related_news = []
        seen = set()

        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            links = soup.find_all('a', href=lambda x: x and '/news/articles' in str(x))
            for a in links:
                href = a.get('href', '')
                if not href:
                    continue
                if href in url:
                    continue
                if not href.startswith('http'):
                    href = self.base_url + href
                if href in seen or href == url:
                    continue
                seen.add(href)

                parent = a.find_parent(['div', 'li', 'article'])
                title = ''
                if parent:
                    h2 = parent.find('h2')
                    if h2:
                        title = h2.get_text(strip=True)
                    if not title or len(title) <= 10:
                        h_elem = parent.find(['h3', 'h4', 'span'])
                        title = h_elem.get_text(strip=True) if h_elem else ''
                    if title and len(title) > 10 and title[0].isdigit():
                        title = ''

                if not title:
                    title = a.get_text(strip=True) or ''
                if title and title[0].isdigit():
                    title = ''

                if title and len(title) > 10:
                    img = ''
                    if parent:
                        for img_elem in parent.find_all('img'):
                            src = img_elem.get('src') or img_elem.get('data-src') or ''
                            if src and 'ichef' in src:
                                img = src
                                break
                    if img and img.startswith('//'):
                        img = 'https:' + img

                    related_news.append({
                        'title': title,
                        'link': href,
                        'image': img,
                        'category': 'RELATED'
                    })

                    if len(related_news) >= 3:
                        break
        except Exception as e:
            print(f"Error getting related news: {e}")

        if len(related_news) == 0:
            topic = ''
            if '/technology' in url or '/tech' in url:
                topic = 'technology'
            elif '/science' in url:
                topic = 'science_and_environment'
            elif '/business' in url:
                topic = 'business'
            elif '/politics' in url:
                topic = 'politics'
            elif '/sport' in url:
                topic = 'sport'

            if topic:
                related_news.extend(self.get_section_news(topic)[:6])

        return related_news[:6]

    def get_sections(self):
        return [
            {'id': 'home', 'name': 'Home', 'default': True},
            {'id': 'technology', 'name': 'Tech'},
            {'id': 'science_and_environment', 'name': 'Science'},
            {'id': 'business', 'name': 'Business'},
            {'id': 'politics', 'name': 'Politics'},
            {'id': 'sport', 'name': 'Sport'},
            {'id': 'culture', 'name': 'Culture'},
        ]

    def get_article(self, url):
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')

            title = ''
            title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)

            article_content = ''
            article_body = soup.find('article')

            if article_body:
                for p in article_body.find_all('p')[:40]:
                    text = p.get_text(strip=True)
                    if text and len(text) > 20:
                        if 'Read more' in text or 'BBC' in text[:10]:
                            continue
                        article_content += f'<p>{text}</p>'

            if not article_content:
                for div in soup.find_all('div', class_=lambda x: x and 'article' in str(x).lower()):
                    for p in div.find_all('p')[:40]:
                        text = p.get_text(strip=True)
                        if text and len(text) > 20 and 'Read more' not in text:
                            article_content += f'<p>{text}</p>'
                    if article_content:
                        break

            if not article_content:
                main_content = soup.find('main') or soup.find('div', {'data-component': 'article-body'})
                if main_content:
                    for p in main_content.find_all('p')[:40]:
                        text = p.get_text(strip=True)
                        if text and len(text) > 20 and 'Read more' not in text:
                            article_content += f'<p>{text}</p>'

            img = ''
            for img_elem in soup.find_all('img'):
                src = img_elem.get('src') or img_elem.get('data-src') or ''
                if src and 'ichef' in src:
                    img = src
                    break
            if not img:
                for img_elem in soup.find_all('img')[:10]:
                    src = img_elem.get('src') or img_elem.get('data-src') or ''
                    if src and 'bbc' in src:
                        img = src
                        break
            if img and img.startswith('//'):
                img = 'https:' + img

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
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(resp.text, 'html.parser')
            for img_elem in soup.find_all('img'):
                src = img_elem.get('src') or img_elem.get('data-src') or ''
                if src and 'ichef' in src:
                    return 'https:' + src if src.startswith('//') else src
            for img_elem in soup.find_all('img')[:10]:
                src = img_elem.get('src') or img_elem.get('data-src') or ''
                if src and 'bbc' in src:
                    return 'https:' + src if src.startswith('//') else src
        except:
            pass
        return ''


register_scraper('bbc', BBCScraper)
