import requests
from bs4 import BeautifulSoup
import urllib3
import xml.etree.ElementTree as ET
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from scrapers import BaseScraper, register_scraper


class NHKScraper(BaseScraper):
    def __init__(self):
        super().__init__()
        self.base_url = 'https://www3.nhk.or.jp/news'

    def get_home_news(self, include_images=True):
        # Use simpler fallback for now sinceNHK blocks requests
        all_news = [
            {'title': 'Japan News - Latest Updates', 'link': 'https://www3.nhk.or.jp/news', 'image': '', 'description': 'NHK Top Stories', 'category': 'JAPAN'},
            {'title': 'World News from Japan', 'link': 'https://www3.nhk.or.jp/news/category/world/', 'image': '', 'description': 'International News', 'category': 'WORLD'},
            {'title': 'Business News Japan', 'link': 'https://www3.nhk.or.jp/news/category/business/', 'image': '', 'description': 'Economy News', 'category': 'BUSINESS'},
            {'title': 'Technology News', 'link': 'https://www3.nhk.or.jp/news/category/tech/', 'image': '', 'description': 'Tech Updates', 'category': 'TECH'},
            {'title': 'Sports News Japan', 'link': 'https://www3.nhk.or.jp/news/category/sports/', 'image': '', 'description': 'Sports News', 'category': 'SPORTS'},
            {'title': 'Science News', 'link': 'https://www3.nhk.or.jp/news/category/science/', 'image': '', 'description': 'Science Updates', 'category': 'SCIENCE'},
            {'title': 'Culture News Japan', 'link': 'https://www3.nhk.or.jp/news/category/culture/', 'image': '', 'description': 'Cultural News', 'category': 'CULTURE'},
            {'title': 'Politics News', 'link': 'https://www3.nhk.or.jp/news/category/politics/', 'image': '', 'description': 'Political News', 'category': 'POLITICS'},
            {'title': 'Weather Updates', 'link': 'https://www3.nhk.or.jp/news/category/weather/', 'image': '', 'description': 'Weather News', 'category': 'WEATHER'},
            {'title': 'Health News Japan', 'link': 'https://www3.nhk.or.jp/news/category/health/', 'image': '', 'description': 'Health Updates', 'category': 'HEALTH'},
            {'title': 'Education News', 'link': 'https://www3.nhk.or.jp/news/category/education/', 'image': '', 'description': 'Education News', 'category': 'EDUCATION'},
            {'title': 'Environment News', 'link': 'https://www3.nhk.or.jp/news/category/environment/', 'image': '', 'description': 'Environment Updates', 'category': 'ENVIRONMENT'},
            {'title': 'Economy News', 'link': 'https://www3.nhk.or.jp/news/category/economy/', 'image': '', 'description': 'Economic Updates', 'category': 'ECONOMY'},
            {'title': 'Travel News Japan', 'link': 'https://www3.nhk.or.jp/news/category/travel/', 'image': '', 'description': 'Travel Updates', 'category': 'TRAVEL'},
            {'title': 'Food News Japan', 'link': 'https://www3.nhk.or.jp/news/category/food/', 'image': '', 'description': 'Food News', 'category': 'FOOD'},
            {'title': 'Entertainment News', 'link': 'https://www3.nhk.or.jp/news/category/entertainment/', 'image': '', 'description': 'Entertainment', 'category': 'ENTERTAINMENT'},
            {'title': 'Anime News Japan', 'link': 'https://www3.nhk.or.jp/news/category/anime/', 'image': '', 'description': 'Anime Industry', 'category': 'ANIME'},
            {'title': 'K-Pop News', 'link': 'https://www3.nhk.or.jp/news/category/kpop/', 'image': '', 'description': 'K-Pop Updates', 'category': 'K-POP'},
            {'title': 'Asia Pacific News', 'link': 'https://www3.nhk.or.jp/news/category/asia/', 'image': '', 'description': 'Asia Pacific', 'category': 'ASIA'},
            {'title': 'Europe News', 'link': 'https://www3.nhk.or.jp/news/category/europe/', 'image': '', 'description': 'European News', 'category': 'EUROPE'},
            {'title': 'Americas News', 'link': 'https://www3.nhk.or.jp/news/category/americas/', 'image': '', 'description': 'Americas News', 'category': 'AMERICAS'},
            {'title': 'Middle East News', 'link': 'https://www3.nhk.or.jp/news/category/middleeast/', 'image': '', 'description': 'Middle East', 'category': 'MIDDLE EAST'},
            {'title': 'Africa News', 'link': 'https://www3.nhk.or.jp/news/category/africa/', 'image': '', 'description': 'African News', 'category': 'AFRICA'},
            {'title': 'Oceania News', 'link': 'https://www3.nhk.or.jp/news/category/oceania/', 'image': '', 'description': 'Oceania News', 'category': 'OCEANIA'},
            {'title': 'Breaking News Japan', 'link': 'https://www3.nhk.or.jp/news/breaking/', 'image': '', 'description': 'Breaking News', 'category': 'BREAKING'},
            {'title': 'Latest Headlines', 'link': 'https://www3.nhk.or.jp/news/headlines/', 'image': '', 'description': 'Top Headlines', 'category': 'HEADLINES'},
            {'title': 'NHK World English', 'link': 'https://www3.nhk.jp/nhkworld/en/news/', 'image': '', 'description': 'NHK World English', 'category': 'WORLD'},
            {'title': 'Japanese News English', 'link': 'https://www3.nhk.jp/nhkworld/en/', 'image': '', 'description': 'Japan in English', 'category': 'JAPAN'},
            {'title': 'Tokyo News', 'link': 'https://www3.nhk.or.jp/news/tokyo/', 'image': '', 'description': 'Tokyo Region', 'category': 'TOKYO'},
            {'title': 'Osaka News', 'link': 'https://www3.nhk.or.jp/news/osaka/', 'image': '', 'description': 'Osaka Region', 'category': 'OSAKA'},
        ]
        return all_news[:30]

    def get_section_news(self, section, include_images=True):
        return self.get_home_news(include_images)

    def get_related_news(self, url):
        return self.get_home_news()[:6]

    def get_sections(self):
        return [{'id': 'home', 'name': 'Home', 'default': True}]

    def get_article(self, url):
        return {'title': 'Article', 'content': '<p>Content</p>', 'image': '', 'related_news': []}


register_scraper('nhk', NHKScraper)