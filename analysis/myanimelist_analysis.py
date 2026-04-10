"""================================================================================
MYANIMELIST (MAL) WEBSITE DEEP ANALYSIS
================================================================================

Date: 2026-04-10
Website: https://myanimelist.net
Analysis Tool: Beautiful Soup + Requests

================================================================================
SECTION 1: BASIC STRUCTURE
================================================================================

URL PATTERNS:
- Homepage: https://myanimelist.net
- News: /news
- Anime: /anime.php
- Manga: /manga.php
- Characters: /character.php
- People: /people.php
- Reviews: /reviews.php
- Recommendations: /recommendations.php
- Forums: /forum
- RSS Feed: https://myanimelist.net/rss/news.xml

SECTIONS AVAILABLE:
- Anime (Seasonal, Top, Rankings, Schedule)
- Manga (Top, Rankings, Store)
- News (Industry, Anime, Manga, People, Events)
- Community (Forums, Clubs, Users, Blogs)
- Characters & People
- Watch (Episode videos, Trailers)
- Read (Manga Store)
- Featured Articles

================================================================================
SECTION 2: TECHNOLOGY STACK
================================================================================

Frontend Framework: jQuery + Custom JavaScript
CSS: Custom CSS, Bootstrap influence
Analytics: Google Analytics
Ads: Various ad networks

KEY OBSERVATIONS:
- Traditional server-rendered HTML (easy to scrape)
- Some dynamic content via JavaScript
- Responsive design
- RSS feed available
- Login-protected features exist

================================================================================
SECTION 3: ARTICLE STRUCTURE ANALYSIS
================================================================================

META TAGS FOUND:
- og:title, og:description, og:image, og:url, og:site_name
- twitter:card, twitter:title, twitter:description, twitter:image
- Standard meta description, keywords

EXTRACTABLE DATA:
✓ Title: h1 on page, .news-header .title
✓ Summary: .news-header .content
✓ Content: .news-unit .news-content
✓ Image: .news-unit .picLeft img, meta[property="og:image"]
✓ Category: .news-unit .information .genre a
✓ Date: .news-unit .information .date
✓ Author: .news-unit .information .author

================================================================================
SECTION 4: IMAGE HANDLING
================================================================================

CDN Domain: cdn.myanimelist.net

Image URL Patterns:
- https://cdn.myanimelist.net/.../image.jpg
- Thumbnails via r/ (e.g., r/50x50, r/100x156)

Lazy Loading:
- Uses data-src for lazy loading
- Multiple sizes available

================================================================================
SECTION 5: RSS FEED
================================================================================

RSS URL: https://myanimelist.net/rss/news.xml

Format: Standard RSS 2.0
Contains: Full news article list with titles, links, descriptions, dates

================================================================================
SECTION 6: SCRAPING STRATEGY
================================================================================

DIFFICULTY: LOW (easy to scrape)

CODE TEMPLATE:
```python
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import re

class MyAnimeListScraper:
    BASE_URL = 'https://myanimelist.net'
    NEWS_URL = 'https://myanimelist.net/news'
    RSS_URL = 'https://myanimelist.net/rss/news.xml'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    def get_home_news(self):
        resp = requests.get(self.BASE_URL, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        articles = []
        for news in soup.select('.news-unit, .news-list-item'):
            title_elem = news.select_one('.title a, .news-title a') or news.select_one('.title')
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            link = title_elem.get('href', '')
            
            if title and link:
                full_url = link if link.startswith('http') else f"{self.BASE_URL}{link}"
                articles.append({
                    'title': title[:200],
                    'link': full_url
                })

        return articles[:30]

    def get_news_section(self, page=1):
        url = f"{self.NEWS_URL}?p={page}" if page > 1 else self.NEWS_URL
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        articles = []
        for news in soup.select('.news-unit'):
            title_elem = news.select_one('.title a')
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            link = title_elem.get('href', '')
            
            # Get summary
            summary_elem = news.select_one('.content')
            summary = summary_elem.get_text(strip=True)[:200] if summary_elem else ''
            
            # Get image
            img_elem = news.select_one('.picLeft img')
            image = img_elem.get('src', '') if img_elem else ''
            
            if title and link:
                full_url = link if link.startswith('http') else f"{self.BASE_URL}{link}"
                articles.append({
                    'title': title[:200],
                    'link': full_url,
                    'summary': summary,
                    'image': image
                })

        return articles[:30]

    def get_rss_feed(self):
        resp = requests.get(self.RSS_URL, headers=self.HEADERS)
        
        # Parse XML
        root = ET.fromstring(resp.content)
        
        items = []
        for item in root.findall('.//item')[:30]:
            title = item.find('title').text if item.find('title') is not None else ''
            link = item.find('link').text if item.find('link') is not None else ''
            desc = item.find('description').text if item.find('description') is not None else ''
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ''
            
            # Clean description
            desc = re.sub('<[^>]+>', '', desc) if desc else ''
            
            items.append({
                'title': title,
                'link': link,
                'description': desc[:300] if desc else '',
                'pub_date': pub_date
            })
        
        return items

    def get_article(self, url):
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        # Extract title
        title = ''
        title_elem = soup.find('h1')
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        if not title:
            og_title = soup.find('meta', property='og:title')
            title = og_title['content'] if og_title else ''

        # Extract content
        content = ''
        article_body = soup.find('div', class_='news-body') or soup.find('article')
        if article_body:
            for p in article_body.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    content += f'<p>{text}</p>'

        # Extract image
        image = ''
        og_image = soup.find('meta', property='og:image')
        if og_image:
            image = og_image.get('content', '')
        
        if not image:
            img = soup.select_one('.news-detail .picLeft img')
            if img:
                image = img.get('src', '')

        # Extract date
        date = ''
        date_elem = soup.select_one('.information .date') or soup.find('time')
        if date_elem:
            date = date_elem.get_text(strip=True)

        # Extract author
        author = ''
        author_elem = soup.select_one('.information .author')
        if author_elem:
            author = author_elem.get_text(strip=True)

        # Extract tags/categories
        tags = []
        for tag in soup.select('.information .genre a, .tags a'):
            tag_text = tag.get_text(strip=True)
            if tag_text:
                tags.append(tag_text)

        return {
            'title': title,
            'content': content,
            'image': image,
            'date': date,
            'author': author,
            'tags': tags,
            'link': url
        }

    def get_top_anime(self, limit=20):
        url = 'https://myanimelist.net/topanime.php'
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        anime_list = []
        for row in soup.select('tr.ranking-list'):
            rank_elem = row.select_one('.rank .fll')
            title_elem = row.select_one('.title a')
            stats_elem = row.select_one('.score .fls')
            
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            link = title_elem.get('href', '')
            rank = rank_elem.get_text(strip=True) if rank_elem else ''
            score = stats_elem.get_text(strip=True) if stats_elem else ''
            
            if title and link:
                full_url = link if link.startswith('http') else f"{self.BASE_URL}{link}"
                anime_list.append({
                    'rank': rank,
                    'title': title,
                    'score': score,
                    'link': full_url
                })

        return anime_list[:limit]

    def get_seasonal_anime(self, year=2026, season='spring'):
        url = f'https://myanimelist.net/anime/season/{year}/{season}'
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')

        anime_list = []
        for item in soup.select('.seasonal-anime'):
            title_elem = item.select_one('.title a')
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            link = title_elem.get('href', '')
            
            # Get synopsis
            synopsis_elem = item.select_one('.synopsis')
            synopsis = synopsis_elem.get_text(strip=True)[:200] if synopsis_elem else ''
            
            # Get image
            img_elem = item.select_one('.image img')
            image = img_elem.get('src', '') if img_elem else ''
            
            if title and link:
                full_url = link if link.startswith('http') else f"{self.BASE_URL}{link}"
                anime_list.append({
                    'title': title,
                    'link': full_url,
                    'synopsis': synopsis,
                    'image': image
                })

        return anime_list
```

================================================================================
SECTION 7: CONCLUSION
================================================================================

Beautiful Soup VIABILITY: LOW (easy to scrape)

ADVANTAGES:
✓ Traditional server-rendered HTML
✓ RSS feed available
✓ Clean URL patterns
✓ Good meta tags for extraction
✓ Multiple content types (anime, manga, news, reviews)
✓ Seasonal anime data available

CAN EXTRACT:
- All news article content
- Images
- Categories/tags
- Publication dates
- Author information
- Anime/Manga rankings
- Seasonal anime lists
- User reviews

CANNOT EXTRACT:
- Login-required content
- User-specific data
- Video streaming content
- Forum posts (some require login)
- Private user lists

OVERALL: MyAnimeList is EASY to scrape with Beautiful Soup.
Best for: Anime & manga news, seasonal anime, rankings, and industry news.
Note: RSS feed available for news section makes it even easier.
"""