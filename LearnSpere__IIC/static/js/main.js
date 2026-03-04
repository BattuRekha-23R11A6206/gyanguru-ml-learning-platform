// ML Learning Assistant - Main JavaScript
// Main application initialization and utilities

const MLLearningAssistant = {
    // Application state
    state: {
        isLoggedIn: false,
        currentPage: null,
        theme: 'light'
    },
    
    // Initialize application
    init: function() {
        console.log('ML Learning Assistant initializing...');
        
        // Check health endpoint
        this.checkHealth();
        
        // Load theme preference
        this.loadTheme();
        
        // Setup navigation
        this.setupNavigation();
        
        // Setup global error handling
        this.setupErrorHandling();
        
        console.log('Application initialized successfully');
    },
    
    // Check API health
    checkHealth: async function() {
        try {
            const response = await fetch('/api/health');
            const data = await response.json();
            console.log('API Health:', data);
        } catch (error) {
            console.error('API health check failed:', error);
        }
    },
    
    // Load theme preference
    loadTheme: function() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
    },
    
    // Set application theme
    setTheme: function(theme) {
        document.documentElement.setAttribute('data-theme', theme);
        this.state.theme = theme;
        localStorage.setItem('theme', theme);
    },
    
    // Setup navigation
    setupNavigation: function() {
        const navLinks = document.querySelectorAll('nav a, .nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                const href = link.getAttribute('href');
                if (href && href.startsWith('/')) {
                    this.state.currentPage = href;
                }
            });
        });
    },
    
    // Setup global error handling
    setupErrorHandling: function() {
        window.addEventListener('error', (event) => {
            console.error('Global error:', event.error);
        });
        
        window.addEventListener('unhandledrejection', (event) => {
            console.error('Unhandled promise rejection:', event.reason);
        });
    },
    
    // Utility: Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
    },
    
    // Utility: Format date
    formatDate: function(date) {
        if (typeof date === 'string') {
            date = new Date(date);
        }
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
    },
    
    // Utility: Show notification
    showNotification: function(message, type = 'info', duration = 3000) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        notification.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 1rem;
            background: ${type === 'success' ? '#27ae60' : type === 'error' ? '#e74c3c' : '#3498db'};
            color: white;
            border-radius: 5px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            z-index: 10000;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => notification.remove(), 300);
        }, duration);
    },
    
    // Utility: Debounce function
    debounce: function(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    },
    
    // Utility: API call wrapper
    apiCall: async function(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };
        
        try {
            const response = await fetch(endpoint, { ...defaultOptions, ...options });
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            this.showNotification('Error: ' + error.message, 'error');
            throw error;
        }
    }
};

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(400px);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(400px);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    MLLearningAssistant.init();
});
