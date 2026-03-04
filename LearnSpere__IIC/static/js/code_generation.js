// Code Generation Module
// Handles Python code generation for ML algorithms

const codeGenerationModule = {
    // Initialize variables
    currentCode: null,
    currentDependencies: [],
    currentTopicId: null,
    pageStartTs: null,
    init: function() {
        console.log('Code generation module initialized');
        this.initTopicFromUrl();
        this.attachEventListeners();
    },
    
    attachEventListeners: function() {
        const form = document.getElementById('codeGenerationForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        const copyCodeBtn = document.getElementById('copyCodeBtn');
        if (copyCodeBtn) {
            copyCodeBtn.addEventListener('click', () => this.copyCode());
        }
        
        const downloadCodeBtn = document.getElementById('downloadCodeBtn');
        if (downloadCodeBtn) {
            downloadCodeBtn.addEventListener('click', () => this.downloadCode());
        }
        
        const executionGuideBtn = document.getElementById('executionGuideBtn');
        if (executionGuideBtn) {
            executionGuideBtn.addEventListener('click', () => this.showExecutionGuide());
        }
        
        const colonabBtn = document.getElementById('colonabBtn');
        if (colonabBtn) {
            colonabBtn.addEventListener('click', () => this.openInColab());
        }

        const nextTopicBtn = document.getElementById('nextTopicBtn');
        if (nextTopicBtn) {
            nextTopicBtn.addEventListener('click', () => this.goToNextTopic());
        }
    },
    
    handleFormSubmit: async function(e) {
        e.preventDefault();
        
        const algorithm = document.getElementById('algorithm').value;
        const complexity = document.getElementById('codeComplexity').value;
        
        if (!algorithm.trim()) {
            alert('Please enter an algorithm or concept');
            return;
        }
        
        await this.generateCode(algorithm, complexity);
    },
    
    generateCode: async function(algorithm, complexity) {
        const generateBtn = document.querySelector('#codeGenerationForm button');
        const outputSection = document.getElementById('codeOutputSection');
        const loadingIndicator = document.getElementById('codeLoadingIndicator');
        const codeContent = document.getElementById('codeContent');
        const codeTitle = document.getElementById('codeTitle');
        const dependenciesList = document.getElementById('dependenciesList');
        const nextTopicBtn = document.getElementById('nextTopicBtn');
        
        generateBtn.disabled = true;
        outputSection.style.display = 'block';
        loadingIndicator.style.display = 'block';
        
        try {
            const response = await fetch('/api/generate-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    algorithm: algorithm,
                    complexity: complexity
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                loadingIndicator.style.display = 'none';
                
                codeTitle.textContent = `${data.algorithm} - ${data.complexity}`;
                codeContent.textContent = data.code;
                this.currentCode = data.code;
                this.currentDependencies = data.dependencies;
                // Removed auto-progress tracking
                
                // Display dependencies
                dependenciesList.innerHTML = '';
                if (data.dependencies && data.dependencies.length > 0) {
                    data.dependencies.forEach(dep => {
                        const badge = document.createElement('span');
                        badge.className = 'dependency-badge';
                        badge.textContent = dep;
                        dependenciesList.appendChild(badge);
                    });
                } else {
                    dependenciesList.textContent = 'Only standard library';
                }
                
                // Show validity status
                if (!data.is_valid) {
                    const errorMsg = document.createElement('div');
                    errorMsg.style.background = '#f8d7da';
                    errorMsg.style.color = '#721c24';
                    errorMsg.style.padding = '1rem';
                    errorMsg.style.marginBottom = '1rem';
                    errorMsg.style.borderRadius = '5px';
                    errorMsg.textContent = 'Warning: ' + data.error;
                    codeContent.parentElement.insertBefore(errorMsg, codeContent);
                }

                // Show "Mark as Complete" button instead of automatically showing next topic
                this.showMarkCompleteButton();
            } else {
                throw new Error(data.error || 'Failed to generate code');
            }
        } catch (error) {
            console.error('Error:', error);
            loadingIndicator.style.display = 'none';
            codeContent.textContent = 'Error: ' + error.message;
        } finally {
            generateBtn.disabled = false;
        }
    },

    initTopicFromUrl: async function() {
        const params = new URLSearchParams(window.location.search);
        const topicId = params.get('topic');
        this.currentTopicId = topicId;
        this.pageStartTs = Date.now();

        const nextTopicBtn = document.getElementById('nextTopicBtn');
        if (nextTopicBtn) nextTopicBtn.style.display = topicId ? 'inline-block' : 'none';

        if (!topicId) return;

        try {
            const resp = await fetch(`/api/topic/${encodeURIComponent(topicId)}`);
            const data = await resp.json();
            if (data.success && data.topic && data.topic.title) {
                const algoInput = document.getElementById('algorithm');
                if (algoInput) algoInput.value = data.topic.title;
            }
        } catch (e) {
            // non-fatal
        }
    },

    goToNextTopic: async function() {
        if (!this.currentTopicId) return;

        try {
            const resp = await fetch(`/api/topic-next/${encodeURIComponent(this.currentTopicId)}`);
            const data = await resp.json();

            if (!data.success || !data.has_next || !data.next_topic || !data.next_topic.topic) {
                alert('No next topic available.');
                return;
            }

            const nextTopic = data.next_topic.topic;
            const contentType = nextTopic.content_type || 'text';
            const routes = {
                text: '/text-explanation',
                code: '/code-generation',
                audio: '/audio-learning',
                image: '/image-visualization'
            };

            const route = routes[contentType] || '/text-explanation';
            window.location.href = `${route}?topic=${encodeURIComponent(nextTopic.id)}`;
        } catch (e) {
            alert('Failed to load next topic.');
        }
    },

    trackProgress: async function(modality) {
        if (!this.currentTopicId) return;
        const token = localStorage.getItem('auth_token');
        const headers = token ? { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } : { 'Content-Type': 'application/json' };
        const minutes = Math.max(0, Math.round((Date.now() - (this.pageStartTs || Date.now())) / 60000));

        try {
            const resp = await fetch('/api/update-progress', {
                method: 'POST',
                headers,
                body: JSON.stringify({
                    topic_id: this.currentTopicId,
                    completed: true,
                    time_spent: minutes,
                    modality,
                    event: 'generated'
                })
            });

            try {
                const data = await resp.json();
                // Removed auto-navigation to quiz
            } catch (e) {
                // ignore
            }
        } catch (e) {
            // non-fatal
        }
    },
    
    showMarkCompleteButton: function() {
        const outputSection = document.getElementById('codeOutputSection');
        if (!outputSection) {
            console.error('Output section not found');
            return;
        }

        // Check if the button already exists
        let markCompleteBtn = document.getElementById('markCompleteBtn');
        
        if (!markCompleteBtn) {
            // Create the button if it doesn't exist
            markCompleteBtn = document.createElement('button');
            markCompleteBtn.id = 'markCompleteBtn';
            markCompleteBtn.textContent = 'Mark as Complete';
            markCompleteBtn.className = 'btn btn-primary mt-3';
            markCompleteBtn.onclick = () => this.markAsComplete();

            // Create a container for the button
            const buttonContainer = document.createElement('div');
            buttonContainer.className = 'text-center mt-3';
            buttonContainer.appendChild(markCompleteBtn);

            // Add the button after the code content
            const codeContent = document.getElementById('codeContent');
            if (codeContent) {
                // Insert after the code content
                const parent = codeContent.parentNode;
                if (parent && parent.parentNode) {
                    parent.parentNode.insertBefore(buttonContainer, parent.nextSibling);
                } else {
                    outputSection.appendChild(buttonContainer);
                }
            } else {
                outputSection.appendChild(buttonContainer);
            }
        }
        
        // Make sure the button is visible
        markCompleteBtn.style.display = 'inline-block';
    },

    markAsComplete: async function() {
        if (!this.currentTopicId) return;
        
        try {
            await this.trackProgress('code');
            // Hide the mark complete button and show next topic button
            document.getElementById('markCompleteBtn').style.display = 'none';
            const nextTopicBtn = document.getElementById('nextTopicBtn');
            if (nextTopicBtn) nextTopicBtn.style.display = 'inline-block';
        } catch (error) {
            console.error('Error marking as complete:', error);
            alert('Error updating progress. Please try again.');
        }
    },

    copyCode: function() {
        if (!this.currentCode) {
            alert('No code to copy');
            return;
        }
        
        navigator.clipboard.writeText(this.currentCode).then(() => {
            alert('Code copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy:', err);
            alert('Failed to copy to clipboard');
        });
    },
    
    downloadCode: function() {
        if (!this.currentCode) {
            alert('No code to download');
            return;
        }
        
        const element = document.createElement('a');
        element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(this.currentCode));
        element.setAttribute('download', 'ml_algorithm.py');
        element.style.display = 'none';
        document.body.appendChild(element);
        element.click();
        document.body.removeChild(element);
    },
    
    showExecutionGuide: async function() {
        if (!this.currentCode) {
            alert('No code to get guide for');
            return;
        }
        
        const guideSection = document.getElementById('executionGuideSection');
        const guideContent = document.getElementById('guideContent');
        
        try {
            const response = await fetch('/api/code-execution-guide', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    code: this.currentCode
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                guideContent.textContent = data.guide;
                guideSection.style.display = 'block';
                guideSection.scrollIntoView({ behavior: 'smooth' });
            } else {
                alert('Error: ' + (data.error || 'Failed to generate guide'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error: ' + error.message);
        }
    },
    
    openInColab: async function() {
        if (!this.currentCode) {
            alert('No code to open');
            return;
        }
        
        try {
            const response = await fetch('/api/code-execution-guide', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    code: this.currentCode
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                const colonabUrl = 'https://colab.research.google.com/notebook';
                alert('Colab code:\n\n' + data.colab_code + '\n\nOpen Google Colab and paste this code.');
                // In a real implementation, you would create a Colab notebook
                window.open(colonabUrl, '_blank');
            }
        } catch (error) {
            console.error('Error:', error);
            alert('Error: ' + error.message);
        }
    },
    
    currentCode: null,
    currentDependencies: [],
    currentTopicId: null,
    pageStartTs: null
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    codeGenerationModule.init();
});
