/*!
 * Cookie Consent Manager
 * GDPR/CCPA Compliant Cookie Consent Implementation
 * Version: 1.0.0
 */

(function() {
  'use strict';

  // =========================================================================
  // CONFIGURATION
  // =========================================================================

  const COOKIE_CONSENT_NAME = 'forum_cookie_consent';
  const COOKIE_PREFERENCES_NAME = 'forum_cookie_preferences';
  const COOKIE_EXPIRY_DAYS = 365;

  const COOKIE_CATEGORIES = {
    essential: {
      name: 'Essential Cookies',
      description: 'Required for authentication and basic site functionality. Cannot be disabled.',
      required: true,
      cookies: ['session', 'csrf_token', COOKIE_CONSENT_NAME, COOKIE_PREFERENCES_NAME]
    },
    functional: {
      name: 'Functional Cookies',
      description: 'Remember your preferences and settings.',
      required: false,
      cookies: ['theme_preference', 'language_preference']
    },
    analytics: {
      name: 'Analytics Cookies',
      description: 'Help us understand how visitors use the site.',
      required: false,
      cookies: ['_ga', '_gid', '_gat']
    },
    marketing: {
      name: 'Marketing Cookies',
      description: 'Used to track visitors across websites for advertising purposes.',
      required: false,
      cookies: ['_fbp', 'fr']
    }
  };


  // =========================================================================
  // COOKIE UTILITIES
  // =========================================================================

  /**
   * Set a cookie
   */
  function setCookie(name, value, days) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = `expires=${date.toUTCString()}`;
    const sameSite = 'SameSite=Lax';
    const secure = location.protocol === 'https:' ? 'Secure' : '';

    document.cookie = `${name}=${value};${expires};path=/;${sameSite};${secure}`;
  }

  /**
   * Get a cookie value
   */
  function getCookie(name) {
    const nameEQ = name + '=';
    const ca = document.cookie.split(';');

    for (let i = 0; i < ca.length; i++) {
      let c = ca[i];
      while (c.charAt(0) === ' ') c = c.substring(1, c.length);
      if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }

    return null;
  }

  /**
   * Delete a cookie
   */
  function deleteCookie(name) {
    document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;`;
  }

  /**
   * Check if consent has been given
   */
  function hasConsent() {
    return getCookie(COOKIE_CONSENT_NAME) !== null;
  }

  /**
   * Get cookie preferences
   */
  function getPreferences() {
    const prefs = getCookie(COOKIE_PREFERENCES_NAME);
    if (!prefs) return null;

    try {
      return JSON.parse(decodeURIComponent(prefs));
    } catch (e) {
      console.error('Failed to parse cookie preferences:', e);
      return null;
    }
  }

  /**
   * Save cookie preferences
   */
  function savePreferences(preferences) {
    const value = encodeURIComponent(JSON.stringify(preferences));
    setCookie(COOKIE_PREFERENCES_NAME, value, COOKIE_EXPIRY_DAYS);
    setCookie(COOKIE_CONSENT_NAME, 'true', COOKIE_EXPIRY_DAYS);
  }


  // =========================================================================
  // COOKIE ENFORCEMENT
  // =========================================================================

  /**
   * Remove non-consented cookies
   */
  function enforceCookiePreferences(preferences) {
    // Get all current cookies
    const cookies = document.cookie.split(';');

    cookies.forEach(cookie => {
      const cookieName = cookie.split('=')[0].trim();

      // Check if this cookie is allowed
      let isAllowed = false;

      for (const [category, config] of Object.entries(COOKIE_CATEGORIES)) {
        // Essential cookies are always allowed
        if (category === 'essential' || preferences[category]) {
          if (config.cookies.includes(cookieName)) {
            isAllowed = true;
            break;
          }
        }
      }

      // Delete if not allowed
      if (!isAllowed && !isEssentialCookie(cookieName)) {
        deleteCookie(cookieName);
      }
    });
  }

  /**
   * Check if a cookie is essential
   */
  function isEssentialCookie(name) {
    return COOKIE_CATEGORIES.essential.cookies.some(pattern => {
      if (pattern.includes('*')) {
        const regex = new RegExp('^' + pattern.replace('*', '.*') + '$');
        return regex.test(name);
      }
      return name === pattern;
    });
  }


  // =========================================================================
  // ANALYTICS INTEGRATION
  // =========================================================================

  /**
   * Initialize analytics if consented
   */
  function initAnalytics(preferences) {
    if (!preferences.analytics) return;

    // Google Analytics example
    if (window.gtag) {
      window.gtag('consent', 'update', {
        'analytics_storage': 'granted'
      });
    }
  }

  /**
   * Initialize marketing if consented
   */
  function initMarketing(preferences) {
    if (!preferences.marketing) return;

    // Facebook Pixel example
    if (window.fbq) {
      window.fbq('consent', 'grant');
    }

    // Google Ads example
    if (window.gtag) {
      window.gtag('consent', 'update', {
        'ad_storage': 'granted',
        'ad_user_data': 'granted',
        'ad_personalization': 'granted'
      });
    }
  }


  // =========================================================================
  // UI COMPONENTS
  // =========================================================================

  /**
   * Show cookie consent banner
   */
  function showConsentBanner() {
    const banner = document.getElementById('cookie-consent-banner');
    if (!banner) {
      console.warn('Cookie consent banner not found in DOM');
      return;
    }

    banner.style.display = 'block';

    // Handle "Accept All" button
    const acceptAllBtn = document.getElementById('cookie-accept-all');
    if (acceptAllBtn) {
      acceptAllBtn.addEventListener('click', () => {
        acceptAll();
        banner.style.display = 'none';
      });
    }

    // Handle "Reject Non-Essential" button
    const rejectBtn = document.getElementById('cookie-reject-non-essential');
    if (rejectBtn) {
      rejectBtn.addEventListener('click', () => {
        rejectNonEssential();
        banner.style.display = 'none';
      });
    }

    // Handle "Manage Preferences" button
    const manageBtn = document.getElementById('cookie-manage');
    if (manageBtn) {
      manageBtn.addEventListener('click', () => {
        showPreferencesModal();
      });
    }
  }

  /**
   * Show preferences modal
   */
  function showPreferencesModal() {
    // Create modal if it doesn't exist
    let modal = document.getElementById('cookie-preferences-modal');

    if (!modal) {
      modal = createPreferencesModal();
      document.body.appendChild(modal);
    }

    modal.style.display = 'flex';

    // Load current preferences
    const preferences = getPreferences() || {
      essential: true,
      functional: false,
      analytics: false,
      marketing: false
    };

    // Set checkbox states
    Object.keys(COOKIE_CATEGORIES).forEach(category => {
      const checkbox = modal.querySelector(`#cookie-${category}`);
      if (checkbox) {
        checkbox.checked = preferences[category] || COOKIE_CATEGORIES[category].required;
        checkbox.disabled = COOKIE_CATEGORIES[category].required;
      }
    });

    // Handle save button
    const saveBtn = modal.querySelector('#save-preferences-btn');
    if (saveBtn) {
      saveBtn.onclick = () => {
        const newPreferences = {};
        Object.keys(COOKIE_CATEGORIES).forEach(category => {
          const checkbox = modal.querySelector(`#cookie-${category}`);
          newPreferences[category] = checkbox ? checkbox.checked : COOKIE_CATEGORIES[category].required;
        });

        savePreferences(newPreferences);
        enforceCookiePreferences(newPreferences);
        initAnalytics(newPreferences);
        initMarketing(newPreferences);

        modal.style.display = 'none';
        const banner = document.getElementById('cookie-consent-banner');
        if (banner) banner.style.display = 'none';

        showNotification('Cookie preferences saved');
      };
    }

    // Handle close button
    const closeBtn = modal.querySelector('.modal__close');
    if (closeBtn) {
      closeBtn.onclick = () => modal.style.display = 'none';
    }

    // Close on overlay click
    const overlay = modal.querySelector('.modal__overlay');
    if (overlay) {
      overlay.onclick = () => modal.style.display = 'none';
    }
  }

  /**
   * Create preferences modal element
   */
  function createPreferencesModal() {
    const modal = document.createElement('div');
    modal.id = 'cookie-preferences-modal';
    modal.className = 'modal';
    modal.style.display = 'none';

    let categoriesHTML = '';
    Object.entries(COOKIE_CATEGORIES).forEach(([key, category]) => {
      categoriesHTML += `
        <div class="preference-item">
          <div class="preference-item__header">
            <label class="preference-item__label">
              <input type="checkbox"
                     id="cookie-${key}"
                     class="preference-checkbox"
                     ${category.required ? 'checked disabled' : ''}>
              <span class="preference-item__name">${category.name}</span>
              ${category.required ? '<span class="badge badge--pinned">Required</span>' : ''}
            </label>
          </div>
          <p class="preference-item__description">${category.description}</p>
        </div>
      `;
    });

    modal.innerHTML = `
      <div class="modal__overlay"></div>
      <div class="modal__container">
        <div class="modal__header">
          <h2 class="modal__title">Cookie Preferences</h2>
          <button class="modal__close" aria-label="Close">
            <svg width="24" height="24">
              <path d="M6 6l12 12M6 18L18 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
            </svg>
          </button>
        </div>
        <div class="modal__body">
          <p style="margin-bottom: 1.5rem; color: var(--color-gray-600);">
            We use cookies to enhance your browsing experience and analyze our traffic.
            Choose which types of cookies you want to allow:
          </p>
          ${categoriesHTML}
        </div>
        <div class="modal__footer">
          <button class="btn btn--primary" id="save-preferences-btn">
            Save Preferences
          </button>
        </div>
      </div>
    `;

    // Add styles
    const style = document.createElement('style');
    style.textContent = `
      .preference-item {
        padding: 1rem;
        margin-bottom: 1rem;
        border: 1px solid var(--color-gray-200);
        border-radius: var(--radius-lg);
      }
      .preference-item__header {
        margin-bottom: 0.5rem;
      }
      .preference-item__label {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        cursor: pointer;
        font-weight: 500;
      }
      .preference-checkbox {
        width: 20px;
        height: 20px;
        cursor: pointer;
      }
      .preference-checkbox:disabled {
        cursor: not-allowed;
        opacity: 0.6;
      }
      .preference-item__name {
        flex: 1;
      }
      .preference-item__description {
        margin: 0;
        margin-left: 2rem;
        font-size: 0.875rem;
        color: var(--color-gray-600);
      }
    `;
    document.head.appendChild(style);

    return modal;
  }

  /**
   * Show notification
   */
  function showNotification(message) {
    const notification = document.createElement('div');
    notification.className = 'alert alert--success';
    notification.style.cssText = `
      position: fixed;
      top: 80px;
      right: 20px;
      z-index: 10000;
      min-width: 300px;
      animation: slideInRight 0.3s ease-out;
    `;

    notification.innerHTML = `
      <svg class="alert__icon" width="20" height="20">
        <circle cx="10" cy="10" r="9" stroke="currentColor" stroke-width="1.5" fill="none"/>
        <path d="M6 10l3 3 5-6" stroke="currentColor" stroke-width="1.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
      <span class="alert__message">${message}</span>
    `;

    document.body.appendChild(notification);

    setTimeout(() => {
      notification.style.animation = 'slideOutRight 0.3s ease-in';
      setTimeout(() => notification.remove(), 300);
    }, 3000);
  }


  // =========================================================================
  // CONSENT ACTIONS
  // =========================================================================

  /**
   * Accept all cookies
   */
  function acceptAll() {
    const preferences = {};
    Object.keys(COOKIE_CATEGORIES).forEach(category => {
      preferences[category] = true;
    });

    savePreferences(preferences);
    initAnalytics(preferences);
    initMarketing(preferences);

    console.log('✓ All cookies accepted');
  }

  /**
   * Reject non-essential cookies
   */
  function rejectNonEssential() {
    const preferences = {};
    Object.keys(COOKIE_CATEGORIES).forEach(category => {
      preferences[category] = COOKIE_CATEGORIES[category].required;
    });

    savePreferences(preferences);
    enforceCookiePreferences(preferences);

    console.log('✓ Non-essential cookies rejected');
  }


  // =========================================================================
  // INITIALIZATION
  // =========================================================================

  function init() {
    console.log('🍪 Initializing Cookie Consent Manager...');

    // Check if user has already consented
    if (hasConsent()) {
      const preferences = getPreferences();

      if (preferences) {
        // Enforce preferences
        enforceCookiePreferences(preferences);
        initAnalytics(preferences);
        initMarketing(preferences);
        console.log('✓ Cookie preferences loaded:', preferences);
      } else {
        // Legacy consent without preferences - show banner again
        deleteCookie(COOKIE_CONSENT_NAME);
        showConsentBanner();
      }
    } else {
      // No consent yet - show banner
      showConsentBanner();
    }

    // Add settings link to footer (if exists)
    const footer = document.querySelector('.footer');
    if (footer) {
      const settingsLink = document.createElement('button');
      settingsLink.textContent = 'Cookie Settings';
      settingsLink.className = 'footer__link';
      settingsLink.style.cssText = 'background: none; border: none; cursor: pointer; padding: 0; text-decoration: underline;';
      settingsLink.onclick = showPreferencesModal;

      // Try to add to footer links
      const footerLinks = footer.querySelector('.footer__links');
      if (footerLinks) {
        const li = document.createElement('li');
        li.appendChild(settingsLink);
        footerLinks.appendChild(li);
      }
    }

    console.log('✓ Cookie Consent Manager initialized');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Expose API for external use
  window.CookieConsent = {
    hasConsent,
    getPreferences,
    savePreferences,
    acceptAll,
    rejectNonEssential,
    showPreferencesModal
  };

})();
