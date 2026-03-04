// Audio Learning Module
// Handles text-to-speech and audio lesson generation

const audioLearningModule = {
    init: function() {
        console.log('Audio learning module initialized');
        this.initTopicFromUrl();
        this.attachEventListeners();
        this.loadRecentAudios();
        this.isReading = false;
        
        // Stop audio when leaving the page
        window.addEventListener('beforeunload', () => this.stopReading());
    },
    
    attachEventListeners: function() {
        const form = document.getElementById('audioForm');
        if (form) {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        }
        
        const downloadAudioBtn = document.getElementById('downloadAudioBtn');
        if (downloadAudioBtn) {
            downloadAudioBtn.addEventListener('click', () => this.downloadAudio());
        }
        
        const copyTranscriptBtn = document.getElementById('copyTranscriptBtn');
        if (copyTranscriptBtn) {
            copyTranscriptBtn.addEventListener('click', () => this.copyTranscript());
        }

        const nextTopicBtn = document.getElementById('nextTopicBtn');
        if (nextTopicBtn) {
            nextTopicBtn.addEventListener('click', () => this.goToNextTopic());
        }
    },
    
    handleFormSubmit: async function(e) {
        e.preventDefault();
        
        if (this.isReading) {
            this.stopReading();
            return;
        }
        
        const topic = document.getElementById('audioTopic').value;
        const length = document.getElementById('audioLength').value;
        
        if (!topic.trim()) {
            alert('Please enter a topic');
            return;
        }
        
        await this.generateAudio(topic, length);
    },
    
    generateAudio: async function(topic, length) {
        const generateBtn = document.querySelector('#audioForm button');
        const outputSection = document.getElementById('audioOutputSection');
        const loadingIndicator = document.getElementById('audioLoadingIndicator');
        const audioSource = document.getElementById('audioSource');
        const transcriptContent = document.getElementById('transcriptContent');
        const nextTopicBtn = document.getElementById('nextTopicBtn');
        const audioPlayer = document.getElementById('audioPlayer');
        
        generateBtn.disabled = true;
        outputSection.style.display = 'block';
        loadingIndicator.style.display = 'block';
        
        try {
            const response = await fetch('/api/generate-audio-script', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    topic: topic,
                    length: length
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                loadingIndicator.style.display = 'none';
                
                this.currentScript = data.script;
                transcriptContent.textContent = data.script;
                
                if (data.audio_url) {
                    audioSource.src = data.audio_url;
                    audioPlayer.load();
                    audioPlayer.play();
                    this.isReading = true;
                    generateBtn.textContent = 'Stop Reading';
                    
                    // Reset when audio ends
                    audioPlayer.addEventListener('ended', () => {
                        this.isReading = false;
                        generateBtn.textContent = 'Generate Audio Lesson';
                    }, { once: true });
                }
                
                this.loadRecentAudios();
                // Removed auto-progress tracking
                // Show "Mark as Complete" button instead of automatically showing next topic
                this.showMarkCompleteButton();
            } else {
                throw new Error(data.error || 'Failed to generate audio');
            }
        } catch (error) {
            console.error('Error:', error);
            loadingIndicator.style.display = 'none';
            transcriptContent.textContent = 'Error: ' + error.message;
        } finally {
            generateBtn.disabled = false;
        }
    },

    stopReading: function() {
        const audioPlayer = document.getElementById('audioPlayer');
        const generateBtn = document.querySelector('#audioForm button');
        
        if (audioPlayer) {
            audioPlayer.pause();
            audioPlayer.currentTime = 0;
        }
        this.isReading = false;
        generateBtn.textContent = 'Generate Audio Lesson';
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
                const input = document.getElementById('audioTopic');
                if (input) input.value = data.topic.title;
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
        const outputSection = document.getElementById('audioOutputSection');
        let markCompleteBtn = document.getElementById('markCompleteBtn');
        if (!markCompleteBtn) {
            markCompleteBtn = document.createElement('button');
            markCompleteBtn.id = 'markCompleteBtn';
            markCompleteBtn.textContent = 'Mark as Complete';
            markCompleteBtn.className = 'btn-primary';
            markCompleteBtn.onclick = () => this.markAsComplete();
            outputSection.appendChild(markCompleteBtn);
        }
        markCompleteBtn.style.display = 'inline-block';
    },

    markAsComplete: async function() {
        if (!this.currentTopicId) return;
        
        try {
            await this.trackProgress('audio');
            // Hide the mark complete button and show next topic button
            document.getElementById('markCompleteBtn').style.display = 'none';
            const nextTopicBtn = document.getElementById('nextTopicBtn');
            if (nextTopicBtn) nextTopicBtn.style.display = 'inline-block';
        } catch (error) {
            console.error('Error marking as complete:', error);
            alert('Error updating progress. Please try again.');
        }
    },

    downloadAudio: function() {
        const audioPlayer = document.getElementById('audioPlayer');
        const audioSource = audioPlayer.querySelector('source');
        
        if (!audioSource.src) {
            alert('No audio to download');
            return;
        }
        
        const a = document.createElement('a');
        a.href = audioSource.src;
        a.download = 'lesson.mp3';
        a.style.display = 'none';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    },
    
    copyTranscript: function() {
        if (!this.currentScript) {
            alert('No transcript to copy');
            return;
        }
        
        navigator.clipboard.writeText(this.currentScript).then(() => {
            alert('Transcript copied to clipboard!');
        }).catch(err => {
            console.error('Failed to copy:', err);
        });
    },
    
    loadRecentAudios: async function() {
        try {
            const response = await fetch('/api/list-audio-files');
            const data = await response.json();
            
            if (data.success && data.files && data.files.length > 0) {
                const audioList = document.getElementById('audioList');
                audioList.innerHTML = '';
                
                data.files.slice(0, 5).forEach(file => {
                    const item = document.createElement('div');
                    item.className = 'audio-item';
                    item.innerHTML = `
                        <h4>${file.filename}</h4>
                        <p>Size: ${file.size}</p>
                        <p>Created: ${file.created}</p>
                        <audio controls style="width: 100%; margin-top: 0.5rem;">
                            <source src="${file.path}" type="audio/mpeg">
                        </audio>
                    `;
                    audioList.appendChild(item);
                });
            }
        } catch (error) {
            console.error('Error loading recent audios:', error);
        }
    },
    
    currentScript: null,
    currentTopicId: null,
    pageStartTs: null
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    audioLearningModule.init();
});
