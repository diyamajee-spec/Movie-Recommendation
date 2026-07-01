window.handlePosterError = function(img) {
    img.onerror = null; // Prevent infinite loops
    
    // Attempt to extract title and year from containing card elements
    const card = img.closest('.movie-card, .trending-movie-card, .skeleton-card');
    let title = card ? card.getAttribute('data-title') : '';
    let year = card ? card.getAttribute('data-year') : '';
    
    if (!title && img.id === 'modalPoster') {
        // Fallback for modal details image
        const titleEl = document.getElementById('modalTitle');
        const yearEl = document.getElementById('modalYear');
        if (titleEl) title = titleEl.textContent;
        if (yearEl) year = yearEl.textContent;
    }
    
    if (title && title.trim()) {
        fetch(`/api/poster?title=${encodeURIComponent(title.trim())}&year=${encodeURIComponent(year || '')}`)
            .then(res => res.json())
            .then(data => {
                if (data.poster) {
                    img.src = data.poster;
                    // If this was a card poster, also update any identical cards in the page
                    if (card) {
                        const sameCards = document.querySelectorAll(`.movie-card[data-title="${title.replace(/"/g, '\\"')}"] img`);
                        sameCards.forEach(sImg => {
                            if (sImg !== img) {
                                sImg.onerror = null;
                                sImg.src = data.poster;
                            }
                        });
                    }
                } else {
                    img.src = 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&q=80&w=300';
                }
            })
            .catch(() => {
                img.src = 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&q=80&w=300';
            });
    } else {
        img.src = 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&q=80&w=300';
    }
};

document.addEventListener('DOMContentLoaded', function() {
    
    // =========================================================================
    // 1. GLOBAL UI HANDLERS (Toast, Back-to-Top, Loading)
    // =========================================================================
    
    // Global Toast helper
    const toastElement = document.getElementById('liveToast');
    let bsToast = null;
    if (toastElement) {
        bsToast = new bootstrap.Toast(toastElement, { delay: 3000 });
    }
    
    window.showNotification = function(message, type = 'success') {
        const toastMessage = document.getElementById('toast-message');
        const toastIcon = document.getElementById('toast-icon');
        
        if (toastMessage && toastIcon && bsToast) {
            toastMessage.textContent = message;
            
            // Set icon
            toastIcon.className = 'fa-solid me-2 fs-5 ';
            if (type === 'success') {
                toastIcon.className += 'fa-circle-check text-success';
            } else if (type === 'error') {
                toastIcon.className += 'fa-circle-exclamation text-danger';
            } else {
                toastIcon.className += 'fa-circle-info text-info';
            }
            
            bsToast.show();
        }
    };

    // Back to top button
    const backToTopBtn = document.getElementById('back-to-top');
    if (backToTopBtn) {
        window.addEventListener('scroll', function() {
            if (window.scrollY > 400) {
                backToTopBtn.classList.add('show');
            } else {
                backToTopBtn.classList.remove('show');
            }
        });
        
        backToTopBtn.addEventListener('click', function() {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }

    // Loading overlay trigger on form submissions
    const formsToLoad = document.querySelectorAll('.trigger-loading');
    const loadingOverlay = document.getElementById('loading-overlay');
    if (loadingOverlay) {
        formsToLoad.forEach(form => {
            form.addEventListener('submit', function() {
                if (form.checkValidity()) {
                    loadingOverlay.classList.add('show');
                }
            });
        });
    }

    // Quick Genre Channel buttons on Home
    const genreButtons = document.querySelectorAll('.genre-channel-btn');
    genreButtons.forEach(btn => {
        btn.addEventListener('click', function() {
            // Fill wizard fields and auto submit
            const wizardGenre = document.getElementById('genre');
            const wizardAge = document.getElementById('age_group');
            const wizardLang = document.getElementById('language');
            const wizardForm = document.querySelector('#wizard form');
            
            if (wizardGenre && wizardAge && wizardLang && wizardForm) {
                wizardGenre.value = this.getAttribute('data-genre');
                // Select default suitable age group & language if not set
                if (!wizardAge.value) wizardAge.value = 'Adult';
                if (!wizardLang.value) wizardLang.value = 'en';
                
                // Show loading overlay and submit
                if (loadingOverlay) loadingOverlay.classList.add('show');
                wizardForm.submit();
            }
        });
    });

    // =========================================================================
    // 2. AUTOCOMPLETE LIVE SEARCH
    // =========================================================================
    
    const searchContainers = document.querySelectorAll('.nav-search-container, .search-form-container');
    
    searchContainers.forEach(container => {
        const searchInput = container.querySelector('.nav-search-input');
        const dropdown = container.querySelector('.autocomplete-dropdown');
        const clearBtn = container.querySelector('.search-clear-btn');
        const suggestionsList = container.querySelector('.suggestions-list');
        const recentSearchesList = container.querySelector('.recent-searches-list');
        const clearRecentBtn = container.querySelector('.clear-recent-btn');
        
        if (!searchInput || !dropdown) return;
        
        let debounceTimer;
        
        // Load recent searches from localStorage
        function getRecentSearches() {
            try {
                return JSON.parse(localStorage.getItem('cinerec_recent_searches')) || [];
            } catch (e) {
                return [];
            }
        }
        
        function saveRecentSearch(query) {
            if (!query || !query.trim()) return;
            let searches = getRecentSearches();
            searches = searches.filter(s => s.toLowerCase() !== query.toLowerCase());
            searches.unshift(query.trim());
            localStorage.setItem('cinerec_recent_searches', JSON.stringify(searches.slice(0, 5)));
        }
        
        function populateRecentSearches() {
            if (!recentSearchesList) return;
            const searches = getRecentSearches();
            recentSearchesList.innerHTML = '';
            
            if (searches.length === 0) {
                recentSearchesList.innerHTML = '<div class="dropdown-item text-muted small py-1 px-3">No recent searches</div>';
                return;
            }
            
            searches.forEach(search => {
                const item = document.createElement('a');
                item.className = 'dropdown-item d-flex justify-content-between align-items-center py-1 px-3';
                item.href = `/search?query=${encodeURIComponent(search)}`;
                item.innerHTML = `
                    <span><i class="fa-solid fa-clock text-muted me-2 small"></i>${escapeHTML(search)}</span>
                    <i class="fa-solid fa-arrow-turn-up text-muted small" style="transform: rotate(90deg);"></i>
                `;
                item.addEventListener('click', function(e) {
                    if (loadingOverlay) loadingOverlay.classList.add('show');
                });
                recentSearchesList.appendChild(item);
            });
        }
        
        // Clear recent searches
        if (clearRecentBtn) {
            clearRecentBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                localStorage.removeItem('cinerec_recent_searches');
                populateRecentSearches();
                window.showNotification("Recent searches cleared", "info");
            });
        }
        
        // Show/hide autocomplete drop
        searchInput.addEventListener('focus', function() {
            populateRecentSearches();
            dropdown.classList.add('show');
        });
        
        document.addEventListener('click', function(e) {
            if (!container.contains(e.target)) {
                dropdown.classList.remove('show');
            }
        });
        
        // Clear button toggle
        if (clearBtn) {
            clearBtn.addEventListener('click', function() {
                searchInput.value = '';
                clearBtn.style.display = 'none';
                suggestionsList.innerHTML = '';
                searchInput.focus();
            });
        }
        
        // Input keyup listener with debounce
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            
            if (clearBtn) {
                clearBtn.style.display = query.length > 0 ? 'block' : 'none';
            }
            
            clearTimeout(debounceTimer);
            if (query.length < 2) {
                suggestionsList.innerHTML = '';
                return;
            }
            
            // Show autocomplete spinner
            suggestionsList.innerHTML = '<div class="text-center py-2"><div class="spinner-border spinner-border-sm text-danger" role="status"></div></div>';
            
            debounceTimer = setTimeout(function() {
                fetch(`/api/search?query=${encodeURIComponent(query)}`)
                    .then(res => res.json())
                    .then(data => {
                        suggestionsList.innerHTML = '';
                        if (!data || data.length === 0) {
                            suggestionsList.innerHTML = '<div class="dropdown-item text-muted py-2 px-3"><i class="fa-solid fa-face-frown me-2"></i>No matches found</div>';
                            return;
                        }
                        
                        data.forEach(movie => {
                            const item = document.createElement('div');
                            item.className = 'dropdown-item d-flex align-items-center py-2 px-3 cursor-pointer border-bottom border-secondary-subtle';
                            item.style.borderBottomStyle = 'dashed';
                            
                            const posterSrc = movie.poster && movie.poster !== 'nan' ? movie.poster : '';
                            const posterHTML = posterSrc 
                                ? `<img src="${posterSrc}" style="width: 32px; height: 48px; object-fit: cover; border-radius: 4px;" class="me-2 shadow-sm" onerror="this.onerror=null; this.outerHTML='<div class=&quot;autocomplete-fallback me-2&quot;><i class=&quot;fa-solid fa-film&quot;></i></div>';">`
                                : `<div class="autocomplete-fallback me-2"><i class="fa-solid fa-film"></i></div>`;
                                
                            item.innerHTML = `
                                ${posterHTML}
                                <div class="flex-grow-1 min-width-0">
                                    <div class="text-white text-truncate font-weight-semibold" style="font-size: 0.95rem;">${escapeHTML(movie.title)}</div>
                                    <div class="text-muted small text-truncate">${movie.year} &middot; ${escapeHTML(movie.genres)} &middot; ★${movie.rating.toFixed(1)}</div>
                                </div>
                            `;
                            
                            item.addEventListener('click', function() {
                                // Save to recent search history
                                saveRecentSearch(movie.title);
                                // Open detailed modal immediately using movie data
                                openDetailsModal(movie);
                                dropdown.classList.remove('show');
                            });
                            
                            suggestionsList.appendChild(item);
                        });
                    })
                    .catch(err => {
                        console.error("Autocomplete error:", err);
                        suggestionsList.innerHTML = '<div class="dropdown-item text-danger py-2 px-3">Failed to load suggestions</div>';
                    });
            }, 250);
        });
        
        // Add query to recent searches on form submission
        const form = container.querySelector('form');
        if (form) {
            form.addEventListener('submit', function() {
                saveRecentSearch(searchInput.value);
            });
        }
    });

    // =========================================================================
    // 3. MOVIE DETAILS MODAL & MOVIE ACTIONS (Favorites, Share)
    // =========================================================================
    
    const detailsModal = document.getElementById('movieDetailsModal');
    let bsDetailsModal = null;
    if (detailsModal) {
        bsDetailsModal = new bootstrap.Modal(detailsModal);
    }
    
    // Check if a movie is favorited
    function getFavorites() {
        try {
            return JSON.parse(localStorage.getItem('cinerec_favorites')) || [];
        } catch (e) {
            return [];
        }
    }
    
    function toggleFavorite(movieTitle) {
        let favs = getFavorites();
        let isAdded = false;
        if (favs.includes(movieTitle)) {
            favs = favs.filter(t => t !== movieTitle);
        } else {
            favs.push(movieTitle);
            isAdded = true;
        }
        localStorage.setItem('cinerec_favorites', JSON.stringify(favs));
        return isAdded;
    }
    
    function updateFavoriteButtonUI(btn, movieTitle) {
        if (!btn) return;
        const favs = getFavorites();
        const icon = btn.querySelector('i');
        
        if (favs.includes(movieTitle)) {
            icon.className = 'fa-solid fa-heart text-danger me-1';
            btn.innerHTML = `<i class="fa-solid fa-heart text-danger me-1"></i>Favorited`;
            btn.classList.add('btn-danger');
            btn.classList.remove('btn-outline-light');
        } else {
            icon.className = 'fa-regular fa-heart me-1';
            btn.innerHTML = `<i class="fa-regular fa-heart me-1"></i>Favorite`;
            btn.classList.remove('btn-danger');
            btn.classList.add('btn-outline-light');
        }
    }

    // Opens details modal dynamically
    window.openDetailsModal = function(movie) {
        const modalTitle = document.getElementById('modalTitle');
        const modalBackdrop = document.getElementById('modalBackdrop');
        const modalPoster = document.getElementById('modalPoster');
        const modalAgeBadge = document.getElementById('modalAgeBadge');
        const modalLanguage = document.getElementById('modalLanguage');
        const modalRuntime = document.getElementById('modalRuntime');
        const modalRating = document.getElementById('modalRating');
        const modalYear = document.getElementById('modalYear');
        const modalOverview = document.getElementById('modalOverview');
        const modalDirector = document.getElementById('modalDirector');
        const modalCast = document.getElementById('modalCast');
        const favBtn = document.getElementById('modalFavoriteBtn');
        const shareBtn = document.getElementById('modalShareBtn');
        const similarSection = document.getElementById('modalSimilarSection');
        const similarMoviesList = document.getElementById('modalSimilarMoviesList');

        if (!modalTitle || !bsDetailsModal) return;

        // Set title, overview, rating, year safely
        modalTitle.textContent = movie.title || "Unknown Title";
        modalOverview.textContent = movie.overview || "No overview available for this movie plot.";
        modalRating.textContent = movie.rating ? parseFloat(movie.rating).toFixed(1) : '5.0';
        modalYear.textContent = movie.year || '2000';
        
        // Director & Cast safely
        modalDirector.textContent = movie.director || "Unknown Director";
        modalCast.textContent = movie.cast || "Unknown Cast";
        
        // Runtime safely
        modalRuntime.textContent = movie.runtime ? `${movie.runtime} mins` : '120 mins';
        
        // Language mapping safely
        const langStr = movie.language ? movie.language.toString().trim() : 'en';
        const langMap = { "en": "EN", "hi": "HI", "ta": "TA", "te": "TE" };
        modalLanguage.textContent = langMap[langStr.toLowerCase()] || langStr.toUpperCase();
        
        // Age suitability badge safely
        const genresStr = movie.genres ? movie.genres.toString().trim() : '';
        const suitableGenreList = genresStr ? genresStr.split(',').map(g => g.trim()) : [];
        let ageLabel = "Adult (18+)";
        let ageColor = "bg-danger";
        
        // Kids logic check: Only Animation, Family, Adventure, Fantasy, Comedy
        const allowedKids = new Set(['Animation', 'Family', 'Adventure', 'Fantasy', 'Comedy']);
        const allowedTeen = new Set(['Adventure', 'Comedy', 'Fantasy', 'Action', 'Science Fiction', 'Drama', 'Animation', 'Family']);
        
        const allKids = suitableGenreList.length > 0 && suitableGenreList.every(g => allowedKids.has(g));
        const allTeen = suitableGenreList.length > 0 && suitableGenreList.every(g => allowedTeen.has(g));
        
        if (allKids) {
            ageLabel = "Kids (G)";
            ageColor = "bg-success";
        } else if (allTeen) {
            ageLabel = "Teen (PG-13)";
            ageColor = "bg-warning text-dark";
        }
        
        modalAgeBadge.textContent = ageLabel;
        modalAgeBadge.className = `badge ${ageColor}`;
        
        // Poster URL setup
        if (movie.poster && movie.poster !== 'nan' && movie.poster !== '') {
            modalPoster.src = movie.poster;
        } else {
            modalPoster.src = 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&q=80&w=300';
        }
        
        // Backdrop Image setup
        if (movie.backdrop && movie.backdrop !== '' && movie.backdrop !== 'nan') {
            modalBackdrop.style.backgroundImage = `url('${movie.backdrop}')`;
        } else if (movie.poster && movie.poster !== 'nan' && movie.poster !== '') {
            modalBackdrop.style.backgroundImage = `url('${movie.poster}')`;
        } else {
            modalBackdrop.style.backgroundImage = '';
        }
        
        // Setup Favorite button state
        updateFavoriteButtonUI(favBtn, movie.title);
        
        // Setup Favorite click
        favBtn.onclick = function() {
            const added = toggleFavorite(movie.title);
            updateFavoriteButtonUI(favBtn, movie.title);
            
            // Sync any existing recommendation list cards
            const matchCards = document.querySelectorAll(`.movie-card[data-title="${escapeAttr(movie.title)}"]`);
            matchCards.forEach(c => {
                const cFavBtn = c.querySelector('.btn-card-favorite i');
                if (cFavBtn) {
                    cFavBtn.className = added ? 'fa-solid fa-heart text-danger' : 'fa-regular fa-heart';
                }
            });
            
            window.showNotification(added ? `Added "${movie.title}" to favorites` : `Removed "${movie.title}" from favorites`, "success");
        };
        
        // Setup Share click
        shareBtn.onclick = function() {
            const shareUrl = `${window.location.origin}/search?query=${encodeURIComponent(movie.title)}`;
            navigator.clipboard.writeText(shareUrl)
                .then(() => {
                    window.showNotification("Movie link copied to clipboard", "info");
                })
                .catch(err => {
                    console.error("Clipboard copy failed:", err);
                    window.showNotification("Failed to copy link", "error");
                });
        };
        
        // Load similar movies dynamically
        if (similarSection && similarMoviesList) {
            similarMoviesList.innerHTML = '<div class="w-100 text-center py-3"><div class="spinner-border text-danger" role="status"></div></div>';
            
            // Detect age suitability filter (Kids, Teen, Adult)
            let ageGroupParam = 'Adult';
            if (ageLabel.startsWith("Kids")) ageGroupParam = 'Kids';
            else if (ageLabel.startsWith("Teen")) ageGroupParam = 'Teen';
            
            fetch(`/api/similar?title=${encodeURIComponent(movie.title)}&age_group=${ageGroupParam}`)
                .then(res => res.json())
                .then(similarList => {
                    similarMoviesList.innerHTML = '';
                    if (!similarList || similarList.length === 0) {
                        similarSection.style.display = 'none';
                        return;
                    }
                    
                    similarSection.style.display = 'block';
                    // Show top 4 similar movies
                    similarList.slice(0, 4).forEach(simMovie => {
                        const col = document.createElement('div');
                        col.className = 'col';
                        
                        const posterSrc = simMovie.poster && simMovie.poster !== 'nan' && simMovie.poster !== '' 
                            ? simMovie.poster 
                            : 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&q=80&w=150';
                            
                        col.innerHTML = `
                            <div class="movie-card sim-card h-100 cursor-pointer shadow-sm overflow-hidden" style="border-radius: 8px; background-color: #1f2937;">
                                <div class="position-relative aspect-ratio-container" style="aspect-ratio: 2/3; overflow: hidden; background-color: #000;" data-title="${escapeAttr(simMovie.title)}" data-year="${simMovie.year}">
                                    <img src="${posterSrc}" class="w-100 h-100" style="object-fit: cover; transition: transform 0.3s;" onerror="handlePosterError(this);">
                                </div>
                                <div class="p-2">
                                    <div class="text-white text-truncate font-weight-bold" style="font-size: 0.85rem;" title="${escapeAttr(simMovie.title)}">${escapeHTML(simMovie.title)}</div>
                                    <div class="text-muted d-flex justify-content-between mt-1" style="font-size: 0.75rem;">
                                        <span>${simMovie.year}</span>
                                        <span><i class="fa-solid fa-star text-warning me-1"></i>${simMovie.rating.toFixed(1)}</span>
                                    </div>
                                </div>
                            </div>
                        `;
                        
                        col.querySelector('.sim-card').addEventListener('click', function() {
                            openDetailsModal(simMovie);
                        });
                        
                        similarMoviesList.appendChild(col);
                    });
                })
                .catch(err => {
                    console.error("Similar movies load error:", err);
                    similarSection.style.display = 'none';
                });
        }
        
        bsDetailsModal.show();
    };

    // Attach details modal triggers to homepage trending cards
    const trendingCards = document.querySelectorAll('.trending-movie-card');
    trendingCards.forEach(card => {
        card.addEventListener('click', function() {
            const movieData = {
                title: this.getAttribute('data-title'),
                year: parseInt(this.getAttribute('data-year') || 0),
                rating: parseFloat(this.getAttribute('data-rating') || 0),
                genres: this.getAttribute('data-genres'),
                language: this.getAttribute('data-language'),
                runtime: parseInt(this.getAttribute('data-runtime') || 120),
                age: this.getAttribute('data-age'),
                director: this.getAttribute('data-director'),
                cast: this.getAttribute('data-cast'),
                overview: this.getAttribute('data-overview'),
                poster: this.getAttribute('data-poster'),
                backdrop: this.getAttribute('data-backdrop')
            };
            openDetailsModal(movieData);
        });
    });

    // =========================================================================
    // 4. RECOMMENDATION PAGE LIVE FILTERING & PAGINATION
    // =========================================================================
    
    const moviesJSONScript = document.getElementById('movies-data-json');
    if (moviesJSONScript) {
        let allMovies = [];
        try {
            const rawMovies = JSON.parse(moviesJSONScript.textContent) || [];
            allMovies = rawMovies.map(movie => ({
                title: movie['Movie Title'] || movie.title || "Unknown Title",
                genres: movie['Genres'] || movie.genres || "",
                overview: movie['Overview'] || movie.overview || "No overview available.",
                language: movie['Language'] || movie.language || "en",
                year: parseInt(movie['Release Year'] || movie.year || 2000),
                rating: parseFloat(movie['Vote Average'] || movie.rating || 5.0),
                poster: movie['Poster URL'] || movie.poster || "",
                popularity: parseFloat(movie['Popularity'] || movie.popularity || 10.0),
                score: parseFloat(movie['Recommendation Score'] || movie.score || 100),
                runtime: parseInt(movie['Runtime'] || movie.runtime || 120),
                director: movie['Director'] || movie.director || "Unknown Director",
                cast: movie['Cast'] || movie.cast || "Unknown Cast",
                backdrop: movie['Backdrop URL'] || movie.backdrop || ""
            }));
        } catch (e) {
            console.error("Failed to parse recommendation movies:", e);
        }
        
        // Element references
        const ratingSlider = document.getElementById('ratingFilter');
        const yearSlider = document.getElementById('yearFilter');
        const searchFilterInput = document.getElementById('filterSearch');
        const sortBySelect = document.getElementById('sortBySelect');
        const sortOrderSwitch = document.getElementById('sortOrderSwitch');
        const sortOrderLabel = document.getElementById('sortOrderLabel');
        
        const ratingValue = document.getElementById('ratingValue');
        const yearValue = document.getElementById('yearValue');
        
        const moviesContainer = document.getElementById('movies-render-container');
        const skeletonContainer = document.getElementById('movies-skeleton-container');
        const noResultsMsg = document.getElementById('no-filter-results');
        
        const paginationNav = document.querySelector('#pagination-nav .pagination');
        const filterChipsList = document.getElementById('filter-chips-list');
        const filterChipsContainer = document.getElementById('filter-chips-container');
        const clearAllFiltersBtn = document.getElementById('btn-clear-all-filters');
        const resetFiltersCTA = document.getElementById('btn-reset-filters-cta');
        
        const btnGridView = document.getElementById('btn-grid-view');
        const btnListView = document.getElementById('btn-list-view');
        const genreListWrapper = document.querySelector('.filter-genre-list');

        // State variables
        let currentLayout = 'grid'; // 'grid' or 'list'
        let selectedGenres = new Set();
        let currentPage = 1;
        const itemsPerPage = 9;

        // Build list of unique genres from returned recommendations list
        function getUniqueGenres() {
            const genresSet = new Set();
            allMovies.forEach(movie => {
                movie.genres.split(',').forEach(g => {
                    const cleanG = g.trim();
                    if (cleanG) genresSet.add(cleanG);
                });
            });
            return Array.from(genresSet).sort();
        }

        function populateGenreSidebar() {
            if (!genreListWrapper) return;
            genreListWrapper.innerHTML = '';
            
            const genres = getUniqueGenres();
            if (genres.length === 0) {
                genreListWrapper.innerHTML = '<div class="text-muted small">No genres available</div>';
                return;
            }
            
            genres.forEach(genre => {
                const div = document.createElement('div');
                div.className = 'form-check mb-1';
                div.innerHTML = `
                    <input class="form-check-input filter-genre-checkbox" type="checkbox" value="${escapeAttr(genre)}" id="genreCheckbox-${escapeAttr(genre)}">
                    <label class="form-check-label text-muted small cursor-pointer" for="genreCheckbox-${escapeAttr(genre)}">
                        ${escapeHTML(genre)}
                    </label>
                `;
                
                div.querySelector('input').addEventListener('change', function() {
                    if (this.checked) {
                        selectedGenres.add(this.value);
                    } else {
                        selectedGenres.delete(this.value);
                    }
                    currentPage = 1;
                    triggerFilterRender();
                });
                
                genreListWrapper.appendChild(div);
            });
        }

        // Toggle Grid vs List View
        if (btnGridView && btnListView) {
            btnGridView.addEventListener('click', function() {
                if (currentLayout === 'grid') return;
                currentLayout = 'grid';
                this.classList.add('active');
                btnListView.classList.remove('active');
                triggerFilterRender();
            });
            
            btnListView.addEventListener('click', function() {
                if (currentLayout === 'list') return;
                currentLayout = 'list';
                this.classList.add('active');
                btnGridView.classList.remove('active');
                triggerFilterRender();
            });
        }

        // Debounce filter render to make search and sliders smooth
        let filterTimeout;
        function triggerFilterRender() {
            if (moviesContainer) {
                moviesContainer.classList.add('d-none');
            }
            if (skeletonContainer) {
                skeletonContainer.classList.remove('d-none');
            }
            if (paginationNav) {
                paginationNav.parentElement.classList.add('d-none');
            }
            
            clearTimeout(filterTimeout);
            filterTimeout = setTimeout(() => {
                if (skeletonContainer) {
                    skeletonContainer.classList.add('d-none');
                }
                if (moviesContainer) {
                    moviesContainer.classList.remove('d-none');
                }
                applyFiltersAndRender();
            }, 300);
        }

        // Apply filters, sorts, and pagination
        function applyFiltersAndRender() {
            if (!moviesContainer) return;
            
            const minRating = parseFloat(ratingSlider ? ratingSlider.value : 0);
            const minYear = parseInt(yearSlider ? yearSlider.value : 1900);
            const searchQuery = searchFilterInput ? searchFilterInput.value.trim().toLowerCase() : '';
            const sortBy = sortBySelect ? sortBySelect.value : 'score';
            const sortDesc = sortOrderSwitch ? sortOrderSwitch.checked : true;
            
            // 1. Filter movies
            let filtered = allMovies.filter(movie => {
                // Match search query
                if (searchQuery && !movie.title.toLowerCase().includes(searchQuery)) return false;
                
                // Match rating
                if (movie.rating < minRating) return false;
                
                // Match release year
                if (movie.year < minYear) return false;
                
                // Match genres (must match all selected genres)
                if (selectedGenres.size > 0) {
                    const movieGenres = movie.genres.split(',').map(g => g.trim());
                    for (let g of selectedGenres) {
                        if (!movieGenres.includes(g)) return false;
                    }
                }
                
                return true;
            });
            
            // 2. Sort movies
            filtered.sort((a, b) => {
                let valA = a[sortBy];
                let valB = b[sortBy];
                
                if (typeof valA === 'string') {
                    return sortDesc ? valB.localeCompare(valA) : valA.localeCompare(valB);
                } else {
                    return sortDesc ? valB - valA : valA - valB;
                }
            });
            
            // 3. Update filter labels & active filter chips
            if (ratingValue) ratingValue.textContent = minRating.toFixed(1);
            if (yearValue) yearValue.textContent = minYear;
            if (sortOrderLabel) sortOrderLabel.textContent = sortDesc ? "Descending" : "Ascending";
            
            renderFilterChips(minRating, minYear, searchQuery);

            // 4. Render Movies list / grid
            moviesContainer.innerHTML = '';
            
            if (filtered.length === 0) {
                if (noResultsMsg) noResultsMsg.classList.remove('d-none');
                if (paginationNav) paginationNav.parentElement.classList.add('d-none');
                return;
            }
            
            if (noResultsMsg) noResultsMsg.classList.add('d-none');
            if (paginationNav) paginationNav.parentElement.classList.remove('d-none');

            // Paginate results
            const totalItems = filtered.length;
            const totalPages = Math.ceil(totalItems / itemsPerPage);
            
            if (currentPage > totalPages) currentPage = 1;
            
            const startIndex = (currentPage - 1) * itemsPerPage;
            const paginatedItems = filtered.slice(startIndex, startIndex + itemsPerPage);
            
            // Set grid structure classes
            if (currentLayout === 'grid') {
                moviesContainer.className = "row row-cols-1 row-cols-md-2 row-cols-xxl-3 g-4";
            } else {
                moviesContainer.className = "row row-cols-1 g-4";
            }

            // Render each card
            paginatedItems.forEach(movie => {
                const col = document.createElement('div');
                col.className = 'col filterable-movie-card';
                
                // Construct genres tags HTML
                const genreTags = movie.genres.split(',').map(g => `<span class="badge bg-secondary-subtle text-white me-1 mb-1" style="font-size:0.7rem; font-weight: 500;">${escapeHTML(g.trim())}</span>`).join('');
                
                const posterSrc = movie.poster && movie.poster !== 'nan' && movie.poster !== '' 
                    ? movie.poster 
                    : 'https://images.unsplash.com/photo-1536440136628-849c177e76a1?auto=format&fit=crop&q=80&w=300';
                
                const favs = getFavorites();
                const heartClass = favs.includes(movie.title) ? 'fa-solid fa-heart text-danger' : 'fa-regular fa-heart';
                
                if (currentLayout === 'grid') {
                    col.innerHTML = `
                        <div class="movie-card h-100 cursor-pointer d-flex flex-column" data-title="${escapeAttr(movie.title)}">
                            <div class="movie-match-score"><i class="fa-solid fa-fire-flame-curved me-1"></i>${movie.score.toFixed(0)}% Match</div>
                            <div class="movie-rating-badge"><i class="fa-solid fa-star text-warning me-1"></i>${movie.rating.toFixed(1)}</div>
                            
                            <div class="movie-poster-container position-relative">
                                <img src="${posterSrc}" class="movie-poster" alt="${escapeAttr(movie.title)} Poster" loading="lazy" onerror="handlePosterError(this);">
                            </div>
                            
                            <div class="movie-info d-flex flex-column flex-grow-1 p-3">
                                <h4 class="movie-title text-truncate-2" title="${escapeAttr(movie.title)}">${escapeHTML(movie.title)}</h4>
                                <div class="movie-meta d-flex justify-content-between text-muted small my-2">
                                    <span><i class="fa-solid fa-calendar-days me-1"></i>${movie.year}</span>
                                    <span><i class="fa-solid fa-globe me-1"></i>${movie.language.toUpperCase()}</span>
                                    <span><i class="fa-solid fa-clock me-1"></i>${movie.runtime}m</span>
                                </div>
                                <p class="movie-overview text-muted text-truncate-3 small leading-relaxed flex-grow-1">${escapeHTML(movie.overview)}</p>
                                
                                <div class="d-flex justify-content-between align-items-center border-top pt-2 mt-2 border-secondary">
                                    <div class="text-truncate" style="max-width: 75%;">${genreTags}</div>
                                    <div class="d-flex gap-2">
                                        <button class="btn btn-link p-0 btn-card-favorite text-white" aria-label="Favorite"><i class="${heartClass}"></i></button>
                                        <button class="btn btn-link p-0 btn-card-share text-white" aria-label="Share"><i class="fa-regular fa-share-from-square"></i></button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                } else {
                    // Horizontal card for List View
                    col.innerHTML = `
                        <div class="movie-card list-card cursor-pointer" data-title="${escapeAttr(movie.title)}">
                            <div class="d-flex flex-column flex-md-row">
                                <div class="position-relative" style="width: 100%; max-width: 180px; min-width: 150px; aspect-ratio: 2/3; overflow: hidden; background-color: #000;" data-title="${escapeAttr(movie.title)}" data-year="${movie.year}">
                                    <div class="movie-match-score" style="top:5px; left:5px; font-size: 0.75rem;"><i class="fa-solid fa-fire-flame-curved me-1"></i>${movie.score.toFixed(0)}%</div>
                                    <img src="${posterSrc}" class="w-100 h-100" style="object-fit: cover;" alt="${escapeAttr(movie.title)}" loading="lazy" onerror="handlePosterError(this);">
                                </div>
                                <div class="p-3 flex-grow-1 d-flex flex-column justify-content-between min-width-0">
                                    <div>
                                        <div class="d-flex justify-content-between align-items-start mb-2">
                                            <h4 class="movie-title mb-0 text-white font-weight-bold text-truncate">${escapeHTML(movie.title)}</h4>
                                            <span class="badge bg-danger"><i class="fa-solid fa-star text-warning me-1"></i>${movie.rating.toFixed(1)}</span>
                                        </div>
                                        <div class="d-flex flex-wrap gap-2 text-muted small mb-2 align-items-center">
                                            <span><i class="fa-solid fa-calendar me-1"></i>${movie.year}</span>
                                            <span>&middot;</span>
                                            <span><i class="fa-solid fa-globe me-1"></i>${movie.language.toUpperCase()}</span>
                                            <span>&middot;</span>
                                            <span><i class="fa-solid fa-clock me-1"></i>${movie.runtime} mins</span>
                                            <span>&middot;</span>
                                            <span>Dir: ${escapeHTML(movie.director)}</span>
                                        </div>
                                        <p class="movie-overview text-muted small leading-relaxed text-truncate-3">${escapeHTML(movie.overview)}</p>
                                    </div>
                                    <div class="d-flex justify-content-between align-items-center mt-3 border-top pt-2 border-secondary">
                                        <div class="text-truncate" style="max-width: 80%;">${genreTags}</div>
                                        <div class="d-flex gap-3">
                                            <button class="btn btn-link p-0 btn-card-favorite text-white" aria-label="Favorite"><i class="${heartClass}"></i></button>
                                            <button class="btn btn-link p-0 btn-card-share text-white" aria-label="Share"><i class="fa-regular fa-share-from-square"></i></button>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    `;
                }

                // Add Card Details Trigger
                col.querySelector('.movie-card').addEventListener('click', function(e) {
                    // Prevent details modal trigger when clicking buttons
                    if (e.target.closest('button') || e.target.closest('.btn-card-favorite') || e.target.closest('.btn-card-share')) {
                        return;
                    }
                    openDetailsModal(movie);
                });

                // Favorite click handler
                col.querySelector('.btn-card-favorite').addEventListener('click', function(e) {
                    e.stopPropagation();
                    const icon = this.querySelector('i');
                    const added = toggleFavorite(movie.title);
                    icon.className = added ? 'fa-solid fa-heart text-danger' : 'fa-regular fa-heart';
                    window.showNotification(added ? `Added "${movie.title}" to favorites` : `Removed "${movie.title}" from favorites`, "success");
                });

                // Share click handler
                col.querySelector('.btn-card-share').addEventListener('click', function(e) {
                    e.stopPropagation();
                    const shareUrl = `${window.location.origin}/search?query=${encodeURIComponent(movie.title)}`;
                    navigator.clipboard.writeText(shareUrl)
                        .then(() => {
                            window.showNotification("Movie link copied to clipboard", "info");
                        })
                        .catch(err => {
                            window.showNotification("Failed to copy link", "error");
                        });
                });

                moviesContainer.appendChild(col);
            });

            renderPagination(totalPages);
        }

        // Render Active Filter Chips
        function renderFilterChips(minRating, minYear, searchQuery) {
            if (!filterChipsList || !filterChipsContainer) return;
            
            filterChipsList.innerHTML = '';
            let hasActiveFilters = false;
            
            // Search Query Chip
            if (searchQuery) {
                hasActiveFilters = true;
                createChip(`Search: "${searchQuery}"`, () => {
                    if (searchFilterInput) searchFilterInput.value = '';
                    triggerFilterRender();
                });
            }
            
            // Rating Chip
            if (minRating > 0) {
                hasActiveFilters = true;
                createChip(`Rating: ${minRating.toFixed(1)}+`, () => {
                    if (ratingSlider) ratingSlider.value = 0;
                    triggerFilterRender();
                });
            }
            
            // Release Year Chip
            if (minYear > 1900) {
                hasActiveFilters = true;
                createChip(`Year: ${minYear}+`, () => {
                    if (yearSlider) yearSlider.value = 1900;
                    triggerFilterRender();
                });
            }
            
            // Genre Chips
            selectedGenres.forEach(genre => {
                hasActiveFilters = true;
                createChip(`Genre: ${genre}`, () => {
                    selectedGenres.delete(genre);
                    const checkbox = document.getElementById(`genreCheckbox-${genre}`);
                    if (checkbox) checkbox.checked = false;
                    triggerFilterRender();
                });
            });
            
            if (hasActiveFilters) {
                filterChipsContainer.style.setProperty('display', 'flex', 'important');
            } else {
                filterChipsContainer.style.setProperty('display', 'none', 'important');
            }
        }

        function createChip(labelText, removeCallback) {
            const chip = document.createElement('div');
            chip.className = 'filter-chip d-flex align-items-center badge bg-secondary text-white py-2 px-3 border border-secondary';
            chip.style.borderRadius = '30px';
            chip.innerHTML = `
                <span class="me-2">${escapeHTML(labelText)}</span>
                <i class="fa-solid fa-xmark text-danger-hover cursor-pointer fs-6"></i>
            `;
            chip.querySelector('.fa-xmark').addEventListener('click', function(e) {
                e.stopPropagation();
                removeCallback();
            });
            filterChipsList.appendChild(chip);
        }

        // Clear all filters action
        function clearAllFilters() {
            selectedGenres.clear();
            
            const checkboxes = document.querySelectorAll('.filter-genre-checkbox');
            checkboxes.forEach(c => c.checked = false);
            
            if (ratingSlider) ratingSlider.value = 0;
            if (yearSlider) yearSlider.value = 1900;
            if (searchFilterInput) searchFilterInput.value = '';
            
            currentPage = 1;
            triggerFilterRender();
            window.showNotification("All filters reset", "info");
        }

        if (clearAllFiltersBtn) {
            clearAllFiltersBtn.addEventListener('click', function(e) {
                e.preventDefault();
                clearAllFilters();
            });
        }

        if (resetFiltersCTA) {
            resetFiltersCTA.addEventListener('click', clearAllFilters);
        }

        // Render Pagination UI
        function renderPagination(totalPages) {
            if (!paginationNav) return;
            paginationNav.innerHTML = '';
            
            if (totalPages <= 1) return;
            
            // Previous button
            const prevLi = document.createElement('li');
            prevLi.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
            prevLi.innerHTML = `<a class="page-link" href="#"><i class="fa-solid fa-chevron-left"></i></a>`;
            prevLi.addEventListener('click', function(e) {
                e.preventDefault();
                if (currentPage > 1) {
                    currentPage--;
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    triggerFilterRender();
                }
            });
            paginationNav.appendChild(prevLi);
            
            // Page numbers
            for (let i = 1; i <= totalPages; i++) {
                // Limit shown page items to keep pagination clean
                if (totalPages > 5 && Math.abs(i - currentPage) > 2 && i !== 1 && i !== totalPages) {
                    if (i === 2 || i === totalPages - 1) {
                        const ellLi = document.createElement('li');
                        ellLi.className = 'page-item disabled';
                        ellLi.innerHTML = `<span class="page-link">...</span>`;
                        paginationNav.appendChild(ellLi);
                    }
                    continue;
                }
                
                const li = document.createElement('li');
                li.className = `page-item ${currentPage === i ? 'active' : ''}`;
                li.innerHTML = `<a class="page-link" href="#">${i}</a>`;
                li.addEventListener('click', function(e) {
                    e.preventDefault();
                    if (currentPage !== i) {
                        currentPage = i;
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                        triggerFilterRender();
                    }
                });
                paginationNav.appendChild(li);
            }
            
            // Next button
            const nextLi = document.createElement('li');
            nextLi.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
            nextLi.innerHTML = `<a class="page-link" href="#"><i class="fa-solid fa-chevron-right"></i></a>`;
            nextLi.addEventListener('click', function(e) {
                e.preventDefault();
                if (currentPage < totalPages) {
                    currentPage++;
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                    triggerFilterRender();
                }
            });
            paginationNav.appendChild(nextLi);
        }

        // Attach event listeners to filters
        if (ratingSlider) ratingSlider.addEventListener('input', triggerFilterRender);
        if (yearSlider) yearSlider.addEventListener('input', triggerFilterRender);
        if (searchFilterInput) searchFilterInput.addEventListener('input', triggerFilterRender);
        if (sortBySelect) sortBySelect.addEventListener('change', triggerFilterRender);
        if (sortOrderSwitch) {
            sortOrderSwitch.addEventListener('change', function() {
                currentPage = 1;
                triggerFilterRender();
            });
        }

        // Run initialization
        populateGenreSidebar();
        applyFiltersAndRender();
    }

    // Utility HTML Escaping
    function escapeHTML(str) {
        if (!str) return '';
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
        );
    }
    
    function escapeAttr(str) {
        if (!str) return '';
        return str.replace(/[&<>'"]/g, 
            tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&apos;', '"': '&quot;' }[tag] || tag)
        );
    }

    // 5. Bootstrap Form Validation
    const validationForms = document.querySelectorAll('.needs-validation');
    Array.from(validationForms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                // Find first invalid input and focus it
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) firstInvalid.focus();
                
                // Hide loading overlay if form submission was blocked
                const overlay = document.getElementById('loading-overlay');
                if (overlay) overlay.classList.remove('show');
                
                window.showNotification("Please fill in all required fields correctly.", "error");
            }
            form.classList.add('was-validated');
        }, false);
    });

    // 6. Offline Connection Monitoring
    window.addEventListener('offline', function() {
        showOfflineOverlay();
    });
    window.addEventListener('online', function() {
        hideOfflineOverlay();
        window.showNotification("Internet connection restored!", "success");
    });

    function showOfflineOverlay() {
        let overlay = document.getElementById('offline-overlay');
        if (!overlay) {
            overlay = document.createElement('div');
            overlay.id = 'offline-overlay';
            overlay.innerHTML = `
                <div class="glass-card p-5 text-center border-secondary rounded shadow-2xl" style="max-width: 500px; margin: 20px;">
                    <i class="fa-solid fa-wifi-slash text-danger fs-1 mb-4"></i>
                    <h3 class="text-white font-weight-bold">Connection Interrupted</h3>
                    <p class="text-muted mb-0">It looks like you are disconnected from the internet. Please check your network settings. The app will automatically resume once online.</p>
                </div>
            `;
            document.body.appendChild(overlay);
        }
        setTimeout(() => overlay.classList.add('show'), 50);
    }

    function hideOfflineOverlay() {
        const overlay = document.getElementById('offline-overlay');
        if (overlay) {
            overlay.classList.remove('show');
            setTimeout(() => overlay.remove(), 300);
        }
    }
});
