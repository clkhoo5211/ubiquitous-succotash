/*!
 * Decentralized Autonomous Forum - Main JavaScript
 * Version: 1.0.0
 * Description: Core client-side functionality
 */

(function() {
  'use strict';

  // =========================================================================
  // GLOBAL STATE
  // =========================================================================

  const App = {
    initialized: false,
    apiBaseUrl: '/api/v1',
    currentUser: null
  };


  // =========================================================================
  // UTILITY FUNCTIONS
  // =========================================================================

  /**
   * Debounce function execution
   */
  function debounce(func, wait) {
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

  /**
   * Throttle function execution
   */
  function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }

  /**
   * Format number with commas
   */
  function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
  }

  /**
   * Get relative time string
   */
  function getRelativeTime(dateString) {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now - date) / 1000);

    const intervals = {
      year: 31536000,
      month: 2592000,
      week: 604800,
      day: 86400,
      hour: 3600,
      minute: 60
    };

    for (const [unit, secondsInUnit] of Object.entries(intervals)) {
      const interval = Math.floor(seconds / secondsInUnit);
      if (interval >= 1) {
        return interval === 1 ? `1 ${unit} ago` : `${interval} ${unit}s ago`;
      }
    }

    return 'just now';
  }

  /**
   * Show toast notification
   */
  function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `alert alert--${type}`;
    toast.style.cssText = `
      position: fixed;
      top: 80px;
      right: 20px;
      z-index: 10000;
      min-width: 300px;
      animation: slideInRight 0.3s ease-out;
    `;

    const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';

    toast.innerHTML = `
      <svg class="alert__icon" width="20" height="20">
        <use xlink:href="#icon-${type === 'success' ? 'check' : type === 'error' ? 'x' : 'info'}-circle"/>
      </svg>
      <span class="alert__message">${message}</span>
      <button class="alert__close" aria-label="Close">&times;</button>
    `;

    document.body.appendChild(toast);

    toast.querySelector('.alert__close').addEventListener('click', () => {
      toast.remove();
    });

    setTimeout(() => {
      toast.style.animation = 'slideOutRight 0.3s ease-in';
      setTimeout(() => toast.remove(), 300);
    }, 5000);
  }


  // =========================================================================
  // API FUNCTIONS
  // =========================================================================

  /**
   * Make API request
   */
  async function apiRequest(endpoint, options = {}) {
    const url = `${App.apiBaseUrl}${endpoint}`;

    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'same-origin'
    };

    const response = await fetch(url, { ...defaultOptions, ...options });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }


  // =========================================================================
  // ALERT/FLASH MESSAGE HANDLING
  // =========================================================================

  function initAlerts() {
    document.querySelectorAll('.alert__close').forEach(btn => {
      btn.addEventListener('click', function() {
        const alert = this.closest('.alert');
        alert.style.animation = 'fadeOut 0.3s ease-out';
        setTimeout(() => alert.remove(), 300);
      });
    });

    // Auto-dismiss alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(alert => {
      setTimeout(() => {
        if (alert.parentElement) {
          alert.style.animation = 'fadeOut 0.3s ease-out';
          setTimeout(() => alert.remove(), 300);
        }
      }, 5000);
    });
  }


  // =========================================================================
  // MOBILE MENU
  // =========================================================================

  function initMobileMenu() {
    const toggle = document.getElementById('mobile-menu-toggle');
    const menu = document.getElementById('mobile-menu');

    if (!toggle || !menu) return;

    toggle.addEventListener('click', () => {
      const isOpen = menu.style.display === 'flex';
      menu.style.display = isOpen ? 'none' : 'flex';
      toggle.setAttribute('aria-expanded', !isOpen);

      // Animate toggle icon
      const icon = toggle.querySelector('.navbar__toggle-icon');
      if (icon) {
        icon.style.transform = isOpen ? 'rotate(0deg)' : 'rotate(90deg)';
      }
    });

    // Close menu when clicking outside (MOBILE ONLY)
    // This should only apply on mobile screens where menu can be open
    document.addEventListener('click', (e) => {
      // Only close menu on mobile screens (< 768px)
      if (window.innerWidth < 768 && menu.style.display === 'flex') {
        if (!toggle.contains(e.target) && !menu.contains(e.target)) {
          menu.style.display = 'none';
          toggle.setAttribute('aria-expanded', 'false');
          
          // Reset toggle icon
          const icon = toggle.querySelector('.navbar__toggle-icon');
          if (icon) {
            icon.style.transform = 'rotate(0deg)';
          }
        }
      }
    });

    // Close menu on window resize to desktop
    window.addEventListener('resize', throttle(() => {
      if (window.innerWidth >= 768) {
        menu.style.display = '';
        toggle.setAttribute('aria-expanded', 'false');
      }
    }, 200));
  }


  // =========================================================================
  // USER DROPDOWN
  // =========================================================================

  function initUserDropdown() {
    const dropdowns = document.querySelectorAll('.user-dropdown');
    
    dropdowns.forEach(dropdown => {
      const trigger = dropdown.querySelector('.user-dropdown__trigger');
      const menu = dropdown.querySelector('.user-dropdown__menu');
      
      if (!trigger || !menu) return;
      
      // Initialize as closed
      dropdown.setAttribute('data-open', 'false');
      
      // Toggle menu on trigger click
      trigger.addEventListener('click', (e) => {
        e.stopPropagation();
        e.preventDefault();
        
        const isOpen = dropdown.getAttribute('data-open') === 'true';
        const newState = !isOpen;
        
        dropdown.setAttribute('data-open', newState.toString());
        trigger.setAttribute('aria-expanded', newState);
        
        // Update arrow rotation
        const arrow = trigger.querySelector('.user-dropdown__arrow');
        if (arrow) {
          arrow.style.transform = newState ? 'rotate(180deg)' : 'rotate(0deg)';
        }
      });
      
      // Prevent clicks inside menu from closing dropdown
      menu.addEventListener('click', (e) => {
        e.stopPropagation();
      });
    });
    
    // Single global click listener to close all dropdowns when clicking outside
    document.addEventListener('click', (e) => {
      dropdowns.forEach(dropdown => {
        const trigger = dropdown.querySelector('.user-dropdown__trigger');
        
        if (!dropdown.contains(e.target)) {
          dropdown.setAttribute('data-open', 'false');
          if (trigger) {
            trigger.setAttribute('aria-expanded', 'false');
            const arrow = trigger.querySelector('.user-dropdown__arrow');
            if (arrow) {
              arrow.style.transform = 'rotate(0deg)';
            }
          }
        }
      });
    });
  }


  // =========================================================================
  // INFINITE SCROLL
  // =========================================================================

  function initInfiniteScroll() {
    const container = document.querySelector('[data-infinite-scroll]');
    if (!container) return;

    const loadMore = container.dataset.infiniteScroll;
    let page = 2;
    let loading = false;
    let hasMore = true;

    const observer = new IntersectionObserver(
      async (entries) => {
        const entry = entries[0];
        if (entry.isIntersecting && !loading && hasMore) {
          loading = true;

          try {
            const response = await apiRequest(`${loadMore}?page=${page}`);

            if (response.items && response.items.length > 0) {
              // Append new items (implementation depends on page structure)
              page++;
            } else {
              hasMore = false;
              observer.disconnect();
            }
          } catch (error) {
            console.error('Failed to load more items:', error);
            showToast('Failed to load more content', 'error');
          } finally {
            loading = false;
          }
        }
      },
      { rootMargin: '200px' }
    );

    const sentinel = document.createElement('div');
    sentinel.style.height = '1px';
    container.appendChild(sentinel);
    observer.observe(sentinel);
  }


  // =========================================================================
  // IMAGE LAZY LOADING
  // =========================================================================

  function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');

    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          observer.unobserve(img);
        }
      });
    });

    images.forEach(img => imageObserver.observe(img));
  }


  // =========================================================================
  // SEARCH FUNCTIONALITY
  // =========================================================================

  function initSearch() {
    const searchInput = document.getElementById('search-input');
    if (!searchInput) return;

    const resultsContainer = document.getElementById('search-results');
    const postsList = document.querySelector('.posts-list, .post-list');

    const performSearch = debounce(async (query) => {
      if (query.length < 2) {
        if (resultsContainer) {
          resultsContainer.innerHTML = '';
          resultsContainer.classList.add('hidden');
        }
        if (postsList) {
          postsList.style.display = '';
        }
        return;
      }

      // Hide posts, show search results
      if (postsList) {
        postsList.style.display = 'none';
      }
      if (resultsContainer) {
        resultsContainer.classList.remove('hidden');
      }

      try {
        const results = await apiRequest(`/search?q=${encodeURIComponent(query)}`);

        if (!resultsContainer) return;

        if (results.length === 0) {
          resultsContainer.innerHTML = '<p class="search-empty">No results found</p>';
        } else {
          resultsContainer.innerHTML = results.map(result => `
            <a href="${result.url}" class="search-result">
              <h4 class="search-result__title">${result.title}</h4>
              <p class="search-result__excerpt">${result.excerpt}</p>
            </a>
          `).join('');
        }
      } catch (error) {
        console.error('Search failed:', error);
        if (resultsContainer) {
          resultsContainer.innerHTML = '<p class="search-empty">Search failed. Please try again.</p>';
        }
      }
    }, 300);

    searchInput.addEventListener('input', (e) => {
      performSearch(e.target.value);
    });
  }


  // =========================================================================
  // MARKDOWN PREVIEW
  // =========================================================================

  function initMarkdownPreview() {
    const textarea = document.getElementById('markdown-input');
    const preview = document.getElementById('markdown-preview');
    const toggleBtn = document.getElementById('preview-toggle');

    if (!textarea || !preview) return;

    const updatePreview = debounce(() => {
      // Simple markdown to HTML conversion (basic implementation)
      let html = textarea.value
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>')
        .replace(/`(.*?)`/g, '<code>$1</code>')
        .replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>')
        .replace(/\n/g, '<br>');

      preview.innerHTML = html;
    }, 300);

    textarea.addEventListener('input', updatePreview);

    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        preview.classList.toggle('hidden');
        toggleBtn.textContent = preview.classList.contains('hidden')
          ? 'Show Preview'
          : 'Hide Preview';
      });
    }
  }


  // =========================================================================
  // COPY TO CLIPBOARD
  // =========================================================================

  function initCopyButtons() {
    document.querySelectorAll('[data-copy]').forEach(btn => {
      btn.addEventListener('click', async function() {
        const text = this.dataset.copy || this.previousElementSibling?.textContent;

        if (!text) return;

        try {
          await navigator.clipboard.writeText(text);
          const originalText = this.textContent;
          this.textContent = 'Copied!';
          setTimeout(() => {
            this.textContent = originalText;
          }, 2000);
        } catch (error) {
          console.error('Failed to copy:', error);
          showToast('Failed to copy to clipboard', 'error');
        }
      });
    });
  }


  // =========================================================================
  // FORM VALIDATION
  // =========================================================================

  function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');

    forms.forEach(form => {
      form.addEventListener('submit', function(e) {
        let isValid = true;

        // Clear previous errors
        this.querySelectorAll('.form-error').forEach(el => el.textContent = '');

        // Validate required fields
        this.querySelectorAll('[required]').forEach(field => {
          if (!field.value.trim()) {
            isValid = false;
            const error = field.parentElement.querySelector('.form-error');
            if (error) error.textContent = 'This field is required';
            field.classList.add('error');
          } else {
            field.classList.remove('error');
          }
        });

        // Validate email fields
        this.querySelectorAll('[type="email"]').forEach(field => {
          const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
          if (field.value && !emailRegex.test(field.value)) {
            isValid = false;
            const error = field.parentElement.querySelector('.form-error');
            if (error) error.textContent = 'Please enter a valid email address';
            field.classList.add('error');
          }
        });

        if (!isValid) {
          e.preventDefault();
          showToast('Please fix the errors in the form', 'error');
        }
      });
    });
  }


  // =========================================================================
  // KEYBOARD SHORTCUTS
  // =========================================================================

  function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
      // Cmd/Ctrl + K: Focus search
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('search-input');
        if (searchInput) searchInput.focus();
      }

      // Cmd/Ctrl + Enter: Submit form (when in textarea)
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        if (e.target.tagName === 'TEXTAREA') {
          const form = e.target.closest('form');
          if (form) {
            e.preventDefault();
            form.requestSubmit();
          }
        }
      }

      // Escape: Close modals
      if (e.key === 'Escape') {
        document.querySelectorAll('.modal[style*="display: flex"]').forEach(modal => {
          modal.style.display = 'none';
        });
      }
    });
  }


  // =========================================================================
  // LIKE ANIMATIONS
  // =========================================================================

  function initLikeButtons() {
    document.querySelectorAll('[data-like-btn]').forEach(btn => {
      btn.addEventListener('click', async function(e) {
        e.preventDefault();

        const postId = this.dataset.postId;
        const commentId = this.dataset.commentId;
        const endpoint = postId
          ? `/posts/${postId}/like`
          : `/comments/${commentId}/like`;

        try {
          const data = await apiRequest(endpoint, { method: 'POST' });

          // Update count
          const countEl = this.querySelector('[data-like-count]');
          if (countEl) {
            countEl.textContent = data.like_count || data.likes;
          }

          // Toggle active state
          this.classList.toggle('action-btn--active');

          // Animate
          this.style.transform = 'scale(1.2)';
          setTimeout(() => {
            this.style.transform = '';
          }, 200);

        } catch (error) {
          console.error('Like failed:', error);
          showToast(error.message || 'Failed to like', 'error');
        }
      });
    });
  }


  // =========================================================================
  // AUTO-SAVE DRAFTS
  // =========================================================================

  function initAutoSave() {
    const forms = document.querySelectorAll('[data-autosave]');

    forms.forEach(form => {
      const key = `draft_${form.dataset.autosave}`;

      // Load saved draft
      try {
        const saved = localStorage.getItem(key);
        if (saved) {
          const data = JSON.parse(saved);
          Object.entries(data).forEach(([name, value]) => {
            const field = form.querySelector(`[name="${name}"]`);
            if (field) field.value = value;
          });

          showToast('Draft restored', 'info');
        }
      } catch (error) {
        console.error('Failed to load draft:', error);
      }

      // Save draft on input
      const saveDraft = debounce(() => {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);

        try {
          localStorage.setItem(key, JSON.stringify(data));
        } catch (error) {
          console.error('Failed to save draft:', error);
        }
      }, 1000);

      form.addEventListener('input', saveDraft);

      // Clear draft on submit
      form.addEventListener('submit', () => {
        localStorage.removeItem(key);
      });
    });
  }


  // =========================================================================
  // SCROLL TO TOP
  // =========================================================================

  function initScrollToTop() {
    const btn = document.createElement('button');
    btn.className = 'scroll-to-top';
    btn.innerHTML = '↑';
    btn.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      width: 48px;
      height: 48px;
      border-radius: 50%;
      background-color: var(--color-primary);
      color: var(--color-gray-900);
      border: none;
      font-size: 24px;
      cursor: pointer;
      display: none;
      z-index: 1000;
      box-shadow: var(--shadow-lg);
      transition: all 0.3s;
    `;

    document.body.appendChild(btn);

    window.addEventListener('scroll', throttle(() => {
      if (window.pageYOffset > 300) {
        btn.style.display = 'flex';
      } else {
        btn.style.display = 'none';
      }
    }, 200));

    btn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /**
   * Initialize filter tabs (Hot/New/Top)
   */
  function initFilterTabs() {
    // Handle filter-tab (home page)
    const filterTabs = document.querySelectorAll('.filter-tab');
    filterTabs.forEach(tab => {
      tab.addEventListener('click', async function() {
        // Remove active class from all tabs
        document.querySelectorAll('.filter-tab').forEach(t => {
          t.classList.remove('filter-tab--active');
        });
        
        // Add active class to clicked tab
        this.classList.add('filter-tab--active');
        
        // Get the filter type from data-filter attribute
        const filter = this.dataset.filter;
        
        // Reload the page with the filter query parameter
        const url = new URL(window.location.href);
        url.searchParams.set('filter', filter);
        url.searchParams.set('page', '1'); // Reset to first page
        
        // Navigate to the filtered page
        window.location.href = url.toString();
      });
    });
    
    // Handle filter-btn (explore page)
    const filterBtns = document.querySelectorAll('.filter-btn');
    filterBtns.forEach(btn => {
      btn.addEventListener('click', async function() {
        // Remove active class from all buttons
        document.querySelectorAll('.filter-btn').forEach(b => {
          b.classList.remove('filter-btn--active');
        });
        
        // Add active class to clicked button
        this.classList.add('filter-btn--active');
        
        // Get the filter type from data-filter attribute
        const filter = this.dataset.filter;
        
        // Reload the page with the filter query parameter
        const url = new URL(window.location.href);
        if (filter === 'all') {
          url.searchParams.delete('filter');
        } else {
          url.searchParams.set('filter', filter);
        }
        url.searchParams.set('page', '1'); // Reset to first page
        
        // Navigate to the filtered page
        window.location.href = url.toString();
      });
    });
  }


  // =========================================================================
  // INITIALIZATION
  // =========================================================================

  function init() {
    if (App.initialized) return;

    console.log('🚀 Initializing Decentralized Forum...');

    // Initialize components
    initAlerts();
    initMobileMenu();
    initUserDropdown();
    initSearch();
    initMarkdownPreview();
    initCopyButtons();
    initFormValidation();
    initKeyboardShortcuts();
    initLikeButtons();
    initAutoSave();
    initLazyLoading();
    initInfiniteScroll();
    initScrollToTop();
    initFilterTabs();

    App.initialized = true;
    console.log('✅ Forum initialized successfully');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose App to global scope for debugging
  window.ForumApp = App;

})();
