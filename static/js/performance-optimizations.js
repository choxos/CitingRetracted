/**
 * Performance Optimization JavaScript for Open Science Tracker
 * 
 * This file includes optimizations for:
 * - Lazy loading of images and content
 * - Debounced search functionality
 * - Efficient DOM operations
 * - Progressive loading of large lists
 * - Memory-efficient table operations
 */

class OST_PerformanceOptimizer {
    constructor() {
        this.init();
    }

    init() {
        this.setupLazyLoading();
        this.setupDebouncedSearch();
        this.setupProgressiveLoading();
        this.setupTableOptimizations();
        this.setupImageOptimizations();
        this.setupMemoryManagement();
    }

    /**
     * Lazy Loading Implementation
     */
    setupLazyLoading() {
        // Intersection Observer for lazy loading
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        this.loadImage(img);
                        observer.unobserve(img);
                    }
                });
            }, {
                rootMargin: '50px 0px',
                threshold: 0.01
            });

            // Observe all lazy images
            document.querySelectorAll('img[data-src]').forEach(img => {
                imageObserver.observe(img);
            });

            // Lazy load content sections
            const contentObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const element = entry.target;
                        this.loadLazyContent(element);
                        observer.unobserve(element);
                    }
                });
            }, {
                rootMargin: '100px 0px'
            });

            document.querySelectorAll('[data-lazy-load]').forEach(element => {
                contentObserver.observe(element);
            });
        }
    }

    loadImage(img) {
        const src = img.dataset.src;
        if (src) {
            img.src = src;
            img.classList.remove('lazy');
            img.classList.add('loaded');
            img.removeAttribute('data-src');
        }
    }

    loadLazyContent(element) {
        const url = element.dataset.lazyLoad;
        if (url) {
            fetch(url)
                .then(response => response.text())
                .then(html => {
                    element.innerHTML = html;
                    element.classList.remove('lazy-content');
                    element.classList.add('loaded-content');
                })
                .catch(error => {
                    console.warn('Failed to load lazy content:', error);
                    element.classList.add('load-error');
                });
        }
    }

    /**
     * Debounced Search Implementation
     */
    setupDebouncedSearch() {
        const searchInputs = document.querySelectorAll('[data-search-debounce]');
        
        searchInputs.forEach(input => {
            const delay = parseInt(input.dataset.searchDebounce) || 300;
            let timeout;

            input.addEventListener('input', (e) => {
                clearTimeout(timeout);
                const form = input.closest('form');
                
                timeout = setTimeout(() => {
                    if (input.value.length >= 2 || input.value.length === 0) {
                        this.performSearch(form, input.value);
                    }
                }, delay);
            });

            // Immediate search on enter
            input.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    clearTimeout(timeout);
                    this.performSearch(input.closest('form'), input.value);
                    e.preventDefault();
                }
            });
        });
    }

    performSearch(form, query) {
        // Add loading state
        const submitBtn = form.querySelector('[type="submit"]');
        const originalText = submitBtn ? submitBtn.textContent : '';
        
        if (submitBtn) {
            submitBtn.textContent = 'Searching...';
            submitBtn.disabled = true;
        }

        // Perform the search
        const formData = new FormData(form);
        const searchParams = new URLSearchParams(formData);
        
        // Update URL without page reload for AJAX search
        if (form.dataset.ajaxSearch === 'true') {
            this.performAjaxSearch(form.action, searchParams, form);
        } else {
            form.submit();
        }

        // Restore button state
        setTimeout(() => {
            if (submitBtn) {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        }, 1000);
    }

    performAjaxSearch(url, params, form) {
        const resultsContainer = document.querySelector(form.dataset.resultsContainer || '#search-results');
        
        if (!resultsContainer) {
            form.submit(); // Fallback to regular form submission
            return;
        }

        // Add loading indicator
        resultsContainer.classList.add('loading');
        resultsContainer.innerHTML = '<div class="loading-spinner">Searching...</div>';

        fetch(`${url}?${params.toString()}`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
        .then(response => response.text())
        .then(html => {
            resultsContainer.innerHTML = html;
            resultsContainer.classList.remove('loading');
            
            // Reinitialize optimizations for new content
            this.reinitializeForNewContent(resultsContainer);
        })
        .catch(error => {
            console.error('Search error:', error);
            resultsContainer.innerHTML = '<div class="error">Search failed. Please try again.</div>';
            resultsContainer.classList.remove('loading');
        });
    }

    /**
     * Progressive Loading for Large Lists
     */
    setupProgressiveLoading() {
        const progressiveContainers = document.querySelectorAll('[data-progressive-load]');
        
        progressiveContainers.forEach(container => {
            const itemsPerPage = parseInt(container.dataset.itemsPerPage) || 20;
            const items = Array.from(container.querySelectorAll('[data-progressive-item]'));
            
            if (items.length <= itemsPerPage) return;

            // Hide items beyond first page
            items.slice(itemsPerPage).forEach(item => {
                item.style.display = 'none';
                item.classList.add('progressive-hidden');
            });

            // Add load more button
            const loadMoreBtn = document.createElement('button');
            loadMoreBtn.className = 'btn btn-outline-primary load-more-btn';
            loadMoreBtn.textContent = `Load More (${items.length - itemsPerPage} remaining)`;
            loadMoreBtn.type = 'button';

            container.appendChild(loadMoreBtn);

            let currentlyVisible = itemsPerPage;

            loadMoreBtn.addEventListener('click', () => {
                const nextBatch = items.slice(currentlyVisible, currentlyVisible + itemsPerPage);
                
                nextBatch.forEach(item => {
                    item.style.display = '';
                    item.classList.remove('progressive-hidden');
                    item.classList.add('progressive-loaded');
                });

                currentlyVisible += itemsPerPage;

                if (currentlyVisible >= items.length) {
                    loadMoreBtn.style.display = 'none';
                } else {
                    loadMoreBtn.textContent = `Load More (${items.length - currentlyVisible} remaining)`;
                }
            });
        });
    }

    /**
     * Table Optimizations for Large Datasets
     */
    setupTableOptimizations() {
        const largeTables = document.querySelectorAll('table[data-large-table]');
        
        largeTables.forEach(table => {
            this.optimizeTable(table);
        });
    }

    optimizeTable(table) {
        // Virtual scrolling for very large tables
        const rowCount = table.querySelectorAll('tbody tr').length;
        const threshold = parseInt(table.dataset.virtualThreshold) || 100;

        if (rowCount > threshold) {
            this.implementVirtualScrolling(table);
        }

        // Efficient sorting
        const sortableHeaders = table.querySelectorAll('th[data-sortable]');
        sortableHeaders.forEach(header => {
            header.style.cursor = 'pointer';
            header.addEventListener('click', () => {
                this.sortTable(table, header);
            });
        });

        // Column resizing
        this.addColumnResizing(table);
    }

    implementVirtualScrolling(table) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const rowHeight = 40; // Estimated row height
        const visibleRows = Math.ceil(window.innerHeight / rowHeight) + 10; // Buffer

        const container = document.createElement('div');
        container.className = 'virtual-scroll-container';
        container.style.height = `${rows.length * rowHeight}px`;
        container.style.overflow = 'auto';

        const viewport = document.createElement('div');
        viewport.className = 'virtual-scroll-viewport';

        let startIndex = 0;
        let endIndex = Math.min(visibleRows, rows.length);

        const renderRows = () => {
            viewport.innerHTML = '';
            viewport.style.paddingTop = `${startIndex * rowHeight}px`;
            viewport.style.paddingBottom = `${(rows.length - endIndex) * rowHeight}px`;

            for (let i = startIndex; i < endIndex; i++) {
                if (rows[i]) {
                    viewport.appendChild(rows[i].cloneNode(true));
                }
            }
        };

        container.addEventListener('scroll', () => {
            const scrollTop = container.scrollTop;
            const newStartIndex = Math.floor(scrollTop / rowHeight);
            const newEndIndex = Math.min(newStartIndex + visibleRows, rows.length);

            if (newStartIndex !== startIndex || newEndIndex !== endIndex) {
                startIndex = newStartIndex;
                endIndex = newEndIndex;
                renderRows();
            }
        });

        container.appendChild(viewport);
        table.parentNode.replaceChild(container, table);
        renderRows();
    }

    sortTable(table, header) {
        const columnIndex = Array.from(header.parentNode.children).indexOf(header);
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const isNumeric = header.dataset.sortType === 'numeric';
        const currentDirection = header.dataset.sortDirection || 'asc';
        const newDirection = currentDirection === 'asc' ? 'desc' : 'asc';

        // Clear other sort indicators
        table.querySelectorAll('th[data-sortable]').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });

        // Sort rows
        rows.sort((a, b) => {
            const aVal = a.cells[columnIndex].textContent.trim();
            const bVal = b.cells[columnIndex].textContent.trim();

            let comparison;
            if (isNumeric) {
                comparison = parseFloat(aVal) - parseFloat(bVal);
            } else {
                comparison = aVal.localeCompare(bVal);
            }

            return newDirection === 'asc' ? comparison : -comparison;
        });

        // Reorder DOM
        rows.forEach(row => tbody.appendChild(row));

        // Update header
        header.dataset.sortDirection = newDirection;
        header.classList.add(`sort-${newDirection}`);
    }

    addColumnResizing(table) {
        const headers = table.querySelectorAll('th');
        
        headers.forEach((header, index) => {
            if (index < headers.length - 1) { // Don't add to last column
                const resizer = document.createElement('div');
                resizer.className = 'column-resizer';
                resizer.style.cssText = `
                    position: absolute;
                    right: 0;
                    top: 0;
                    bottom: 0;
                    width: 5px;
                    cursor: col-resize;
                    background: transparent;
                `;

                header.style.position = 'relative';
                header.appendChild(resizer);

                this.makeResizable(header, resizer);
            }
        });
    }

    makeResizable(header, resizer) {
        let startX, startWidth;

        resizer.addEventListener('mousedown', (e) => {
            startX = e.clientX;
            startWidth = parseInt(document.defaultView.getComputedStyle(header).width, 10);
            document.addEventListener('mousemove', doResize);
            document.addEventListener('mouseup', stopResize);
            e.preventDefault();
        });

        function doResize(e) {
            header.style.width = (startWidth + e.clientX - startX) + 'px';
        }

        function stopResize() {
            document.removeEventListener('mousemove', doResize);
            document.removeEventListener('mouseup', stopResize);
        }
    }

    /**
     * Image Optimizations
     */
    setupImageOptimizations() {
        // Preload critical images
        const criticalImages = document.querySelectorAll('img[data-critical]');
        criticalImages.forEach(img => {
            if (img.dataset.src) {
                this.loadImage(img);
            }
        });

        // Implement responsive images
        this.setupResponsiveImages();
    }

    setupResponsiveImages() {
        const responsiveImages = document.querySelectorAll('img[data-responsive]');
        
        responsiveImages.forEach(img => {
            const updateSrc = () => {
                const width = img.offsetWidth;
                const baseSrc = img.dataset.responsive;
                let size = 'small';

                if (width > 800) size = 'large';
                else if (width > 400) size = 'medium';

                const newSrc = baseSrc.replace('{size}', size);
                if (img.src !== newSrc) {
                    img.src = newSrc;
                }
            };

            updateSrc();
            window.addEventListener('resize', this.debounce(updateSrc, 250));
        });
    }

    /**
     * Memory Management
     */
    setupMemoryManagement() {
        // Clean up observers when elements are removed
        this.setupMutationObserver();
        
        // Periodic cleanup
        setInterval(() => {
            this.performMemoryCleanup();
        }, 30000); // Every 30 seconds
    }

    setupMutationObserver() {
        if ('MutationObserver' in window) {
            const observer = new MutationObserver((mutations) => {
                mutations.forEach((mutation) => {
                    mutation.removedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.cleanupElement(node);
                        }
                    });
                });
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });
        }
    }

    cleanupElement(element) {
        // Remove event listeners and observers from removed elements
        const images = element.querySelectorAll ? element.querySelectorAll('img[data-observer]') : [];
        images.forEach(img => {
            if (img._observer) {
                img._observer.disconnect();
                delete img._observer;
            }
        });
    }

    performMemoryCleanup() {
        // Force garbage collection if available (Chrome DevTools)
        if (window.gc && typeof window.gc === 'function') {
            window.gc();
        }

        // Clean up cached elements that are no longer in DOM
        this.cleanupCache();
    }

    cleanupCache() {
        // Implementation depends on specific caching strategy
        console.log('Performing memory cleanup...');
    }

    /**
     * Utility Functions
     */
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    throttle(func, limit) {
        let inThrottle;
        return function(...args) {
            if (!inThrottle) {
                func.apply(this, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    reinitializeForNewContent(container) {
        // Reinitialize lazy loading for new content
        const newImages = container.querySelectorAll('img[data-src]');
        newImages.forEach(img => {
            if ('IntersectionObserver' in window) {
                const observer = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            this.loadImage(entry.target);
                            observer.unobserve(entry.target);
                        }
                    });
                });
                observer.observe(img);
            }
        });

        // Reinitialize progressive loading
        const progressiveContainers = container.querySelectorAll('[data-progressive-load]');
        progressiveContainers.forEach(cont => {
            this.setupProgressiveLoading();
        });
    }
}

// CSS for performance optimizations
const performanceCSS = `
.lazy {
    opacity: 0;
    transition: opacity 0.3s;
}

.lazy.loaded {
    opacity: 1;
}

.lazy-content {
    min-height: 100px;
    background: #f8f9fa;
    display: flex;
    align-items: center;
    justify-content: center;
}

.loading-spinner {
    padding: 2rem;
    text-align: center;
    color: #6c757d;
}

.load-more-btn {
    margin: 1rem auto;
    display: block;
}

.progressive-hidden {
    display: none !important;
}

.progressive-loaded {
    animation: fadeIn 0.3s ease-in;
}

@keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

.virtual-scroll-container {
    overflow: auto;
    height: 400px;
}

.column-resizer:hover {
    background: #007bff !important;
}

th.sort-asc::after {
    content: ' ↑';
}

th.sort-desc::after {
    content: ' ↓';
}

.error {
    color: #dc3545;
    padding: 1rem;
    text-align: center;
}
`;

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Add CSS
    const style = document.createElement('style');
    style.textContent = performanceCSS;
    document.head.appendChild(style);

    // Initialize performance optimizer
    new OST_PerformanceOptimizer();

    console.log('OST Performance Optimizations loaded');
});

// Export for use in other scripts
window.OST_PerformanceOptimizer = OST_PerformanceOptimizer; 