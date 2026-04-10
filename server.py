from flask import Flask, render_template, jsonify, request, send_file
from bs4 import BeautifulSoup
import os
import glob
import importlib.util
import sys
import wave
from io import BytesIO

app = Flask(__name__)

# Dynamically load all scrapers from the scrapers folder
SCRAPERS = {}

def load_scrapers():
    """Dynamically load all scraper modules from the scrapers folder"""
    global SCRAPERS
    SCRAPERS = {}
    
    scrapers_dir = os.path.join(os.path.dirname(__file__), 'scrapers')
    
    # Ensure parent dir is in path
    parent_dir = os.path.dirname(__file__)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Import each scraper module to trigger register_scraper()
    for filename in os.listdir(scrapers_dir):
        if filename.endswith('.py') and not filename.startswith('_') and filename not in ('__init__.py', 'BaseScraper.py'):
            module_name = f'scrapers.{filename[:-3]}'
            try:
                __import__(module_name)
            except Exception as e:
                print(f"Failed to import {module_name}: {e}")
    
    # Now get the registered scrapers
    from scrapers import SCRAPERS as registered
    for name, scraper_class in registered.items():
        if isinstance(scraper_class, type):
            SCRAPERS[name] = scraper_class()
        else:
            SCRAPERS[name] = scraper_class
    
    print(f"Loaded scrapers: {list(SCRAPERS.keys())}")

load_scrapers()

PIPER_AVAILABLE = False

def install_piper():
    import subprocess
    import sys
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'piper-tts', '-q'])
        return True
    except Exception as e:
        print(f"Piper install failed: {e}")
        return False

def ensure_piper():
    global PIPER_AVAILABLE
    try:
        import piper
        from tts_service import piper_available
        PIPER_AVAILABLE = piper_available
    except ImportError:
        print("Piper not installed, attempting to install...")
        if install_piper():
            try:
                import piper
                from tts_service import piper_available
                PIPER_AVAILABLE = piper_available
            except Exception as e:
                print(f"Piper still not available after install: {e}")
                PIPER_AVAILABLE = False
        else:
            PIPER_AVAILABLE = False

ensure_piper()


@app.route('/api/scrapers')
def api_scrapers():
    """Return list of available scrapers"""
    return jsonify(list(SCRAPERS.keys()))


@app.route('/api/capabilities')
def api_capabilities():
    """Return capabilities for a specific scraper or all scrapers"""
    source = request.args.get('source')
    if source:
        scraper = SCRAPERS.get(source)
        if not scraper:
            return jsonify({'error': 'Scraper not found'}), 404
        return jsonify(scraper.get_capabilities())
    
    caps = {}
    for name, scraper in SCRAPERS.items():
        try:
            caps[name] = scraper.get_capabilities()
        except Exception as e:
            caps[name] = {'error': str(e)}
    return jsonify(caps)


@app.route('/api/sections')
def api_sections():
    source = request.args.get('source', 'bbc')
    default_scraper = list(SCRAPERS.values())[0] if SCRAPERS else None
    scraper = SCRAPERS.get(source, default_scraper)
    if not scraper:
        return jsonify([])
    return jsonify(scraper.get_sections())

def get_scraper():
    source = request.args.get('source', 'bbc')
    default_scraper = list(SCRAPERS.values())[0] if SCRAPERS else None
    return SCRAPERS.get(source, default_scraper)


@app.route('/')
@app.route('/index.html')
def spa_route():
    return render_template('index.html')


@app.route('/api/news')
def api_news():
    scraper = get_scraper()
    if not scraper:
        return jsonify({'error': 'Scraper not found'}), 404
    include_images = request.args.get('images', 'true').lower() == 'true'
    try:
        return jsonify(scraper.get_home_news(include_images))
    except Exception as e:
        print(f"Error in get_home_news: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/section')
def api_section():
    scraper = get_scraper()
    if not scraper:
        return jsonify({'error': 'Scraper not found'}), 404
    section = request.args.get('section', 'technology')
    include_images = request.args.get('images', 'true').lower() == 'true'
    try:
        return jsonify(scraper.get_section_news(section, include_images))
    except Exception as e:
        print(f"Error in get_section_news: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/images')
def api_images():
    scraper = get_scraper()
    urls = request.args.getlist('urls')
    
    def generate():
        for url in urls:
            img = scraper.get_article_image(url) if hasattr(scraper, 'get_article_image') else ''
            yield f'{{"url": "{url}", "image": "{img}"}}\n'
    
    from flask import Response
    return Response(generate(), mimetype='application/x-ndjson')


@app.route('/api/related')
def api_related():
    scraper = get_scraper()
    url = request.args.get('url', '')
    if not url:
        return jsonify([])
    return jsonify(scraper.get_related_news(url))


@app.route('/article')
def article():
    url = request.args.get('url', '')
    if not url:
        return "No URL provided", 400

    source = request.args.get('source', 'bbc')
    default_scraper = list(SCRAPERS.values())[0] if SCRAPERS else None
    scraper = SCRAPERS.get(source, default_scraper)
    if not scraper:
        return "Scraper not available", 404
    theme = request.args.get('theme', 'aurora')
    article_data = scraper.get_article(url)

    return render_template('article.html',
                         title=article_data['title'],
                         content=article_data['content'],
                         image=article_data['image'],
                         theme=theme,
                         original_url=url,
                         related_news=article_data['related_news'],
                         source=source,
                         tts_available=PIPER_AVAILABLE)


@app.route('/api/article')
def api_article():
    url = request.args.get('url', '')
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    source = request.args.get('source', 'bbc')
    default_scraper = list(SCRAPERS.values())[0] if SCRAPERS else None
    scraper = SCRAPERS.get(source, default_scraper)
    if not scraper:
        return jsonify({'error': 'Scraper not available'}), 404
    
    article_data = scraper.get_article(url)
    return jsonify(article_data)


@app.route('/api/tts', methods=['POST', 'GET'])
def api_tts():
    if not PIPER_AVAILABLE:
        return jsonify({'error': 'TTS not available'}), 503

    if request.method == 'POST':
        data = request.get_json()
        text = data.get('text', '')
    else:
        url = request.args.get('url', '')
        source = request.args.get('source', 'bbc')
        
        if not url:
            return jsonify({'error': 'No URL provided'}), 400
        
        default_scraper = list(SCRAPERS.values())[0] if SCRAPERS else None
        scraper = SCRAPERS.get(source, default_scraper)
        if not scraper:
            return jsonify({'error': 'Scraper not available'}), 404
        article_data = scraper.get_article(url)
        
        title = article_data.get('title', '')
        content = article_data.get('content', '')
        
        text = title + '. ' + ''.join([p.text for p in BeautifulSoup(content, 'html.parser').find_all('p')])[:2000]

    if not text:
        return jsonify({'error': 'No text provided'}), 400

    try:
        from tts_service import generate_tts_audio
        result = generate_tts_audio(text)

        if not result:
            return jsonify({'error': 'TTS generation failed'}), 500

        wav_data, sample_rate = result

        wav_io = BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(wav_data)

        wav_io.seek(0)

        return send_file(wav_io, mimetype='audio/wav', as_attachment=False)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)