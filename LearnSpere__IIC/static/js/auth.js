/**
 * Authentication Handler
 * Manages user authentication state on the client side
 */

const authManager = {
    init: function() {
        console.log('Auth manager initialized');
        this.checkAuthStatus();
        this.setupAuthUI();
        this.setupProtectedLinkGuards();
        this.setupBackButton();
    },
    
    checkAuthStatus: async function() {
        try {
            const token = localStorage.getItem('auth_token');
            const headers = token ? {'Authorization': `Bearer ${token}`} : {};
            
            const response = await fetch('/api/check-auth', { headers });
            const data = await response.json();
            
            if (data.authenticated) {
                this.setAuthenticated(data.username);
            } else {
                this.setUnauthenticated();
            }
        } catch (error) {
            console.error('Auth check error:', error);
            this.setUnauthenticated();
        }
    },
    
    setAuthenticated: function(username) {
        console.log('User authenticated:', username);
        
        // Update UI
        document.getElementById('userDisplay').style.display = 'inline';
        document.getElementById('currentUser').textContent = `Welcome, ${username}!`;
        const progressBtn = document.getElementById('progressBtn');
        if (progressBtn) progressBtn.style.display = 'inline-block';
        document.getElementById('loginBtn').style.display = 'none';
        document.getElementById('registerBtn').style.display = 'none';
        document.getElementById('logoutBtn').style.display = 'inline-block';
        
        // Store username
        sessionStorage.setItem('username', username);
    },
    
    setUnauthenticated: function() {
        console.log('User not authenticated');
        
        // Update UI
        document.getElementById('userDisplay').style.display = 'none';
        const progressBtn = document.getElementById('progressBtn');
        if (progressBtn) progressBtn.style.display = 'none';
        document.getElementById('loginBtn').style.display = 'inline-block';
        document.getElementById('registerBtn').style.display = 'inline-block';
        document.getElementById('logoutBtn').style.display = 'none';
        
        // Clear stored username
        sessionStorage.removeItem('username');
        localStorage.removeItem('auth_token');
    },
    
    setupAuthUI: function() {
        // Setup logout form to prevent default and clear data
        const logoutForm = document.getElementById('logoutForm');
        if (logoutForm) {
            logoutForm.addEventListener('submit', (e) => {
                localStorage.removeItem('auth_token');
                sessionStorage.removeItem('username');
            });
        }
    },

    setupProtectedLinkGuards: function() {
        const protectedPrefixes = ['/progress', '/quiz'];

        document.addEventListener('click', (e) => {
            const link = e.target && e.target.closest ? e.target.closest('a') : null;
            if (!link) return;

            const href = link.getAttribute('href');
            if (!href || !href.startsWith('/')) return;

            const isProtected = protectedPrefixes.some((p) => href === p || href.startsWith(p + '/'));
            if (!isProtected) return;

            if (!this.isAuthenticated()) {
                e.preventDefault();
                const next = encodeURIComponent(window.location.origin + href);
                window.location.href = `/api/register?next=${next}`;
            }
        });
    },

    setupBackButton: function() {
        const backBtn = document.getElementById('backBtn');
        if (!backBtn) return;

        // Heuristic: hide if there's no prior navigation history.
        if (window.history && typeof window.history.length === 'number' && window.history.length > 1) {
            backBtn.style.display = 'inline-block';
        } else {
            backBtn.style.display = 'none';
        }
    },
    
    logout: async function() {
        try {
            await fetch('/logout', {
                method: 'POST',
                credentials: 'include'
            });
        } catch (e) {
            // ignore
        }

        localStorage.removeItem('auth_token');
        sessionStorage.removeItem('username');
        this.setUnauthenticated();
        window.location.href = '/';
    },
    
    isAuthenticated: function() {
        const token = localStorage.getItem('auth_token');
        const user = sessionStorage.getItem('username');
        return !!(token || user);
    },
    
    getUsername: function() {
        return sessionStorage.getItem('username');
    },
    
    getAuthToken: function() {
        return localStorage.getItem('auth_token');
    }
};

// Initialize auth manager when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => authManager.init());
} else {
    authManager.init();
}
