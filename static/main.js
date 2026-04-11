(function() {
    'use strict';

    const NewsApp = {
        config: {
            themes: {
                aurora: 'aurora.css',
                sunset: 'sunset.css',
                forest: 'forest.css',
                midnight: 'midnight.css',
                neon: 'neon.css'
            },
            defaultTheme: 'aurora',
            defaultSource: 'bbc',
            apiTimeout: 15000
        },

        state: {
            currentTheme: localStorage.getItem('newsTheme') || 'aurora',
            currentSource: localStorage.getItem('newsOutlet') || 'bbc',
            currentSection: 'home',
            showImages: localStorage.getItem('showImages') !== 'false',
            currentNews: [],
            capabilities: {},
            ttsQueue: [],
            isTTSPlaying: false,
            isTTSLoading: false,
            ttsAudio: null,
            currentArticleUrl: '',
            currentArticleTitle: ''
        },

        elements: {},
        
        themes: {
            aurora: 'aurora.css',
            sunset: 'sunset.css',
            forest: 'forest.css',
            midnight: 'midnight.css',
            neon: 'neon.css'
        },

        init: function() {
            this.cacheElements();
            this.bindEvents();
            this.loadInitialData();
        },

        cacheElements: function() {
            this.elements = {
                themeStylesheet: document.getElementById('theme-stylesheet'),
                themeMenu: document.getElementById('theme-menu'),
                themeBtn: document.getElementById('theme-btn'),
                outletSelect: document.getElementById('outlet-select'),
                sectionNav: document.getElementById('section-nav'),
                newsGrid: document.getElementById('news-grid'),
                headerTitle: document.getElementById('header-title'),
                footer: document.querySelector('.footer'),
                mainContainer: document.getElementById('main-container'),
                ttsBtn: document.getElementById('tts-btn'),
                ttsMenu: document.getElementById('tts-menu'),
                ttsQueueList: document.getElementById('tts-queue-list'),
                ttsProgress: document.getElementById('tts-progress'),
                ttsCurrentTitle: document.getElementById('tts-current-title'),
                ttsTime: document.getElementById('tts-time'),
                imageToggle: document.getElementById('image-toggle'),
                timer: document.getElementById('timer'),
                gridLines: document.getElementById('grid-lines')
            };
        },

        bindEvents: function() {
            document.addEventListener('click', (e) => this.handleClick(e));
            
            if (this.elements.ttsProgress) {
                this.elements.ttsProgress.addEventListener('input', (e) => this.seekTTS(e));
            }

            setInterval(() => this.updateTTSProgress(), 200);
            setInterval(() => this.updateTimer(), 1000);

            window.addEventListener('popstate', (e) => this.handlePopState(e));
        },

        handleClick: function(e) {
            if (this.elements.themeMenu && this.elements.themeBtn) {
                if (!this.elements.themeMenu.contains(e.target) && !this.elements.themeBtn.contains(e.target)) {
                    this.elements.themeMenu.classList.remove('open');
                }
            }

            if (this.elements.ttsMenu && this.elements.ttsBtn) {
                if (!this.elements.ttsMenu.contains(e.target) && !this.elements.ttsBtn.contains(e.target)) {
                    this.elements.ttsMenu.classList.remove('open');
                }
            }
        },

        handlePopState: function(e) {
            const state = e.state || history.state;
            if (state) {
                if (state.page === 'article') {
                    this.loadArticle(state.url, state.source);
                } else {
                    this.showHome();
                }
            }
        },

        loadInitialData: function() {
            this.setTheme(this.state.currentTheme);
            this.loadOutlets();
        },

        loadOutlets: function() {
            this.fetchAPI('/api/scrapers')
                .then(outlets => {
                    if (!outlets || !outlets.length) return;
                    
                    if (this.elements.outletSelect) {
                        this.elements.outletSelect.innerHTML = '';
                        outlets.forEach(outlet => {
                            const option = document.createElement('option');
                            option.value = outlet;
                            option.textContent = outlet.toUpperCase();
                            this.elements.outletSelect.appendChild(option);
                        });
                        this.elements.outletSelect.value = this.state.currentSource;
                    }

                    this.loadCapabilities();
                })
                .catch(err => console.error('Failed to load outlets:', err));
        },

        loadCapabilities: function() {
            this.fetchAPI('/api/capabilities?source=' + this.state.currentSource)
                .then(caps => {
                    this.state.capabilities = caps || {};
                    this.loadSections();
                })
                .catch(err => {
                    console.error('Failed to load capabilities:', err);
                    this.state.capabilities = {};
                    this.loadSections();
                });
        },

        loadSections: function() {
            this.fetchAPI('/api/sections?source=' + this.state.currentSource)
                .then(sections => {
                    if (!sections || !sections.length) {
                        if (this.elements.sectionNav) {
                            this.elements.sectionNav.innerHTML = '<div class="error">No sections</div>';
                        }
                        return;
                    }

                    if (this.elements.sectionNav) {
                        const defaultSection = sections.find(s => s.default) || sections[0];
                        this.state.currentSection = defaultSection ? defaultSection.id : 'home';
                        
                        this.elements.sectionNav.innerHTML = sections.map(s => 
                            `<button class="section-btn ${s.id === this.state.currentSection ? 'active' : ''}" data-section="${s.id}">${s.name}</button>`
                        ).join('');

                        this.elements.sectionNav.querySelectorAll('.section-btn').forEach(btn => {
                            btn.addEventListener('click', (e) => this.loadSection(e.target.dataset.section, e.target));
                        });
                    }

                    this.loadNews();
                })
                .catch(err => {
                    console.error('Failed to load sections:', err);
                    if (this.elements.sectionNav) {
                        this.elements.sectionNav.innerHTML = '<div class="error">Error loading sections</div>';
                    }
                });
        },

        loadSection: function(section, btn) {
            this.state.currentSection = section;
            
            if (this.elements.sectionNav) {
                this.elements.sectionNav.querySelectorAll('.section-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            }
            
            this.loadNews();
        },

        loadNews: function() {
            if (!this.elements.newsGrid) return;
            
            this.elements.newsGrid.innerHTML = '<div class="loading">Loading...</div>';

            const url = this.state.currentSection === 'home' 
                ? `/api/news?source=${this.state.currentSource}`
                : `/api/section?section=${this.state.currentSection}&source=${this.state.currentSource}`;

            this.fetchAPI(url)
                .then(news => {
                    this.state.currentNews = news || [];
                    this.renderNews(news || []);
                    
                    if (this.state.capabilities.has_images) {
                        this.fetchMissingImages(news || []);
                    }
                })
                .catch(err => {
                    console.error('Failed to load news:', err);
                    if (this.elements.newsGrid) {
                        this.elements.newsGrid.innerHTML = '<div class="error">Error loading news</div>';
                    }
                });
        },

        renderNews: function(news) {
            if (!this.elements.newsGrid) return;
            
            if (!news || !news.length) {
                this.elements.newsGrid.innerHTML = '<div class="error">No news available</div>';
                return;
            }

            this.elements.newsGrid.innerHTML = news.map((item, idx) => {
                const tags = (item.category || '').split(',').map(t => t.trim()).filter(t => t);
                const tagHtml = tags.length 
                    ? tags.map(t => `<span>${this.escapeHtml(t)}</span>`).join('')
                    : '<span>News</span>';
                
                const imgHtml = item.image && this.state.showImages
                    ? `<img src="${this.escapeHtml(item.image)}" alt="" onerror="this.style.display='none'">`
                    : (this.state.showImages ? '<div class="img-placeholder">No image</div>' : '');
                
                return `<div class="news-card" data-index="${idx}" data-link="${this.escapeHtml(item.link, true)}">
                    ${imgHtml}
                    <div class="news-content">
                        <div class="news-category">${tagHtml}</div>
                        <div class="news-title">${this.escapeHtml(item.title || '')}</div>
                        <div class="news-desc">${this.escapeHtml(item.description || '')}</div>
                    </div>
                    <button class="queue-btn" onclick="event.stopPropagation(); NewsApp.addToQueue('${this.escapeHtml(item.link, true)}', '${this.state.currentSource}', '${this.escapeHtml(item.title, true)}')">+</button>
                </div>`;
            }).join('');

            this.elements.newsGrid.querySelectorAll('.news-card').forEach(card => {
                card.addEventListener('click', (e) => {
                    if (e.target.classList.contains('queue-btn')) return;
                    const idx = card.dataset.index;
                    const item = news[idx];
                    if (item) this.navigateToArticle(item.link, this.state.currentSource);
                });
            });

            if (this.state.showImages) {
                this.elements.newsGrid.querySelectorAll('img').forEach(img => img.style.display = '');
                this.elements.newsGrid.querySelectorAll('.img-placeholder').forEach(p => p.style.display = '');
            }

            this.updateHeader();
        },

        fetchMissingImages: function(news) {
            if (!this.state.capabilities.has_images) return;
            
            const urls = news.filter(n => !n.image).map(n => n.link);
            if (!urls.length) return;

            const params = urls.map(u => 'urls=' + encodeURIComponent(u)).join('&');
            const apiUrl = '/api/images?source=' + this.state.currentSource + '&' + params;
            
            fetch(apiUrl)
                .then(res => res.text())
                .then(text => {
                    if (!text) return;
                    const lines = text.trim().split('\n');
                    
                    lines.forEach(line => {
                        try {
                            const data = JSON.parse(line);
                            if (data.url && data.image) {
                                this.updateCardImage(data.url, data.image);
                            }
                        } catch (e) {}
                    });
                })
                .catch(err => console.error('Error fetching images:', err));
        },
        
        updateCardImage: function(url, image) {
            const cards = this.elements.newsGrid?.querySelectorAll('.news-card');
            if (!cards) return;
            
            const apiPath = url.split('?')[0];
            
            cards.forEach(card => {
                const cardLink = card.getAttribute('data-link') || '';
                if (!cardLink) return;
                
                const apiId = (url.split('/article/')[1] || '').split('/')[0];
                const cardId = (cardLink.split('/article/')[1] || '').split('/')[0];
                
                if (apiId && cardId && apiId === cardId) {
                    const placeholder = card.querySelector('.img-placeholder');
                    if (placeholder) {
                        placeholder.outerHTML = '<img src="' + image + '" alt="" style="width:100%;height:200px;object-fit:cover;background:var(--display-bg);display:' + (this.state.showImages ? '' : 'none') + '" onerror="this.style.display=\'none\'">';
                    }
                }
            });
        },
        
        navigateToArticle: function(url, source) {
            const theme = this.state.currentTheme;
            history.pushState(
                {page: 'article', url: url, theme: theme, source: source},
                '',
                '/article?url=' + encodeURIComponent(url) + '&theme=' + theme + '&source=' + source
            );
            window.location.href = '/article?url=' + encodeURIComponent(url) + '&theme=' + theme + '&source=' + source;
        },

        showHome: function() {
            history.pushState(
                {page: 'home', theme: this.state.currentTheme, source: this.state.currentSource},
                '',
                '/?theme=' + this.state.currentTheme + '&source=' + this.state.currentSource
            );
            window.location.href = '/?theme=' + this.state.currentTheme + '&source=' + this.state.currentSource;
        },

        loadArticle: function(url, source) {
            if (this.elements.mainContainer) {
                this.elements.mainContainer.classList.add('article-view');
                this.elements.mainContainer.innerHTML = '<div class="loading">Loading article...</div>';
            }

            this.fetchAPI('/api/article?url=' + encodeURIComponent(url) + '&source=' + source)
                .then(data => {
                    this.renderArticle(data, url, source);
                })
                .catch(err => {
                    if (this.elements.mainContainer) {
                        this.elements.mainContainer.innerHTML = '<div class="error">Error loading article</div>';
                    }
                });
        },

        renderArticle: function(data, url, source) {
            if (!this.elements.mainContainer || !data) return;

            window.originalUrl = url;
            window.currentSource = source;
            this.state.currentArticleUrl = url;
            this.state.currentArticleTitle = data.title || 'Article';

            const relatedHtml = (data.related_news || []).map(item => 
                `<div class="related-card" onclick="NewsApp.navigateToArticle('${this.escapeHtml(item.link, true)}', '${source}')">
                    ${item.image ? `<img src="${this.escapeHtml(item.image)}" alt="">` : '<div class="related-placeholder">Loading...</div>'}
                    <div class="related-content">
                        <div class="related-title-text">${this.escapeHtml(item.title || '')}</div>
                        <button class="queue-btn" onclick="event.stopPropagation(); NewsApp.addToQueue('${this.escapeHtml(item.link, true)}', '${source}', '')">+</button>
                    </div>
                </div>`
            ).join('');

            this.elements.mainContainer.innerHTML = 
                `<a class="back-btn" onclick="NewsApp.showHome()">← Back to News</a>
                <div class="article-card">
                    ${data.image ? `<img src="${this.escapeHtml(data.image)}" alt="">` : ''}
                    <h1 class="article-title">${this.escapeHtml(data.title || '')}</h1>
                    <div class="summary-box"></div>
                    <div class="article-content">${data.content || ''}</div>
                </div>
                ${relatedHtml ? `<h2 class="related-title">Related News</h2><div class="related-grid">${relatedHtml}</div>` : ''}`;
            
            // Generate summary after a delay
            var self = this;
            setTimeout(function() { self.generateSummary(); }, 500);

            if (!this.state.showImages) {
                this.elements.mainContainer.querySelectorAll('img').forEach(img => img.style.display = 'none');
            }
        },
        
        generateSummary: function() {
            var self = this;
            var summaryBox = this.elements.mainContainer?.querySelector('.summary-box');
            var content = this.elements.mainContainer?.querySelector('.article-content');
            
            if (!summaryBox) {
                console.log('Summary box not found');
                return;
            }
            
            if (!content) {
                summaryBox.innerHTML = '<div style="font-size:10px;color:var(--text-secondary);margin-bottom:8px;">AI Summary</div><div style="font-size:14px;color:#ff4444;">Error: no content found</div>';
                return;
            }
            
            var text = content.textContent || '';
            if (!text) return;
            
            summaryBox.innerHTML = '<div style="font-size:10px;color:var(--text-secondary);margin-bottom:8px;">AI Summary</div><div style="font-size:14px;color:var(--text-secondary);">Loading...</div>';
            
            fetch('/api/summarize?text=' + encodeURIComponent(text.slice(0, 2000)))
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    if (data.summary) {
                        summaryBox.innerHTML = '<div style="font-size:10px;color:var(--text-secondary);margin-bottom:8px;">AI Summary</div><div style="font-size:14px;color:var(--text-primary);line-height:1.5;">' + data.summary + '</div>';
                    } else {
                        summaryBox.innerHTML = '';
                    }
                })
                .catch(function(err) {
                    summaryBox.innerHTML = '';
                });
        },

        changeOutlet: function(outlet) {
            if (!outlet) return;
            
            this.state.currentSource = outlet;
            localStorage.setItem('newsOutlet', outlet);
            
            this.updateHeader();
            this.loadCapabilities();
        },

        updateHeader: function() {
            if (this.elements.headerTitle) {
                this.elements.headerTitle.textContent = (this.state.currentSource || 'NEWS').toUpperCase() + ' NEWS';
            }
            if (this.elements.footer) {
                this.elements.footer.textContent = (this.state.currentSource || '').toUpperCase() + ' News • Themeable';
            }
        },

        setTheme: function(theme) {
            if (!this.config.themes[theme]) theme = this.config.defaultTheme;
            
            this.state.currentTheme = theme;
            localStorage.setItem('newsTheme', theme);
            
            if (this.elements.themeStylesheet) {
                this.elements.themeStylesheet.href = '/static/' + this.config.themes[theme];
            }

            if (this.elements.gridLines) {
                this.elements.gridLines.style.display = theme === 'neon' ? 'block' : 'none';
            }

            document.querySelectorAll('.theme-option').forEach(opt => {
                opt.classList.toggle('active', opt.dataset.theme === theme);
            });

            if (this.elements.themeMenu) {
                this.elements.themeMenu.classList.remove('open');
            }
        },

        toggleThemeMenu: function() {
            if (this.elements.themeMenu) {
                this.elements.themeMenu.classList.toggle('open');
            }
        },

        toggleImages: function() {
            this.state.showImages = !this.state.showImages;
            localStorage.setItem('showImages', this.state.showImages);

            if (this.elements.imageToggle) {
                this.elements.imageToggle.classList.toggle('hidden', !this.state.showImages);
            }

            document.querySelectorAll('img').forEach(img => {
                img.style.display = this.state.showImages ? '' : 'none';
            });
            document.querySelectorAll('.img-placeholder').forEach(p => {
                p.style.display = this.state.showImages ? '' : 'none';
            });
        },

        addToQueue: function(url, source, title) {
            this.state.ttsQueue.push({
                url: url,
                source: source,
                title: title || 'Article',
                status: 'pending'
            });
            
            this.updateQueueDisplay();
            
            if (!this.state.isTTSPlaying && !this.state.isTTSLoading && this.state.ttsQueue.length === 1) {
                this.processNextInQueue();
            }
        },

        processNextInQueue: function() {
            if (this.state.ttsQueue.length === 0 || this.state.isTTSPlaying || this.state.isTTSLoading) return;

            const item = this.state.ttsQueue[0];
            item.status = 'loading';
            this.state.isTTSLoading = true;
            
            if (this.elements.ttsBtn) {
                this.elements.ttsBtn.classList.add('loading');
            }
            
            this.updateQueueDisplay();

            fetch('/api/tts?url=' + encodeURIComponent(item.url) + '&source=' + item.source)
                .then(res => {
                    if (!res.ok) throw new Error('TTS failed');
                    return res.arrayBuffer();
                })
                .then(buf => {
                    this.state.isTTSLoading = false;
                    
                    if (this.elements.ttsBtn) {
                        this.elements.ttsBtn.classList.remove('loading');
                    }

                    if (this.state.ttsAudio) {
                        URL.revokeObjectURL(this.state.ttsAudio.src);
                    }

                    const blob = new Blob([buf], { type: 'audio/wav' });
                    this.state.ttsAudio = new Audio(URL.createObjectURL(blob));

                    this.state.ttsAudio.onended = () => {
                        this.state.isTTSPlaying = false;
                        if (this.elements.ttsBtn) {
                            this.elements.ttsBtn.classList.remove('playing');
                        }
                        item.status = 'done';
                        
                        if (this.state.ttsQueue.length > 1) {
                            this.state.ttsQueue.shift();
                            this.updateQueueDisplay();
                            if (this.state.ttsQueue.length > 0) {
                                this.state.ttsQueue[0].title = 'Now reading: ' + this.state.ttsQueue[0].title;
                                this.updateQueueDisplay();
                                this.processNextInQueue();
                            }
                        } else {
                            this.state.ttsQueue.shift();
                            this.updateQueueDisplay();
                            this.updateTimer();
                        }
                    };

                    this.state.ttsAudio.onerror = () => {
                        this.state.isTTSPlaying = false;
                        if (this.elements.ttsBtn) {
                            this.elements.ttsBtn.classList.remove('playing');
                        }
                        console.error('Audio error');
                        this.state.ttsQueue.shift();
                        this.updateQueueDisplay();
                        if (this.state.ttsQueue.length > 0) this.processNextInQueue();
                    };

                    this.state.ttsAudio.play();
                    this.state.isTTSPlaying = true;
                    
                    if (this.elements.ttsBtn) {
                        this.elements.ttsBtn.classList.add('playing');
                    }
                    
                    item.status = 'playing';
                    this.state.currentArticleTitle = item.title;
                    this.updateQueueDisplay();
                    this.updateTimer();
                })
                .catch(err => {
                    console.error('TTS error:', err);
                    this.state.isTTSLoading = false;
                    this.state.isTTSPlaying = false;
                    
                    if (this.elements.ttsBtn) {
                        this.elements.ttsBtn.classList.remove('playing');
                    }
                    
                    this.state.ttsQueue.shift();
                    this.updateQueueDisplay();
                    if (this.state.ttsQueue.length > 0) this.processNextInQueue();
                });
        },

        playOrPauseTTS: function() {
            if (this.state.isTTSPlaying) {
                this.pauseTTS();
            } else if (this.state.isTTSLoading) {
                return;
            } else if (this.state.ttsQueue.length > 0) {
                this.processNextInQueue();
            } else if (this.state.currentArticleUrl) {
                this.addToQueue(this.state.currentArticleUrl, window.currentSource || this.state.currentSource, this.state.currentArticleTitle);
            }
        },

        pauseTTS: function() {
            if (this.state.ttsAudio) {
                this.state.ttsAudio.pause();
            }
            this.state.isTTSPlaying = false;
            
            if (this.elements.ttsBtn) {
                this.elements.ttsBtn.classList.remove('playing');
            }
            
            if (this.elements.ttsCurrentTitle) {
                this.elements.ttsCurrentTitle.textContent = 'Paused';
            }
        },

        updateQueueDisplay: function() {
            if (!this.elements.ttsQueueList) return;

            if (this.state.ttsQueue.length === 0) {
                this.elements.ttsQueueList.innerHTML = '<div class="tts-empty">No items in queue</div>';
                return;
            }

            this.elements.ttsQueueList.innerHTML = this.state.ttsQueue.map((item, i) => {
                let statusIcon = '⏸';
                let statusClass = '';
                
                if (item.status === 'playing') {
                    statusIcon = '▶';
                    statusClass = 'playing';
                } else if (item.status === 'done') {
                    statusIcon = '✓';
                    statusClass = 'done';
                } else if (item.status === 'loading') {
                    statusIcon = '⏳';
                }
                
                return `<div class="tts-queue-item ${statusClass}" onclick="NewsApp.playQueueItem(${i})">
                    <span class="tts-queue-status">${statusIcon}</span>
                    <span class="tts-queue-title" title="${this.escapeHtml(item.title)}">${this.escapeHtml(item.title)}</span>
                    <button class="tts-queue-remove" onclick="event.stopPropagation(); NewsApp.removeFromQueue(${i})">×</button>
                </div>`;
            }).join('');
        },

        playQueueItem: function(index) {
            const item = this.state.ttsQueue[index];
            if (!item) return;

            if (index === 0 && !this.state.isTTSPlaying && !this.state.isTTSLoading) {
                this.processNextInQueue();
            }
            
            if (this.elements.ttsMenu) {
                this.elements.ttsMenu.classList.remove('open');
            }
        },

        removeFromQueue: function(index) {
            if (index === 0 && (this.state.isTTSPlaying || this.state.isTTSLoading)) {
                if (this.state.ttsAudio) {
                    this.state.ttsAudio.pause();
                    this.state.ttsAudio = null;
                }
                this.state.isTTSPlaying = false;
                this.state.isTTSLoading = false;
            }
            
            this.state.ttsQueue.splice(index, 1);
            this.updateQueueDisplay();
            this.updateTimer();
        },

        updateTimer: function() {
            if (!this.elements.timer) return;
            
            if (this.state.ttsQueue.length > 0) {
                const status = this.state.isTTSPlaying ? '▶' : this.state.isTTSLoading ? '⏳' : '⏸';
                this.elements.timer.textContent = 'Q:' + this.state.ttsQueue.length + ' ' + status;
                this.elements.timer.classList.add('active');
            } else if (this.state.ttsAudio && this.state.ttsAudio.duration) {
                const remaining = Math.max(0, Math.ceil(this.state.ttsAudio.duration - this.state.ttsAudio.currentTime));
                this.elements.timer.textContent = 'TTS: ' + remaining + 's';
                this.elements.timer.classList.add('active');
            } else {
                this.elements.timer.textContent = '';
                this.elements.timer.classList.remove('active');
            }
        },

        updateTTSProgress: function() {
            if (!this.elements.ttsProgress || !this.state.ttsAudio || !this.state.ttsAudio.duration) return;

            const percent = (this.state.ttsAudio.currentTime / this.state.ttsAudio.duration) * 100;
            this.elements.ttsProgress.value = percent;

            const formatTime = (s) => {
                const mins = Math.floor(s / 60);
                const secs = Math.floor(s % 60);
                return mins + ':' + (secs < 10 ? '0' : '') + secs;
            };

            if (this.elements.ttsCurrentTitle) {
                this.elements.ttsCurrentTitle.textContent = this.state.currentArticleTitle || 'Playing';
            }
            
            if (this.elements.ttsTime) {
                this.elements.ttsTime.textContent = formatTime(this.state.ttsAudio.currentTime) + ' / ' + formatTime(this.state.ttsAudio.duration);
            }
        },

        seekTTS: function(e) {
            if (this.state.ttsAudio && this.elements.ttsProgress) {
                const percent = parseFloat(this.elements.ttsProgress.value);
                this.state.ttsAudio.currentTime = (percent / 100) * this.state.ttsAudio.duration;
            }
        },

fetchAPI: async function(url, options = {}) {
            const controller = new AbortController();
            const timeout = setTimeout(() => controller.abort(), this.config.apiTimeout);
            const responseType = options.responseType;
            const fetchOptions = { signal: controller.signal };

            try {
                const response = await fetch(url, fetchOptions);

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                if (responseType === 'arraybuffer') {
                    return await response.arrayBuffer();
                }

                return await response.json();
            } finally {
                clearTimeout(timeout);
            }
        },

        escapeHtml: function(str, forAttr = false) {
            if (!str) return '';
            const div = document.createElement('div');
            div.textContent = str;
            let result = div.innerHTML;
            if (forAttr) {
                result = result.replace(/'/g, "\\'").replace(/"/g, '&quot;');
            }
            return result;
        }
    };

    window.NewsApp = NewsApp;

    document.addEventListener('DOMContentLoaded', () => {
        const params = new URLSearchParams(window.location.search);
        const url = params.get('url');
        const source = params.get('source') || 'bbc';
        const theme = params.get('theme') || 'aurora';
        
        NewsApp.state.currentSource = source;
        NewsApp.state.currentTheme = theme;
        
        if (url) {
            NewsApp.loadArticle(url, source);
        } else {
            history.replaceState(
                {page: 'home', theme: theme, source: source},
                '',
                '/?theme=' + theme + '&source=' + source
            );
            NewsApp.init();
        }
    });

    window.changeOutlet = function(value) {
        NewsApp.changeOutlet(value);
    };

    window.loadNews = function() {
        NewsApp.loadNews();
    };

    window.setTheme = function(theme) {
        NewsApp.setTheme(theme);
    };

    window.toggleThemeMenu = function() {
        NewsApp.toggleThemeMenu();
    };

    window.toggleImages = function() {
        NewsApp.toggleImages();
    };

    window.playOrPauseTTS = function() {
        NewsApp.playOrPauseTTS();
    };

    window.navigateToArticle = function(url, source) {
        NewsApp.navigateToArticle(url, source);
    };

    window.goBack = function() {
        NewsApp.showHome();
    };

    window.loadSection = function(section, btn) {
        NewsApp.loadSection(section, btn);
    };

})();