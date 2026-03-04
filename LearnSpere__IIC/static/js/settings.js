// Settings Module
// Handles user preferences and application settings

const settingsModule = {
    init: function() {
        console.log('Settings module initialized');
        this.loadSettings();
        this.attachEventListeners();
    },
    
    loadSettings: function() {
        const savedSettings = localStorage.getItem('appSettings');
        if (savedSettings) {
            this.settings = JSON.parse(savedSettings);
        } else {
            this.settings = this.getDefaultSettings();
        }
        this.displaySettings();
    },
    
    getDefaultSettings: function() {
        return {
            username: 'ML Student',
            theme: 'light',
            language: 'en',
            audioSpeed: '1.0',
            autoplay: false,
            notifications: true,
            dataSaving: false
        };
    },
    
    displaySettings: function() {
        if (document.getElementById('username')) {
            document.getElementById('username').value = this.settings.username;
        }
        if (document.getElementById('theme')) {
            document.getElementById('theme').value = this.settings.theme;
        }
        if (document.getElementById('language')) {
            document.getElementById('language').value = this.settings.language;
        }
    },
    
    attachEventListeners: function() {
        const form = document.getElementById('settingsForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
    },
    
    handleFormSubmit: function(e) {
        e.preventDefault();
        
        this.settings.username = document.getElementById('username').value;
        this.settings.theme = document.getElementById('theme').value;
        this.settings.language = document.getElementById('language').value;
        
        this.saveSettings();
    },
    
    saveSettings: function() {
        localStorage.setItem('appSettings', JSON.stringify(this.settings));
        alert('Settings saved successfully!');
        console.log('Settings saved:', this.settings);
    },
    
    getSetting: function(key) {
        return this.settings[key];
    },
    
    setSetting: function(key, value) {
        this.settings[key] = value;
        this.saveSettings();
    },
    
    settings: null
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    settingsModule.init();
});
