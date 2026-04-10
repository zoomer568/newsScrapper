from flask import Flask, render_template, jsonify, request, send_file
import os
import tempfile
import wave
from io import BytesIO

from scrapers.bbc import BBCScraper
from scrapers.scmp import SCMPScraper

app = Flask(__name__)

SCRAPERS = {
    'bbc': BBCScraper(),
    'scmp': SCMPScraper()
}

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


@app.route('/api/sections')
def api_sections():
    source = request.args.get('source', 'bbc')
    scraper = SCRAPERS.get(source, SCRAPERS['bbc'])
    return jsonify(scraper.get_sections())

def get_scraper():
    source = request.args.get('source', 'bbc')
    return SCRAPERS.get(source, SCRAPERS['bbc'])


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/news')
def api_news():
    scraper = get_scraper()
    include_images = request.args.get('images', 'true').lower() == 'true'
    return jsonify(scraper.get_home_news(include_images))


@app.route('/api/section')
def api_section():
    scraper = get_scraper()
    section = request.args.get('section', 'technology')
    include_images = request.args.get('images', 'true').lower() == 'true'
    return jsonify(scraper.get_section_news(section, include_images))


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
    scraper = SCRAPERS.get(source, SCRAPERS['bbc'])
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


@app.route('/api/tts', methods=['POST'])
def api_tts():
    if not PIPER_AVAILABLE:
        return jsonify({'error': 'TTS not available'}), 503

    data = request.get_json()
    text = data.get('text', '')
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