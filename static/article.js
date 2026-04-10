const themes = {
    aurora: 'aurora.css',
    sunset: 'sunset.css',
    forest: 'forest.css',
    midnight: 'midnight.css',
    neon: 'neon.css'
};

let showImages = localStorage.getItem('showImages') !== 'false';
const imageToggleBtn = document.getElementById('image-toggle');
const linkElement = document.getElementById('theme-stylesheet');
const currentTheme = new URLSearchParams(window.location.search).get('theme') || 'aurora';

function changeTheme(theme) {
    window.location.href = '/article?url=' + encodeURIComponent(window.originalUrl) + '&theme=' + theme + '&source=' + window.currentSource;
}

function toggleImages() {
    showImages = !showImages;
    localStorage.setItem('showImages', showImages);
    imageToggleBtn.textContent = showImages ? 'Hide Images' : 'Show Images';
    document.querySelectorAll('img').forEach(img => img.style.display = showImages ? '' : 'none');
    document.querySelectorAll('.related-placeholder').forEach(p => p.style.display = showImages ? 'none' : 'flex');
}

function toggleThemeMenu() {
    const menu = document.getElementById('theme-menu');
    menu.classList.toggle('open');
}

function setTheme(theme) {
    window.location.href = '/article?url=' + encodeURIComponent(window.originalUrl) + '&theme=' + theme + '&source=' + window.currentSource;
}

document.addEventListener('click', (e) => {
    const menu = document.getElementById('theme-menu');
    const btn = document.getElementById('theme-btn');
    if (menu && !menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove('open');
    }
});

imageToggleBtn.textContent = showImages ? 'Hide Images' : 'Show Images';

document.addEventListener('DOMContentLoaded', () => {
    window.originalUrl = document.body.getAttribute('data-original-url') || '';
    window.currentSource = new URLSearchParams(window.location.search).get('source') || 'bbc';
    
    if (!showImages) {
        document.querySelectorAll('img').forEach(img => img.style.display = 'none');
    }
    
    // Fetch related news images
    fetchRelatedImages();
});

function fetchRelatedImages() {
    const cards = document.querySelectorAll('.related-card');
    if (!cards.length) return;
    
    const urls = Array.from(cards).map((_, i) => {
        return cards[i].getAttribute('onclick').match(/url=([^&]+)/)[1];
    });
    
    if (!urls.length) return;
    
    fetch('/api/images?source=' + window.currentSource + '&' + urls.map(u => 'urls=' + encodeURIComponent(u)).join('&'))
        .then(res => {
            const reader = res.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            
            function processChunk() {
                return reader.read().then(({done, value}) => {
                    if (done) {
                        if (buffer.trim()) {
                            try {
                                const imgData = JSON.parse(buffer.trim());
                                updateRelatedCard(imgData);
                            } catch (e) {}
                        }
                        return;
                    }
                    
                    buffer += decoder.decode(value, {stream: true});
                    const lines = buffer.split('\n');
                    buffer = lines.pop();
                    
                    lines.forEach(line => {
                        if (line.trim()) {
                            try {
                                const imgData = JSON.parse(line.trim());
                                updateRelatedCard(imgData);
                            } catch (e) {}
                        }
                    });
                    
                    return processChunk();
                });
            }
            
            return processChunk();
        })
        .catch(err => console.error('Error fetching related images:', err));
}

function updateRelatedCard(imgData) {
    if (!imgData.image || !imgData.url) return;
    
    const cards = document.querySelectorAll('.related-card');
    cards.forEach((card, index) => {
        const onclick = card.getAttribute('onclick');
        if (onclick && onclick.includes(encodeURIComponent(imgData.url))) {
            const placeholder = card.querySelector('.related-placeholder');
            if (placeholder) {
                placeholder.outerHTML = `<img src="${imgData.image}" alt="" style="width:100%;height:120px;object-fit:cover;background:var(--display-bg);display:${showImages ? '' : 'none'}" onerror="this.style.display='none'">`;
            }
        }
    });
}

let ttsAudio = null;
let isTTSPlaying = false;

function toggleTTS() {
    const btn = document.getElementById('tts-btn');
    const textEl = document.getElementById('tts-text');
    
    if (isTTSPlaying) {
        if (ttsAudio) {
            ttsAudio.pause();
            ttsAudio = null;
        }
        isTTSPlaying = false;
        btn.classList.remove('playing');
        textEl.textContent = 'Read Aloud';
        return;
    }
    
    const title = document.querySelector('.article-title')?.textContent || '';
    const content = document.querySelector('.article-content')?.textContent || '';
    const fullText = title + '. ' + content.substring(0, 1500);
    
    btn.classList.add('playing');
    textEl.textContent = 'Playing...';
    isTTSPlaying = true;
    
    fetch('/api/tts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: fullText})
    })
    .then(res => {
        if (!res.ok) throw new Error('TTS failed');
        return res.arrayBuffer();
    })
    .then(arrayBuffer => {
        const blob = new Blob([arrayBuffer], {type: 'audio/wav'});
        const url = URL.createObjectURL(blob);
        ttsAudio = new Audio(url);
        
        ttsAudio.onended = () => {
            isTTSPlaying = false;
            btn.classList.remove('playing');
            textEl.textContent = 'Read Aloud';
            URL.revokeObjectURL(url);
        };
        
        ttsAudio.onerror = () => {
            isTTSPlaying = false;
            btn.classList.remove('playing');
            textEl.textContent = 'Error';
            console.error('Audio playback error');
        };
        
        ttsAudio.play();
    })
    .catch(err => {
        console.error('TTS error:', err);
        isTTSPlaying = false;
        btn.classList.remove('playing');
        textEl.textContent = 'Error';
    });
}