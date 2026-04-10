const themes = {
    aurora: 'aurora.css',
    sunset: 'sunset.css',
    forest: 'forest.css',
    midnight: 'midnight.css',
    neon: 'neon.css'
};

let currentTheme = localStorage.getItem('newsTheme') || 'aurora';
const linkElement = document.getElementById('theme-stylesheet');
const gridLines = document.getElementById('grid-lines');

let autoRefreshTime = 60;
let timerInterval;
let currentSection = 'home';
let currentOutlet = localStorage.getItem('newsOutlet') || 'bbc';
let showImages = localStorage.getItem('showImages') !== 'false';
let availableSections = [];
let currentNewsData = [];

function updateTimer() {
    const timerEl = document.getElementById('timer');
    if (timerEl) {
        timerEl.textContent = `Auto-update in ${autoRefreshTime}s`;
        timerEl.classList.add('active');
    }
    autoRefreshTime--;
    if (autoRefreshTime < 0) {
        loadNews();
        autoRefreshTime = 60;
    }
}

function loadNews() {
    loadCurrentSection();
}

function loadCurrentSection() {
    if (currentSection === 'home') {
        loadNewsData('/api/news');
    } else {
        loadNewsData('/api/section?section=' + currentSection);
    }
}

function renderNewsCards(news) {
    const grid = document.getElementById('news-grid');
    if (!news || !news.length) {
        grid.innerHTML = '<div class="error">No news</div>';
        return;
    }

    grid.innerHTML = news.map((item, index) => {
        const tags = (item.category || '').split(',').map(t => t.trim()).filter(t => t);
        const tagHtml = tags.length ? tags.map(t => `<span>${t}</span>`).join('') : `<span>${item.category || 'News'}</span>`;
        
        const hasImage = item.image && item.image.length > 0;
        const imgHtml = hasImage 
            ? `<img src="${item.image}" alt="" style="display:${showImages ? '' : 'none'};width:100%;height:200px;object-fit:cover;background:var(--display-bg)" onerror="this.style.display='none'">`
            : `<div class="img-placeholder" style="display:${showImages ? '' : 'none'};width:100%;height:200px;background:var(--display-bg);display:flex;align-items:center;justify-content:center;color:var(--text-secondary)">Loading...</div>`;
            
        return `<div class="news-card" data-index="${index}" onclick="window.location.href='/article?url=${encodeURIComponent(item.link)}&theme=${currentTheme}&source=${currentOutlet}'">${imgHtml}<div class="news-content"><div class="news-category">${tagHtml}</div><div class="news-title">${item.title || ''}</div><div class="news-desc">${item.description || ''}</div></div></div>`;
    }).join('');
}

function fetchImages(news) {
    const urls = news.filter(n => !n.image).map(n => n.link);
    if (!urls.length) return;
    
    fetch('/api/images?source=' + currentOutlet + '&' + urls.map(u => 'urls=' + encodeURIComponent(u)).join('&'))
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
                                updateNewsCard(news, imgData);
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
                                updateNewsCard(news, imgData);
                            } catch (e) {}
                        }
                    });
                    
                    return processChunk();
                });
            }
            
            return processChunk();
        })
        .catch(err => console.error('Error fetching images:', err));
}

function updateNewsCard(news, imgData) {
    if (imgData.image && imgData.url) {
        const index = news.findIndex(n => n.link === imgData.url);
        if (index !== -1) {
            news[index].image = imgData.image;
        }
        const card = index !== -1 ? document.querySelector(`.news-card[data-index="${index}"]`) : null;
        if (card) {
            const placeholder = card.querySelector('.img-placeholder');
            if (placeholder) {
                placeholder.outerHTML = `<img src="${imgData.image}" alt="" style="display:${showImages ? '' : 'none'};width:100%;height:200px;object-fit:cover;background:var(--display-bg)" onerror="this.style.display='none'">`;
            }
        }
    }
}

function loadNewsData(url) {
    document.getElementById('news-grid').innerHTML = '<div class="loading">Loading...</div>';
    let apiUrl = url.includes('?') ? url + '&source=' + currentOutlet : url + '?source=' + currentOutlet;
    fetch(apiUrl).then(res => res.json()).then(news => {
        currentNewsData = news;
        renderNewsCards(news);
        fetchImages(news);
        autoRefreshTime = 60;
    }).catch(err => {
        console.error('Error loading news:', err);
        document.getElementById('news-grid').innerHTML = '<div class="error">Error loading news</div>';
    });
}

function loadSection(section, btn) {
    currentSection = section;
    document.querySelectorAll('.section-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    loadCurrentSection();
}

function toggleImages() {
    showImages = !showImages;
    localStorage.setItem('showImages', showImages);
    const imageToggleBtn = document.getElementById('image-toggle');
    if (showImages) {
        imageToggleBtn.classList.remove('hidden');
    } else {
        imageToggleBtn.classList.add('hidden');
    }
    document.querySelectorAll('.news-card img, .news-card .img-placeholder').forEach(img => img.style.display = showImages ? '' : 'none');
}

function toggleThemeMenu() {
    const menu = document.getElementById('theme-menu');
    menu.classList.toggle('open');
}

function setTheme(theme) {
    linkElement.href = '/static/' + themes[theme];
    currentTheme = theme;
    localStorage.setItem('newsTheme', currentTheme);
    gridLines.style.display = theme === 'neon' ? 'block' : 'none';
    
    // Update active state in menu
    document.querySelectorAll('.theme-option').forEach(opt => {
        opt.classList.toggle('active', opt.dataset.theme === theme);
    });
    
    // Close menu
    document.getElementById('theme-menu').classList.remove('open');
}

// Close theme menu when clicking outside
document.addEventListener('click', (e) => {
    const menu = document.getElementById('theme-menu');
    const btn = document.getElementById('theme-btn');
    if (menu && !menu.contains(e.target) && !btn.contains(e.target)) {
        menu.classList.remove('open');
    }
});

linkElement.href = '/static/' + themes[currentTheme];
if (gridLines) {
    gridLines.style.display = currentTheme === 'neon' ? 'block' : 'none';
}

const imageToggleBtn = document.getElementById('image-toggle');
if (!showImages) {
    imageToggleBtn.classList.add('hidden');
}

function initOutletSlider() {
    const toggleContainer = document.querySelector('.outlet-toggle');
    if (!toggleContainer) return;

    const slider = document.createElement('div');
    slider.className = 'outlet-slider';
    toggleContainer.appendChild(slider);

    const outletNames = {
        bbc: 'BBC NEWS',
        scmp: 'SCMP NEWS'
    };

    function updateSliderPosition() {
        const activeBtn = document.querySelector('.outlet-btn.active');
        if (activeBtn && slider) {
            slider.style.width = activeBtn.offsetWidth + 'px';
            slider.style.transform = `translateX(${activeBtn.offsetLeft}px)`;
        }
    }

    window.updateOutletSliderPosition = updateSliderPosition;

    setTimeout(updateSliderPosition, 100);
    window.addEventListener('resize', updateSliderPosition);

    document.querySelectorAll('.outlet-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const outlet = btn.dataset.outlet;
            const unsupported = ['cnn', 'reuters'];
            if (unsupported.includes(outlet)) {
                document.getElementById('news-grid').innerHTML = '<div class="error">Module not found: ' + outlet.toUpperCase() + ' scraper not implemented yet</div>';
                return;
            }
            document.querySelectorAll('.outlet-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            updateSliderPosition();

            currentOutlet = outlet;
            localStorage.setItem('newsOutlet', currentOutlet);
            const headerTitle = document.getElementById('header-title');
            if (headerTitle) {
                headerTitle.textContent = outletNames[currentOutlet] || 'NEWS';
            }
            loadSections();
        });
    });
}

function loadSections() {
    fetch('/api/sections?source=' + currentOutlet)
        .then(res => res.json())
        .then(sections => {
            availableSections = sections || [];
            const nav = document.getElementById('section-nav');
            if (!availableSections.length) {
                nav.innerHTML = '<div class="error">No sections available</div>';
                return;
            }
            nav.innerHTML = availableSections.map(s => 
                `<button class="section-btn ${s.default ? 'active' : ''}" data-section="${s.id}" onclick="loadSection('${s.id}', this)">${s.name}</button>`
            ).join('');
            
            const defaultSection = availableSections.find(s => s.default);
            if (defaultSection) {
                currentSection = defaultSection.id;
            }
            loadNews();
            
            // Update slider position after sections are rendered
            if (window.updateOutletSliderPosition) {
                window.updateOutletSliderPosition();
            }
        })
        .catch(err => {
            console.error('Error loading sections:', err);
            document.getElementById('section-nav').innerHTML = '<div class="error">Error loading sections</div>';
        });
}

initOutletSlider();

// Make sure active state and slider position are synced on load
setTimeout(() => {
    const outletNames = {
        bbc: 'BBC NEWS',
        scmp: 'SCMP NEWS'
    };
    const headerTitle = document.getElementById('header-title');
    document.querySelectorAll('.outlet-btn').forEach(btn => {
        if (btn.dataset.outlet === currentOutlet) {
            btn.classList.add('active');
            if (headerTitle) {
                headerTitle.textContent = outletNames[currentOutlet] || 'NEWS';
            }
        } else {
            btn.classList.remove('active');
        }
    });
    
    if (window.updateOutletSliderPosition) {
        window.updateOutletSliderPosition();
    }
}, 50);

loadSections();
timerInterval = setInterval(updateTimer, 1000);