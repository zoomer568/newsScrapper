"""
================================================================================
BANGKOK POST WEBSITE DEEP ANALYSIS
================================================================================

Date: 2026-04-10
Website: https://www.bangkokpost.com
Analysis Tool: Beautiful Soup + Requests

================================================================================
SECTION 1: BASIC STRUCTURE
================================================================================

URL PATTERNS:
- Homepage: https://www.bangkokpost.com
- Sections: /news, /thailand, /business, /world, /sports, /life
- Articles: /<category>/<article-id>/<slug>
- Video: /video
- Photos: /photo
- Podcast: /podcast
- RSS: /digitalproduct/rss

SECTIONS AVAILABLE:
- News (All)
- Thailand (General, Politics, Special Reports, PR News, People)
- Business (General, Motoring, Investment)
- Opinion (Columnist, Postbag)
- World
- Property
- Sports
- Life (Arts & Entertainment, Social & Lifestyle, Travel, Tech)
- Guru (Eat, Travel, Join, Watch, Stuff, Horoscope, Deals)
- Learning
- Multimedia (Video, Photos, Podcast, Visual Stories)
- Events
- Sustainability

================================================================================
SECTION 2: TECHNOLOGY STACK
================================================================================

Frontend Framework: Bootstrap 5 + Custom JavaScript
CSS: Bootstrap CSS + custom styles
Analytics: Google Analytics, Taboola, various ad networks
CDN: static.bangkokpost.com

KEY OBSERVATIONS:
- Traditional server-rendered HTML (easy to scrape)
- Bootstrap-based responsive design
- Lazy loading for images (data-src attributes)
- JSON-LD structured data available
- Rich meta tags

================================================================================
SECTION 3: ARTICLE STRUCTURE ANALYSIS
================================================================================

META TAGS FOUND:
- og:title, og:type, og:url, og:image, og:site_name, og:description
- twitter:card, twitter:site, twitter:title, twitter:description, twitter:image
- schema.org JSON-LD for Organization and WebPage

SCHEMA MARKUP:
- WebSite with potentialAction for search
- Organization with contact info and social links
- WebPage with breadcrumb

EXTRACTABLE DATA:
✓ Title: h1 or meta[property="og:title"]
✓ Summary: meta[name="description"] or meta[property="og:description"]
✓ Content: article body with paragraphs
✓ Image: meta[property="og:image"] or article figure img
✓ Category: From URL path or breadcrumb
✓ Date: From article metadata

================================================================================
SECTION 4: IMAGE HANDLING
================================================================================

CDN Domains:
- static.bangkokpost.com (main assets)
- c1.bangkokpost.com (content images)

Image URL Patterns:
- https://static.bangkokpost.com/media/content/.../image.jpg
- WebP format available: image.webp
- Responsive with srcset: 350w, 500w, 700w

Lazy Loading:
- data-src attribute for lazy-loaded images
- class="lazyload"
- data-srcset for responsive images

================================================================================
SECTION 5: RSS FEED
================================================================================

RSS URL: https://www.bangkokpost.com/digitalproduct/rss

Format: Standard RSS 2.0
Contains: Various content categories

================================================================================
SECTION 6: SCRAPING STRATEGY
================================================================================

DIFFICULTY: LOW (easy to scrape)

CODE TEMPLATE:
```python
import requests
from bs4 import BeautifulSoup

class BangkokPostScraper:
    BASE_URL = 'https://www.bangkokpost.com'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def get_home_news(self):
        resp = requests.get(self.BASE_URL, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        articles = []
        
        # Find articles in highlight section
        for item in soup.select('.section-highlight .item, .news--list, .timeline-first'):
            link = item.find('a', href=True)
            if not link:
                continue
            
            href = link.get('href', '')
            title = link.get_text(strip=True)
            
            # Get image
            img = item.find('img')
            image = ''
            if img:
                image = img.get('data-src') or img.get('src') or ''
            
            # Get category
            category_tag = item.find('a', href=lambda x: x and '/' in x)
            category = ''
            if category_tag:
                category = category_tag.get_text(strip=True)
            
            if title and href and len(title) > 10:
                full_url = href if href.startswith('http') else f'{self.BASE_URL}{href}'
                articles.append({
                    'title': title[:100],
                    'link': full_url,
                    'image': image,
                    'category': category
                })
        
        return articles[:30]
    
    def get_article(self, url):
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract title
        title = soup.find('h1')
        title = title.get_text(strip=True) if title else ''
        
        # Try meta tag
        if not title:
            meta_title = soup.find('meta', property='og:title')
            title = meta_title['content'] if meta_title else ''
        
        # Extract content
        content = ''
        article_body = soup.find('article') or soup.find('.article-content')
        if article_body:
            for p in article_body.find_all('p'):
                text = p.get_text(strip=True)
                if text and len(text) > 20:
                    content += f'<p>{text}</p>'
        
        # Extract image
        img = soup.find('meta', property='og:image')
        image = img['content'] if img else ''
        
        # Try article figure
        if not image:
            figure = soup.find('figure')
            if figure:
                img = figure.find('img')
                if img:
                    image = img.get('data-src') or img.get('src') or ''
        
        return {
            'title': title,
            'content': content,
            'image': image,
            'link': url
        }
    
    def get_rss_feed(self):
        import xml.etree.ElementTree as ET
        rss_url = f'{self.BASE_URL}/digitalproduct/rss'
        
        try:
            resp = requests.get(rss_url, headers=self.HEADERS, timeout=10)
            root = ET.fromstring(resp.content)
            
            items = []
            for item in root.findall('.//item')[:30]:
                title = item.find('title').text or ''
                link = item.find('link').text or ''
                desc = item.find('description').text or ''
                
                items.append({
                    'title': title,
                    'link': link,
                    'description': desc[:200] if desc else ''
                })
            
            return items
        except Exception as e:
            print(f"RSS error: {e}")
            return []
```

================================================================================
SECTION 7: CONCLUSION
================================================================================

Beautiful Soup VIABILITY: LOW (very easy)

ADVANTAGES:
✓ Traditional server-rendered HTML
✓ Bootstrap makes structure predictable
✓ RSS feed available
✓ JSON-LD structured data
✓ Clean URL patterns
✓ Lazy loading with data-src (still extractable)

CAN EXTRACT:
- All article content
- Images (from data-src)
- Categories from URLs
- Publication dates

LIMITATIONS:
- Lazy loaded images need data-src not src
- Some dynamic features unavailable

OVERALL: Bangkok Post is ONE OF THE EASIEST news sites to scrape.
Similar difficulty level to Korea Herald and Al Jazeera.
"""

if __name__ == "__main__":
    print(__doc__)