const themes = {
    aurora: 'aurora.css',
    sunset: 'sunset.css',
    forest: 'forest.css',
    midnight: 'midnight.css',
    neon: 'neon.css'
};

function getUrlPath(url) {
    try {
        const parser = document.createElement('a');
        parser.href = url;
        return parser.pathname;
    } catch (e) {
        return '';
    }
}

window.addEventListener('popstate', function(e) {
    const state = e.state || history.state;
    if (state && state.page === 'home') {
        window.location.href = '/?theme=' + state.theme + '&source=' + state.source;
    }
});

let showImages;
let linkElement;
let imageToggleBtn;
let ttsAudio;
let isTTSPlaying = false;
let isTTSLoading = false;
let ttsQueue = [];
let currentAudioData = null;
let audioContext = null;
let audioBlobUrl = null;

function updateReadTime() {
    const timerEl = document.getElementById('timer');
    if (!timerEl) {
        console.log('Timer element not found');
        return;
    }
    
    const content = document.querySelector('.article-content')?.textContent || '';
    const wordCount = content.split(/\s+/).filter(w => w.length > 0).length;
    const readTimeMin = Math.ceil(wordCount / 200);
    
    if (ttsQueue.length > 0) {
        const status = isTTSPlaying ? '▶' : isTTSLoading ? '⏳' : '⏸';
        const text = `Q:${ttsQueue.length} ${status}`;
        console.log('Setting timer to:', text);
        timerEl.textContent = text;
    } else if (isTTSPlaying && ttsAudio && ttsAudio.duration) {
        const remaining = Math.max(0, Math.ceil(ttsAudio.duration - ttsAudio.currentTime));
        timerEl.textContent = `TTS: ${remaining}s`;
    } else {
        timerEl.textContent = `~${readTimeMin} min`;
    }
}

function changeTheme(theme) {
    window.location.href = '/article?url=' + encodeURIComponent(window.originalUrl) + '&theme=' + theme + '&source=' + window.currentSource;
}

function goBack() {
    if (history.length > 1) {
        history.back();
    } else {
        renderHomePageInline();
    }
}

function renderHomePageInline() {
    const source = localStorage.getItem('newsOutlet') || 'bbc';
    const theme = localStorage.getItem('newsTheme') || 'aurora';
    
    history.pushState({page: 'home', source: source, theme: theme}, '', '/?theme=' + theme + '&source=' + source);
    
    fetch('/')
        .then(r => r.text())
        .then(html => {
            document.body.innerHTML = html;
            // Trigger main.js init
            const script = document.createElement('script');
            script.src = '/static/main.js';
            script.onload = () => {
                if (typeof initOutletSlider === 'function') initOutletSlider();
                if (typeof loadSections === 'function') loadSections();
            };
            document.body.appendChild(script);
        });
}

function goToArticle(url) {
    const source = localStorage.getItem('newsOutlet') || 'bbc';
    const theme = localStorage.getItem('newsTheme') || 'aurora';
    
    const container = document.querySelector('.container');
    if (container) {
        container.innerHTML = '<div class="loading">Loading article...</div>';
    }
    
    // Decode in case it was double-encoded
    const decodedUrl = decodeURIComponent(url);
    
    fetch('/api/article?url=' + encodeURIComponent(decodedUrl) + '&source=' + source)
        .then(res => res.json())
        .then(data => {
            renderArticlePage(data, decodedUrl);
        })
        .catch(err => {
            if (container) {
                container.innerHTML = '<div class="error">Error loading article: ' + err.message + '</div>';
            }
        });
}

function renderArticlePage(data, url) {
    const source = localStorage.getItem('newsOutlet') || 'bbc';
    const theme = localStorage.getItem('newsTheme') || 'aurora';
    
    const container = document.querySelector('.container');
    if (!container) return;
    
    const relatedHtml = (data.related_news || []).map(item => 
        '<div class="news-card" onclick="goToArticle(\'' + encodeURIComponent(item.link) + '\')">' +
        (item.image ? '<img src="' + item.image + '">' : '') +
        '<div class="news-content"><div class="news-title">' + (item.title || '') + '</div></div></div>'
    ).join('');
    
    container.innerHTML = '<a class="back-btn" onclick="renderHomePage()">← Back to News</a>' +
        '<div class="article-card">' + (data.image ? '<img src="' + data.image + '">' : '') +
        '<h1 class="article-title">' + (data.title || '') + '</h1>' +
        '<div class="summary-box"></div>' +
        '<div class="article-content">' + (data.content || '') + '</div></div>' +
        (relatedHtml ? '<h2 class="related-title">Related News</h2><div class="news-grid">' + relatedHtml + '</div>' : '');
    
    // Auto generate summary
    var summaryBox = document.querySelector('.summary-box');
    var content = document.querySelector('.article-content');
    console.log('Summary box:', summaryBox);
    console.log('Content:', content ? content.textContent.slice(0, 30) : 'NOT FOUND');
    
    if (summaryBox && content && content.textContent) {
        summaryBox.innerHTML = '<div style="font-size:10px;color:var(--text-secondary);margin-bottom:8px;text-transform:uppercase;">AI Summary</div><div style="font-size:14px;color:var(--text-secondary);">Loading...</div>';
        
        fetch('/api/summarize?text=' + encodeURIComponent(content.textContent.slice(0, 2000)))
            .then(function(res) { return res.json(); })
            .then(function(data) {
                if (data.summary) {
                    summaryBox.innerHTML = '<div style="font-size:10px;color:var(--text-secondary);margin-bottom:8px;text-transform:uppercase;">AI Summary</div><div style="font-size:14px;color:var(--text-primary);line-height:1.5;">' + data.summary + '</div>';
                } else {
                    summaryBox.innerHTML = '<div style="font-size:10px;color:var(--text-secondary);margin-bottom:8px;text-transform:uppercase;">AI Summary</div><div style="font-size:14px;color:var(--text-secondary);">No summary available</div>';
                }
            })
            .catch(function(err) { 
                summaryBox.innerHTML = '<div style="font-size:10px;color:var(--text-secondary);margin-bottom:8px;text-transform:uppercase;">AI Summary</div><div style="font-size:14px;color:var(--text-secondary);">Error generating summary</div>';
            });
    }
}

function showHomeInline() {
    document.body.innerHTML = '<div style="padding:100px;text-align:center;color:#fff;background:#000">Loading...</div>';
    const source = window.currentSource || localStorage.getItem('newsOutlet') || 'bbc';
    const theme = localStorage.getItem('newsTheme') || 'aurora';
    
    fetch('/')
        .then(res => res.text())
        .then(html => {
            // Replace body with the index page body
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const bodyContent = doc.body.innerHTML;
            
            // Update to use the current source
            document.body.innerHTML = bodyContent;
            
            // Update the header title
            const headerTitle = document.getElementById('header-title');
            if (headerTitle) {
                headerTitle.textContent = source.toUpperCase() + ' NEWS';
            }
            
            // Manually load and execute main.js to get its functions
            const script = document.createElement('script');
            script.src = '/static/main.js';
            script.onload = function() {
                // Set current outlet and load sections
                currentOutlet = source;
                loadSections();
            };
            document.head.appendChild(script);
        })
        .catch(err => {
            console.error('Error loading:', err);
            document.body.innerHTML = '<div style="padding:100px;text-align:center;color:red">Error loading: ' + err.message + '</div>';
        });
}

function loadCurrentSectionInline(source, theme) {
    fetch('/api/news?source=' + source).then(r => r.json()).then(news => {
        const newsCards = news.map((item, idx) => {
            const tags = (item.category || '').split(',').map(t => t.trim()).filter(t => t);
            const tagHtml = tags.length ? tags.map(t => `<span>${t}</span>`).join('') : `<span>${item.category || 'News'}</span>`;
            return `<div class="news-card" data-index="${idx}" onclick="navigateToArticle('${encodeURIComponent(item.link)}', '${theme}', '${source}')">
                ${item.image ? `<img src="${item.image}" alt="" style="width:100%;height:200px;object-fit:cover;background:var(--display-bg)">` : ''}
                <div class="news-content">
                    <div class="news-category">${tagHtml}</div>
                    <div class="news-title">${item.title || ''}</div>
                    <div class="news-desc">${item.description || ''}</div>
                </div>
            </div>`;
        }).join('');
        document.getElementById('news-grid').innerHTML = newsCards;
    });
}

function toggleImagesInline() {
    showImages = !showImages;
    localStorage.setItem('showImages', showImages);
    document.querySelectorAll('.news-card img').forEach(img => img.style.display = showImages ? '' : 'none');
    const imageToggleBtn = document.getElementById('image-toggle');
    if (imageToggleBtn) {
        imageToggleBtn.classList.toggle('hidden', !showImages);
    }
}

function setThemePersistent(newTheme) {
    localStorage.setItem('newsTheme', newTheme);
    const linkEl = document.querySelector('link[href*=".css"]');
    if (linkEl) {
        linkEl.href = '/static/' + newTheme + '.css';
    }
    document.querySelectorAll('.theme-option').forEach(opt => {
        opt.classList.toggle('active', opt.getAttribute('onclick').includes(newTheme));
    });
    document.getElementById('theme-menu').classList.remove('open');
}

function setOutletNoReload(source, theme) {
    window.currentSource = source;
    localStorage.setItem('newsOutlet', source);
    showHomeInline();
}

function loadSectionNoReload(section, source, theme) {
    fetch('/api/section?section=' + section + '&source=' + source).then(r => r.json()).then(news => {
        const newsCards = news.map((item, idx) => {
            return `<div class="news-card" data-index="${idx}" onclick="navigateToArticle('${encodeURIComponent(item.link)}', '${theme}', '${source}')">
                ${item.image ? `<img src="${item.image}" alt="" style="width:100%;height:200px;object-fit:cover;background:var(--display-bg)">` : ''}
                <div class="news-content">
                    <div class="news-category"><span>${item.category || section.toUpperCase()}</span></div>
                    <div class="news-title">${item.title || ''}</div>
                    <div class="news-desc">${item.description || ''}</div>
                </div>
            </div>`;
        }).join('');
        
        document.getElementById('news-grid').innerHTML = newsCards;
        document.querySelectorAll('.section-btn').forEach(btn => {
            btn.classList.toggle('active', btn.getAttribute('onclick').includes(section));
        });
    });
}

function navigateToArticle(url, theme, source) {
    window.location.href = '/article?url=' + url + '&theme=' + theme + '&source=' + source;
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
    linkElement.href = '/static/' + themes[theme];
    localStorage.setItem('newsTheme', theme);
    
    document.querySelectorAll('.theme-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.theme === theme);
    });
    
    document.getElementById('theme-menu').classList.remove('open');
}

document.addEventListener('click', (e) => {
    const menu = document.getElementById('theme-menu');
    const btn = document.getElementById('theme-btn');
    if (menu && !menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove('open');
    }
});

setInterval(updateReadTime, 1000);

document.addEventListener('DOMContentLoaded', () => {
    showImages = localStorage.getItem('showImages') !== 'false';
    imageToggleBtn = document.getElementById('image-toggle');
    linkElement = document.getElementById('theme-stylesheet');
    const urlParams = new URLSearchParams(window.location.search);
    const currentTheme = urlParams.get('theme') || 'aurora';
    const currentSource = urlParams.get('source') || 'bbc';
    const originalUrl = urlParams.get('url') || '';
    
    // Push article state for back button support
    if (!history.state || history.state.page !== 'article') {
        history.replaceState({page: 'article', url: originalUrl, theme: currentTheme, source: currentSource}, '', window.location.href);
    }
    
    // Initialize timer immediately
    const timerEl = document.getElementById('timer');
    if (timerEl) {
        timerEl.textContent = 'Tap + to queue';
    }
    
    if (linkElement) {
        linkElement.href = '/static/' + themes[currentTheme];
    }
    
    if (imageToggleBtn) {
        imageToggleBtn.textContent = showImages ? 'Hide Images' : 'Show Images';
    }
    
    window.originalUrl = document.body.getAttribute('data-original-url') || originalUrl;
    window.currentSource = currentSource;
    
    if (!showImages) {
        document.querySelectorAll('img').forEach(img => img.style.display = 'none');
    }
    
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
    
    const imgPath = getUrlPath(imgData.url);
    const cards = document.querySelectorAll('.related-card');
    cards.forEach((card, index) => {
        const onclick = card.getAttribute('onclick');
        if (onclick) {
            const urlMatch = onclick.match(/url=([^&']+)/);
            if (urlMatch) {
                const cardPath = getUrlPath(decodeURIComponent(urlMatch[1]));
                if (cardPath === imgPath) {
                    const placeholder = card.querySelector('.related-placeholder');
                    if (placeholder) {
                        placeholder.outerHTML = '<img src="' + imgData.image + '" alt="" style="width:100%;height:120px;object-fit:cover;background:var(--display-bg);display:' + (showImages ? '' : 'none') + '" onerror="this.style.display=\'none\'">';
                    }
                }
            }
        }
    });
}

ttsAudio = null;
isTTSPlaying = false;
isTTSLoading = false;
ttsQueue = [];
currentAudioData = null;
audioContext = null;
audioBlobUrl = null;

function addToQueue(url, title, source) {
    const queueItem = { url, title, source, status: 'pending' };
    ttsQueue.push(queueItem);
    updateQueueDisplay();
    
    if (!isTTSPlaying && !isTTSLoading && ttsQueue.length === 1) {
        processNextInQueue();
    }
}

function addToQueueFromCard(url, source) {
    addToQueue(url, '', source);
    
    // Visual feedback
    const cards = document.querySelectorAll('.related-card');
    cards.forEach(card => {
        const onclick = card.getAttribute('onclick');
        if (onclick && onclick.includes(url)) {
            const btn = card.querySelector('.queue-btn');
            if (btn) {
                btn.textContent = '✓';
                btn.style.background = 'var(--orb-1)';
                btn.style.color = 'var(--bg-primary)';
            }
        }
    });
}

function updateQueueDisplay() {
    const timerEl = document.getElementById('timer');
    if (!timerEl) return;
    
    const content = document.querySelector('.article-content')?.textContent || '';
    const wordCount = content.split(/\s+/).filter(w => w.length > 0).length;
    const readTimeMin = Math.ceil(wordCount / 200);
    
    if (ttsQueue.length > 0) {
        const status = isTTSPlaying ? '▶' : isTTSLoading ? '⏳' : '⏸';
        timerEl.textContent = `Q:${ttsQueue.length} ${status}`;
    } else if (isTTSPlaying && ttsAudio && ttsAudio.duration) {
        const remaining = Math.max(0, Math.ceil(ttsAudio.duration - ttsAudio.currentTime));
        timerEl.textContent = `TTS: ${remaining}s`;
    } else {
        timerEl.textContent = `~${readTimeMin} min`;
    }
}

function processNextInQueue() {
    if (ttsQueue.length === 0 || isTTSPlaying || isTTSLoading) return;
    
    const item = ttsQueue[0];
    item.status = 'loading';
    
    const btn = document.getElementById('tts-btn');
    btn.classList.add('loading');
    isTTSLoading = true;
    
    fetch('/api/tts?url=' + encodeURIComponent(item.url) + '&source=' + item.source)
        .then(res => {
            if (!res.ok) throw new Error('TTS failed');
            return res.arrayBuffer();
        })
        .then(arrayBuffer => {
            isTTSLoading = false;
            btn.classList.remove('loading');
            
            if (audioBlobUrl) URL.revokeObjectURL(audioBlobUrl);
            const blob = new Blob([arrayBuffer], {type: 'audio/wav'});
            audioBlobUrl = URL.createObjectURL(blob);
            
            ttsAudio = new Audio(audioBlobUrl);
            currentAudioData = item;
            
            ttsAudio.onended = () => {
                isTTSPlaying = false;
                btn.classList.remove('playing');
                ttsQueue.shift();
                updateQueueDisplay();
                if (ttsQueue.length > 0) {
                    processNextInQueue();
                }
            };
            
            ttsAudio.onerror = () => {
                isTTSPlaying = false;
                btn.classList.remove('playing');
                console.error('Audio playback error');
            };
            
            ttsAudio.play();
            isTTSPlaying = true;
            btn.classList.add('playing');
            item.status = 'playing';
            updateQueueDisplay();
        })
        .catch(err => {
            console.error('TTS error:', err);
            isTTSLoading = false;
            isTTSPlaying = false;
            btn.classList.remove('loading', 'playing');
            ttsQueue.shift();
            if (ttsQueue.length > 0) processNextInQueue();
        });
}

function toggleTTS() {
    const btn = document.getElementById('tts-btn');
    const currentUrl = window.originalUrl || '';
    const currentSource = window.currentSource || 'bbc';
    const currentTitle = document.querySelector('.article-title')?.textContent || '';
    
    if (isTTSPlaying || isTTSLoading) {
        if (ttsAudio) {
            ttsAudio.pause();
            ttsAudio = null;
        }
        isTTSPlaying = false;
        isTTSLoading = false;
        btn.classList.remove('playing', 'loading');
        ttsQueue = [];
        updateQueueDisplay();
        return;
    }
    
    addToQueue(currentUrl, currentTitle, currentSource);
}