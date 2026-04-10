"""
================================================================================
THE GUARDIAN WEBSITE DEEP ANALYSIS
================================================================================

Date: 2026-04-10
Website: https://www.theguardian.com
Analysis Tool: Beautiful Soup + Requests

================================================================================
SECTION 1: BASIC STRUCTURE
================================================================================

URL PATTERNS:
- Homepage: https://www.theguardian.com
- Sections: /<section> (news, sport, culture, opinion, etc.)
- Articles: /<section>/<year>/<month>/<day>/<article-slug>
- Live Blogs: /<section>/live/<slug>
- Topics: /topic/<topic-name>
- Search: /search?q=<query>
- API: https://content.guardianapis.com/

UK-specific domains:
- theguardian.com (international)
- theguardian.co.uk (UK)

================================================================================
SECTION 2: TECHNOLOGY STACK
================================================================================

Frontend: DCR (Dotcom Rendering) - Guardian's React rendering
Backend: Complex configuration in window.guardian object
Analytics: Ophan, Google Analytics, various A/B testing
Ad Tech: Prebid (multiple bidders), Amazon, Google

KEY OBSERVATIONS:
- Very sophisticated architecture
- Multiple rendering paths (AMP, app, web)
- Heavy JavaScript usage
- Complex data structures in page source

================================================================================
SECTION 3: ARTICLE STRUCTURE ANALYSIS
================================================================================

META TAGS:
- Limited Open Graph (notable absence compared to others)
- Twitter cards minimal
- Complex data-layer in JavaScript

WINDOW.GUARDIAN CONFIG:
The Guardian puts extensive config in JavaScript:
```javascript
window.guardian = {
    config: {
        page: {
            webTitle: "Article Title",
            section: "news",
            contentType: "Article",
            // ... extensive config
        },
        switches: { /* Feature toggles */ },
        tests: { /* A/B test config */ }
    }
}
```

EXTRACTABLE DATA (WITH CHALLENGES):
✓ Title: h1 or window.guardian.config.page.webTitle
✓ Section: window.guardian.config.page.section
✓ Content Type: window.guardian.config.page.contentType
⚠ Author: Scattered in various elements
⚠ Date: In multiple formats
⚠ Content: Distributed across components

TYPICAL ARTICLE HTML:
- Complex, component-based structure
- Content split across multiple divs
- Different templates for articles vs liveblogs

================================================================================
SECTION 4: IMAGE HANDLING
================================================================================

Image Domains:
- assets.guim.co.uk (static assets)
- i.guim.co.uk (user-generated, comments)
- Static assets use hash-based URLs

Image Features:
- Responsive with srcset
- Lazy loading
- Multiple formats (JPEG, WebP)

================================================================================
SECTION 5: VIDEO CONTENT
================================================================================

Video Sources:
- YouTube embeds
- Guardian's own video player
- Third-party players

Handling:
- iframes for embeds
- Video metadata in page
- Limited direct stream access

================================================================================
SECTION 6: OFFICIAL API
================================================================================

The Guardian offers a public API!

API Endpoint: https://content.guardianapis.com/

Features:
- Search articles
- Get article by ID
- Fetch tags, sections
- Requires API key (free)

Example:
https://content.guardianapis.com/search?api-key=test&show-fields=body

RECOMMENDATION:
Use the official API instead of scraping when possible!

================================================================================
SECTION 7: SCRAPING STRATEGY
================================================================================

DIFFICULTY: HIGH (use API when possible)

OPTION 1 - USE OFFICIAL API (RECOMMENDED):
```python
import requests

class GuardianAPI:
    BASE_URL = 'https://content.guardianapis.com'
    API_KEY = 'YOUR_API_KEY'  # Get free key from Guardian
    
    def search_articles(self, query, limit=10):
        url = f'{self.BASE_URL}/search'
        params = {
            'api-key': self.API_KEY,
            'q': query,
            'page-size': limit,
            'show-fields': 'body,thumbnail,byline,firstPublicationDate'
        }
        
        resp = requests.get(url, params=params)
        data = resp.json()
        
        articles = []
        for item in data['response']['results']:
            articles.append({
                'title': item['webTitle'],
                'link': item['webUrl'],
                'date': item.get('fields', {}).get('firstPublicationDate'),
                'author': item.get('fields', {}).get('byline', ''),
                'image': item.get('fields', {}).get('thumbnail', '')
            })
        
        return articles
    
    def get_article(self, article_id):
        url = f'{self.BASE_URL}/{article_id}'
        params = {
            'api-key': self.API_KEY,
            'show-fields': 'body,thumbnail,byline,firstPublicationDate'
        }
        
        resp = requests.get(url, params=params)
        data = resp.json()
        
        article = data['response']['content']
        fields = article.get('fields', {})
        
        return {
            'title': article['webTitle'],
            'content': fields.get('body', ''),
            'author': fields.get('byline', ''),
            'date': fields.get('firstPublicationDate', ''),
            'image': fields.get('thumbnail', ''),
            'link': article['webUrl']
        }
```

OPTION 2 - DIRECT HTML SCRAPING (DIFFICULT):
```python
import requests
from bs4 import BeautifulSoup
import json

class GuardianScraper:
    BASE_URL = 'https://www.theguardian.com'
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    def get_article(self, url):
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Try to get title from config
        title = ''
        script = soup.find('script', string=lambda t: t and 'window.guardian' in t)
        if script:
            try:
                # Extract from window.guardian.config
                config_match = str(script).find('window.guardian = ')
                if config_match > 0:
                    # Complex extraction needed
                    pass
            except:
                pass
        
        # Fallback to HTML
        if not title:
            h1 = soup.find('h1')
            title = h1.get_text(strip=True) if h1 else ''
        
        # Content - look for article body
        content = ''
        article = soup.find('article')
        if article:
            # Guardian content may be in multiple containers
            for selector in ['.article-body', '[data-component="body"]', '.content-body']:
                body = article.select_one(selector)
                if body:
                    for p in body.find_all('p'):
                        text = p.get_text(strip=True)
                        if text:
                            content += f'<p>{text}</p>'
                    break
        
        # Try JSON-LD
        json_ld = soup.find('script', type='application/ld+json')
        if json_ld:
            try:
                data = json.loads(json_ld.string)
                if isinstance(data, dict):
                    title = title or data.get('headline', '')
                    content = content or data.get('articleBody', '')
            except:
                pass
        
        # Image
        img = soup.find('meta', property='og:image')
        image = img['content'] if img else ''
        
        return {
            'title': title,
            'content': content,
            'image': image,
            'link': url
        }
    
    def get_home_news(self):
        # Complex due to JavaScript rendering
        # Best to use API or specific section pages
        url = f'{self.BASE_URL}/news'
        resp = requests.get(url, headers=self.HEADERS)
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        articles = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/news/' in href and href != 'https://www.theguardian.com/news':
                title = link.get_text(strip=True)
                if title and len(title) > 20:
                    articles.append({
                        'title': title,
                        'link': href
                    })
        
        return articles[:30]
```

================================================================================
SECTION 8: CONCLUSION
================================================================================

Beautiful Soup VIABILITY: HIGH DIFFICULTY

STRONGLY RECOMMEND:
- Use the official Guardian API instead of scraping
- It's free, reliable, and respects terms of service

WHEN USING BEAUTIFUL SOUP:
✓ CAN extract: Basic content with effort
✓ CAN extract: Links and titles
✓ CAN extract: Some metadata via config

✗ CANNOT easily extract: Full article content
✗ CANNOT extract: Dynamic content
✗ CANNOT extract: Personalization
✗ CANNOT extract: Comments section

OVERALL ASSESSMENT:
The Guardian is one of the HARDEST major news sites to scrape.
Use the API whenever possible. Direct HTML scraping should be
a fallback option only.
"""

if __name__ == "__main__":
    print(__doc__)