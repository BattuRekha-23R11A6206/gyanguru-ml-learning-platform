#!/usr/bin/env python3
"""
ML Learning Assistant - Main Flask Application
GyanGuru: AI Powered Learning Assistant for AI & ML
"""

from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for, abort
from flask_cors import CORS
from datetime import datetime
import os
import json
import numpy as np
import time
from werkzeug.utils import secure_filename

# Import utility modules
from utils.genai_utils import GroqAIUtils, get_groq, init_groq
from utils.audio_utils import get_audio, init_audio
from utils.image_utils import get_images, init_images
from utils.code_executor import get_code_executor, init_code_executor
from models.user import ensure_users_file, User
from utils.quiz_utils import init_quiz, get_quiz_system
from utils.hf_utils import init_hf_models, hf_manager
from utils.auth_utils import require_login, generate_token, verify_token, token_required
from utils.sklearn_utils import sklearn_manager
from utils.progress_utils import (
    get_course_progress,
    update_topic_progress,
    get_next_topic,
    get_available_topics,
    reset_user_progress,
    get_module_for_topic,
    get_course_statistics,
    update_quiz_score,
)
import logging
# Configure logging to file
logging.basicConfig(
    filename='flask_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'iichackathon')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force template reloading
app.jinja_env.auto_reload = True  # Force Jinja2 auto-reload
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0  # Disable file caching

# Enable CORS
CORS(app)

# Initialize upload directories
os.makedirs('uploads', exist_ok=True)
os.makedirs('uploads/audio', exist_ok=True)
os.makedirs('uploads/images', exist_ok=True)
os.makedirs('uploads/code', exist_ok=True)

# Initialize user data file
ensure_users_file()

# Initialize utility modules
init_groq() # Automatically loads from GROQ_API_KEY env var
init_audio()
init_images()
init_code_executor()
init_quiz()
init_hf_models()

# Create local instances for easier use and to satisfy static analysis
groq = get_groq() or GroqAIUtils()
audio = get_audio()
images = get_images()
executor = get_code_executor()
quiz_system = get_quiz_system()

# ensure hf_manager and sklearn_manager are available
hf = hf_manager
sklearn_mgr = sklearn_manager

# ============================================
# STATIC FILES SERVING
# ============================================

# Serve uploaded files
@app.route('/uploads/<path:filepath>')
def serve_upload(filepath):
    """Serve uploaded files (audio, images, code)"""
    print(f"📁 Upload request for: {filepath}")
    try:
        full_path = os.path.join('uploads', filepath)
        print(f"📂 Full path: {full_path}")
        print(f"📂 File exists: {os.path.exists(full_path)}")
        if os.path.exists(full_path):
            # Determine MIME type based on file extension
            mimetype = 'application/octet-stream'
            if filepath.lower().endswith('.mp3'):
                mimetype = 'audio/mpeg'
            elif filepath.lower().endswith('.wav'):
                mimetype = 'audio/wav'
            elif filepath.lower().endswith('.png'):
                mimetype = 'image/png'
            elif filepath.lower().endswith('.jpg') or filepath.lower().endswith('.jpeg'):
                mimetype = 'image/jpeg'
            elif filepath.lower().endswith('.py'):
                mimetype = 'text/plain'
            
            # Serve file inline (for playing in browser) not as attachment
            response = send_file(full_path, mimetype=mimetype, as_attachment=False)
            # Add headers for better caching and browser support
            response.headers['Cache-Control'] = 'public, max-age=86400'
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# PAGE ROUTES
# ============================================

@app.route('/')
def index():
    """Home page - Dashboard"""
    features = [
        {
            'title': 'Text Explanations',
            'badge': 'All Levels',
            'description': 'Get comprehensive explanations of any ML concept from basic fundamentals to advanced applications',
            'list_items': [
                {'icon': '✨', 'text': 'Adaptive difficulty levels'},
                {'icon': '🎯', 'text': 'Interactive learning'},
                {'icon': '📚', 'text': 'Comprehensive coverage'}
            ],
            'endpoint': 'text_explanation',
            'btn_text': 'Start Learning',
            'main_icon': '📝',
            'btn_class': 'btn-primary',
            'secondary_btn_text': 'Learn More'
        },
        {
            'title': 'Code Generation',
            'badge': 'Production Ready',
            'description': 'Generate production-ready Python code with automatic dependency detection and best practices',
            'list_items': [
                {'icon': '⚡', 'text': 'Real-time generation'},
                {'icon': '🛡️', 'text': 'Error handling'},
                {'icon': '🏆', 'text': 'Best practices'}
            ],
            'endpoint': 'code_generation',
            'btn_text': 'Generate Code',
            'main_icon': '💻',
            'btn_class': 'btn-success',
            'secondary_btn_text': 'View Examples'
        },
        {
            'title': 'Audio Learning',
            'badge': 'Offline First',
            'description': 'Listen to engaging audio lessons while commuting or during breaks',
            'list_items': [
                {'icon': '🎵', 'text': 'Clear narration'},
                {'icon': '📱', 'text': 'Mobile friendly'},
                {'icon': '⚡', 'text': 'Offline generation'}
            ],
            'endpoint': 'audio_learning',
            'btn_text': 'Listen Now',
            'main_icon': '🎧',
            'btn_class': 'btn-warning',
            'secondary_btn_text': 'Sample Audio'
        },
        {
            'title': 'Visual Diagrams',
            'badge': 'Interactive',
            'description': 'AI-generated visual diagrams and illustrations for better understanding',
            'list_items': [
                {'icon': '🎨', 'text': 'Interactive diagrams'},
                {'icon': '🧠', 'text': 'Visual explanations'},
                {'icon': '🗺️', 'text': 'Concept mapping'}
            ],
            'endpoint': 'image_visualization',
            'btn_text': 'View Diagrams',
            'main_icon': '🎨',
            'btn_class': 'btn-outline',
            'secondary_btn_text': 'See Examples'
        }
    ]

    return render_template('index.html', features=features)

@app.route('/text-explanation')
def text_explanation():
    """Text explanation learning page"""
    return render_template('text_explanation.html')

@app.route('/code-generation')
def code_generation():
    """Code generation learning page"""
    return render_template('code_generation.html')

@app.route('/audio-learning')
def audio_learning():
    """Audio learning page"""
    return render_template('audio_learning.html')

@app.route('/image-visualization')
def image_visualization():
    """Image visualization page"""
    return render_template('image_visualization.html')

@app.route('/settings')
def settings():
    """Settings page"""
    return render_template('settings.html')

@app.route('/about')
def about():
    """About page"""
    return render_template('about.html')

# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.route('/api/register', methods=['GET', 'POST'])
def register():
    """User registration page"""
    if request.method == 'GET':
        return render_template('register.html')
    
    # Handle POST request
    data = request.get_json()
    username = data.get('username', '').strip()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    
    try:
        # Validate input
        if not username or not email or not password:
            return jsonify({'error': 'All fields are required'}), 400
        
        if len(username) < 3 or len(username) > 20:
            return jsonify({'error': 'Username must be 3-20 characters'}), 400
        
        # Create user
        User.create(username, email, password)
        
        return jsonify({'success': True, 'message': 'Account created successfully'}), 201
    
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"[ERROR] Registration error: {str(e)}")
        return jsonify({'error': 'Registration failed'}), 500

@app.route('/api/login', methods=['GET', 'POST'])
def login():
    """User login page"""
    if request.method == 'GET':
        return render_template('login.html')
    
    # Handle POST request
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    try:
        if not username or not password:
            return jsonify({'error': 'Username and password are required'}), 400
        
        user = User.authenticate(username, password)
        
        if not user:
            return jsonify({'error': 'Invalid username or password'}), 401
        
        # Generate JWT token
        token = generate_token(username)
        
        # Store in session
        session['username'] = username
        session.permanent = True  # Make session persist
        
        return jsonify({
            'success': True, 
            'token': token,
            'username': username,
            'message': 'Login successful'
        }), 200
    
    except Exception as e:
        print(f"[ERROR] Login error: {str(e)}")
        return jsonify({'error': 'Login failed'}), 500

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    """User logout"""
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/check-auth', methods=['GET'])
def check_auth():
    """Check if user is authenticated"""
    token = request.headers.get('Authorization')
    username = None
    
    if token:
        try:
            username = verify_token(token.split(" ")[1])
        except:
            pass
    
    if not username and 'username' in session:
        username = session['username']
    
    if username:
        return jsonify({'authenticated': True, 'username': username}), 200
    else:
        return jsonify({'authenticated': False}), 200

@app.route('/api/user-profile', methods=['GET'])
@require_login
def user_profile():
    """Get current user profile"""
    username = getattr(request, 'username', None)
    user = User.get_by_username(username)
    
    if user:
        return jsonify({
            'username': user.username,
            'email': user.email,
            'created_at': user.created_at,
            'last_login': user.last_login
        }), 200
    else:
        return jsonify({'error': 'User not found'}), 404

# ============================================
# API ROUTES - TEXT EXPLANATION
# ============================================

@app.route('/api/topic/<topic_id>', methods=['GET'])
def get_topic_metadata(topic_id):
    """Fetch a topic definition from the course structure by id."""
    try:
        with open('data/course_structure.json', 'r') as f:
            course_data = json.load(f)

        for module in course_data.get('course', {}).get('modules', []):
            for topic in module.get('topics', []):
                if topic.get('id') == topic_id:
                    if not topic.get('content_type'):
                        topic['content_type'] = 'text'
                    return jsonify({
                        'success': True,
                        'topic': topic,
                        'module': {
                            'id': module.get('id'),
                            'title': module.get('title'),
                            'order': module.get('order')
                        }
                    })

        return jsonify({'success': False, 'error': 'Topic not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/topic-next/<topic_id>', methods=['GET'])
def get_next_topic_by_id(topic_id):
    """Get the next topic (in course order) after a given topic_id."""
    try:
        with open('data/course_structure.json', 'r') as f:
            course_data = json.load(f)

        ordered_topics = []
        for module in course_data.get('course', {}).get('modules', []):
            for topic in module.get('topics', []):
                ordered_topics.append({
                    'module': {
                        'id': module.get('id'),
                        'title': module.get('title'),
                        'order': module.get('order'),
                    },
                    'topic': topic,
                })

        current_index = None
        for idx, item in enumerate(ordered_topics):
            if item.get('topic', {}).get('id') == topic_id:
                current_index = idx
                break

        if current_index is None:
            return jsonify({'success': False, 'error': 'Topic not found'}), 404

        next_index = current_index + 1
        if next_index >= len(ordered_topics):
            return jsonify({'success': True, 'has_next': False, 'next_topic': None}), 200

        # Ensure next topic has a content type so the frontend can route correctly
        try:
            next_item = ordered_topics[next_index]
            if next_item.get('topic') and not next_item['topic'].get('content_type'):
                next_item['topic']['content_type'] = 'text'
        except Exception:
            pass

        return jsonify({
            'success': True,
            'has_next': True,
            'next_topic': ordered_topics[next_index],
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate-explanation', methods=['POST'])
def generate_explanation():
    """Generate text explanation for ML topic"""
    print("[INFO] API HIT: /api/generate-explanation")
    try:
        data = request.get_json()
        print(f"[DEBUG] Received data: {data}")
        topic = data.get('topic', '')
        complexity = data.get('complexity', 'Intermediate')
        
        print(f"[DEBUG] Topic: {topic}, Complexity: {complexity}")
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        gemini = get_groq() or GroqAIUtils()
        explanation = gemini.generate_text_explanation(topic, complexity)
        print(f"[INFO] Explanation generated (first 100 chars): {explanation[:100]}...")
        
        return jsonify({
            'success': True,
            'explanation': explanation,
            'topic': topic,
            'complexity': complexity,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"[ERROR] generate_explanation failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# API ROUTES - CODE GENERATION
# ============================================

@app.route('/api/generate-code', methods=['POST'])
def generate_code():
    """Generate Python code for ML concepts"""
    try:
        data = request.get_json()
        algorithm = data.get('algorithm', '')
        complexity = data.get('complexity', 'Detailed')
        
        print(f"🔧 Code generation request: algorithm='{algorithm}', complexity='{complexity}'")
        
        if not algorithm:
            return jsonify({'error': 'Algorithm is required'}), 400
        
        gemini = get_groq() or GroqAIUtils()
        code = gemini.generate_code_example(algorithm, complexity)
        
        print(f"📝 Generated code length: {len(code)} characters")
        print(f"📝 Code preview: {code[:200]}...")
        
        # Detect dependencies
        dependencies = get_code_executor().detect_dependencies(code)
        
        print(f"📦 Dependencies detected: {dependencies}")
        
        # Validate syntax
        is_valid, error = executor.validate_syntax(code)

        # Save code file
        filepath, webpath = executor.save_code_file(code) or (None, None)
        
        return jsonify({
            'success': True,
            'code': code,
            'algorithm': algorithm,
            'complexity': complexity,
            'dependencies': dependencies,
            'is_valid': is_valid,
            'error': error,
            'download_url': webpath,
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"💥 Error in code generation: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/code-execution-guide', methods=['POST'])
def code_execution_guide():
    """Get execution guide for generated code"""
    try:
        data = request.get_json()
        code = data.get('code', '')
        
        if not code:
            return jsonify({'error': 'Code is required'}), 400
        
        executor = get_code_executor()
        dependencies = executor.detect_dependencies(code)
        guide = executor.create_execution_guide(code, dependencies)
        
        # Create Colab notebook
        colab_code = executor.create_colab_notebook(code, "ML Learning Code")
        
        return jsonify({
            'success': True,
            'guide': guide,
            'dependencies': dependencies,
            'colab_code': colab_code
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# API ROUTES - AUDIO GENERATION
# ============================================

@app.route('/api/generate-audio', methods=['POST'])
def generate_audio():
    """Generate audio from text or script"""
    try:
        data = request.get_json()
        text = data.get('text', '')
        topic = data.get('topic', 'lesson')
        audio_type = data.get('type', 'tts')  # 'tts' or 'script'
        
        if not text:
            return jsonify({'error': 'Text content is required'}), 400
        
        audio = get_audio()
        result = None
        
        if audio_type == 'script':
            result = audio.generate_educational_audio(text, topic)
        else:
            result = audio.generate_audio(text)
        
        if result:
            filepath, webpath = result
            filename = os.path.basename(filepath)
            audio_play_url = f'/uploads/audio/{filename}'
            audio_download_url = f'/api/download/audio/{filename}'
            return jsonify({
                'success': True,
                'audio_url': audio_play_url,
                'audio_path': filepath,
                'filename': filename,
                'download_url': audio_download_url,
                'topic': topic,
                'generated_at': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'Failed to generate audio'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate-audio-script', methods=['POST'])
def generate_audio_script():
    """Generate audio script from topic"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        length = data.get('length', 'Medium')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        print(f"🎙️ Generating audio script for: {topic} (Length: {length})")
        
        gemini = get_groq() or GroqAIUtils()
        script = gemini.generate_audio_script(topic, length)
        
        print(f"📝 Script generated, length: {len(script)} characters")
        
        # Generate audio from script
        audio = get_audio()
        audio_result = audio.generate_educational_audio(script, topic)
        
        if audio_result:
            filepath, webpath = audio_result
            filename = os.path.basename(filepath)
            print(f"✅ Audio file created: {filename}")
            
            audio_play_url = f'/api/download/audio/{filename}?mode=play'
            audio_download_url = f'/api/download/audio/{filename}'
            
            return jsonify({
                'success': True,
                'script': script,
                'topic': topic,
                'length': length,
                'audio_url': audio_play_url,
                'filename': filename,
                'download_url': audio_download_url,
                'generated_at': datetime.now().isoformat()
            })
        else:
            print("❌ Audio generation failed")
            return jsonify({
                'success': True,
                'script': script,
                'topic': topic,
                'length': length,
                'audio_url': None,
                'filename': None,
                'message': 'Script generated but audio generation failed',
                'generated_at': datetime.now().isoformat()
            })
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================
# API ROUTES - IMAGE GENERATION
# ============================================

@app.route('/api/generate-image', methods=['POST'])
def generate_image():
    """Generate educational diagram/image"""
    try:
        data = request.get_json()
        concept = data.get('concept', '')
        diagram_type = data.get('diagram_type', 'Conceptual')
        backend = data.get('backend', 'placeholder')
        
        if not concept:
            return jsonify({'error': 'Concept is required'}), 400
        
        print(f"🎨 Generating {diagram_type} diagram for: {concept}")
        
        gemini = get_groq() or GroqAIUtils()
        prompt = gemini.generate_image_prompt(concept, diagram_type)
        
        print(f"📝 Prompt generated for image creation")
        
        images = get_images()
        logging.debug(f"Calling generate_image_from_prompt for {concept}")
        result = images.generate_image_from_prompt(prompt, filename=None, diagram_type=diagram_type, use_api=backend, topic=concept)
        logging.debug(f"Generation result: {result}")
        
        if result:
            filepath, webpath = result
            print(f"✅ Image generated successfully: {diagram_type}")
            return jsonify({
                'success': True,
                'image_url': webpath,
                'concept': concept,
                'diagram_type': diagram_type,
                'prompt': prompt[:200] if len(prompt) > 200 else prompt,
                'generated_at': datetime.now().isoformat()
            })
        else:
            print(f"❌ Image generation failed completely - both API and fallback")
            return jsonify({
                'success': False,
                'error': 'Image generation service unavailable. Please try again later.',
                'concept': concept,
                'diagram_type': diagram_type
            }), 503  # Service Unavailable
    except Exception as e:
        print(f"💥 Error generating image: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500

@app.route('/api/generate-images-multiple', methods=['POST'])
def generate_images_multiple():
    """Generate multiple diverse diagrams for a concept from different perspectives"""
    try:
        data = request.get_json()
        concept = data.get('concept', '')
        count = min(int(data.get('count', 4)), 5)  # Max 5 images
        
        if not concept:
            return jsonify({'error': 'Concept is required'}), 400
        
        print(f"🖼️ Generating {count} diverse diagrams for: {concept}")
        
        gemini = get_groq()
        images_obj = get_images()
        
        # Get diverse perspectives for this topic
        all_perspectives = gemini.get_diverse_perspectives(concept)
        perspectives = all_perspectives[:count]
        
        generated_images = []
        
        for i, (diagram_type, perspective) in enumerate(perspectives):
            perspective_label = f"{perspective.title()}" if perspective else "General"
            print(f"📐 Creating {diagram_type} diagram - {perspective or 'general'} ({i+1}/{count})...")

            # Generate unique prompt for this perspective
            prompt = gemini.generate_image_prompt(concept, diagram_type, perspective)
            result = images_obj.generate_image_from_prompt(prompt, filename=None, diagram_type=diagram_type, topic=concept)

            if result:
                filepath, webpath = result
                generated_images.append({
                    'image_url': webpath,
                    'diagram_type': diagram_type,
                    'perspective': perspective_label,
                    'prompt': prompt[:100] + "..." if len(prompt) > 100 else prompt
                })
                print(f"✅ {diagram_type} ({perspective_label}) diagram generated")
            else:
                print(f"⚠️ {diagram_type} ({perspective_label}) diagram generation failed")
        
        print(f"✅ Generated {len(generated_images)} unique diagrams")
        
        if not generated_images:
            return jsonify({'error': 'Failed to generate images'}), 500

        return jsonify({
            'success': True,
            'images': generated_images,
            'concept': concept,
            'count': len(generated_images),
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        print(f"💥 Error generating multiple images: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============================================
# API ROUTES - RESOURCE MANAGEMENT
# ============================================

@app.route('/api/list-audio-files', methods=['GET'])
def list_audio_files():
    """List all generated audio files"""
    try:
        audio = get_audio()
        files = audio.list_generated_files()
        print(f"📊 Listed {len(files)} audio files")
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        print(f"❌ Error listing files: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/audio/<filename>', methods=['DELETE'])
def delete_audio_file(filename):
    """Delete an audio file"""
    print(f"🗑️ Delete request received for: {filename}")
    try:
        filename = secure_filename(filename)
        print(f"🔒 Secure filename: {filename}")
        filepath = os.path.join('uploads/audio', filename)
        print(f"📁 Full path: {filepath}")
        print(f"📂 File exists: {os.path.exists(filepath)}")
        
        if os.path.exists(filepath):
            os.remove(filepath)
            print(f"✅ File deleted successfully")
            return jsonify({
                'success': True,
                'message': f'Audio file "{filename}" deleted successfully'
            })
        else:
            print(f"❌ File not found")
            return jsonify({'error': 'Audio file not found'}), 404
    except Exception as e:
        print(f"💥 Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-images', methods=['GET'])
def list_images_api():
    """List all generated images"""
    try:
        images = get_images()
        files = images.list_generated_images()
        return jsonify({'success': True, 'images': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/list-code-files', methods=['GET'])
def list_code_files():
    """List all generated code files"""
    try:
        executor = get_code_executor()
        files = executor.list_generated_code_files()
        return jsonify({'success': True, 'files': files})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Audio playback endpoint (serves inline for browser playback)
@app.route('/api/play/audio/<filename>', methods=['GET'])
def play_audio(filename):
    """Play audio file inline in browser"""
    print(f"🎵 Play request for: {filename}")
    try:
        filename = secure_filename(filename)
        print(f"🔒 Secure filename: {filename}")
        filepath = os.path.join('uploads/audio', filename)
        print(f"📁 Full path: {filepath}")
        print(f"📂 File exists: {os.path.exists(filepath)}")
        
        if os.path.exists(filepath):
            print(f"✅ Serving audio file")
            # Serve inline for playback, not as attachment
            response = send_file(
                filepath,
                mimetype='audio/mpeg',
                as_attachment=False
            )
            # Add headers for streaming and caching
            response.headers['Cache-Control'] = 'public, max-age=3600'
            response.headers['Accept-Ranges'] = 'bytes'
            return response
        else:
            print(f"❌ Audio file not found")
            return jsonify({'error': 'Audio file not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/test')
def test():
    return "Server is working!"

@app.route('/api/test-delete', methods=['DELETE'])
def test_delete():
    return jsonify({'success': True, 'message': 'Delete route works'})

@app.route('/api/download/<file_type>/<filename>', methods=['GET'])
def download_file(file_type, filename):
    """Download generated files with proper headers"""
    try:
        filename = secure_filename(filename)
        
        if file_type == 'audio':
            filepath = os.path.join('uploads/audio', filename)
            mimetype = 'audio/mpeg'
        elif file_type == 'image':
            filepath = os.path.join('uploads/images', filename)
            mimetype = 'image/png'
        elif file_type == 'code':
            filepath = os.path.join('uploads/code', filename)
            mimetype = 'text/plain'
        else:
            return jsonify({'error': 'Invalid file type'}), 400
        
        if os.path.exists(filepath):
            # Check if this is for playback or download
            mode = request.args.get('mode', 'download')
            as_attachment = (mode != 'play')
            
            response = send_file(
                filepath,
                mimetype=mimetype,
                as_attachment=as_attachment,
                download_name=filename if as_attachment else None
            )
            
            if as_attachment:
                # Download headers
                response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
                response.headers['Pragma'] = 'no-cache'
                response.headers['Expires'] = '0'
            else:
                # Playback headers -remove attachment header for inline playback
                response.headers['Cache-Control'] = 'public, max-age=3600'
                response.headers['Accept-Ranges'] = 'bytes'
                # Remove Content-Disposition to allow inline playback
                if 'Content-Disposition' in response.headers:
                    del response.headers['Content-Disposition']
            
            return response
        else:
            return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# API ROUTES - COMBINED LEARNING PATH
# ============================================

@app.route('/api/generate-complete-lesson', methods=['POST'])
def generate_complete_lesson():
    """Generate comprehensive lesson with all modalities"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        complexity = data.get('complexity', 'Intermediate')
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        gemini = get_groq()
        
        # Generate all content types
        explanation = gemini.generate_text_explanation(topic, complexity)
        code = gemini.generate_code_example(topic, complexity)
        script = gemini.generate_audio_script(topic, "Medium")
        image_prompt = gemini.generate_image_prompt(topic, "Technical")

        # Process code
        executor = get_code_executor()
        code = executor.sanitize_code(code)
        dependencies = executor.detect_dependencies(code)
        code_valid, code_error = executor.validate_syntax(code)
        code_file = executor.save_code_file(code)
        
        # Generate audio
        audio = get_audio()
        audio_file = audio.generate_educational_audio(script, topic)
        
        # Generate image
        images = get_images()
        image_file = images.generate_image_from_prompt(image_prompt)
        
        return jsonify({
            'success': True,
            'topic': topic,
            'complexity': complexity,
            'explanation': explanation,
            'code': {
                'content': code,
                'dependencies': dependencies,
                'valid': code_valid,
                'download_url': code_file[1] if code_file else None
            },
            'audio': {
                'script': script,
                'download_url': audio_file[1] if audio_file else None,
                'filename': os.path.basename(audio_file[0]) if audio_file else None,
                'api_download_url': f'/api/download/audio/{os.path.basename(audio_file[0])}' if audio_file else None
            },
            'image': {
                'prompt': image_prompt,
                'download_url': image_file[1] if image_file else None
            },
            'generated_at': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# FILE SERVING
# ============================================

@app.route('/uploads/<path:filename>')
def serve_uploads(filename):
    """Serve files from the uploads directory"""
    try:
        filepath = os.path.join('uploads', filename)
        # Convert to absolute path for checking
        abs_filepath = os.path.abspath(filepath)
        abs_uploads = os.path.abspath('uploads')
        
        # Security check: ensure the file is within uploads directory
        if not abs_filepath.startswith(abs_uploads):
            return jsonify({'error': 'Access denied'}), 403
        
        if not os.path.exists(filepath):
            print(f"[WARN] File not found: {filepath} (absolute: {abs_filepath})")
            return jsonify({'error': f'File not found: {filepath}'}), 404
        
        # Determine mimetype based on file extension
        if filename.endswith('.png'):
            mimetype = 'image/png'
        elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
            mimetype = 'image/jpeg'
        elif filename.endswith('.svg'):
            mimetype = 'image/svg+xml'
        elif filename.endswith('.mp3'):
            mimetype = 'audio/mpeg'
        else:
            mimetype = 'application/octet-stream'
        
        return send_file(filepath, mimetype=mimetype)
    except Exception as e:
        print(f"[ERROR] Error serving file: {str(e)}")
        return jsonify({'error': str(e)}), 500

# ============================================
# ERROR HANDLERS
# ============================================

@app.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    """Handle 403 errors"""
    return jsonify({'error': 'Forbidden'}), 403

# ============================================
# API ROUTES - PROGRESS TRACKING
# ============================================

@app.route('/api/course-progress', methods=['GET'])
@require_login
def get_course_progress_api():
    """Get course progress for current user"""
    username = getattr(request, 'username', None)
    if not username:
        return jsonify({'error': 'Login required'}), 401
    progress = get_course_progress(username)
    return jsonify({'success': True, 'progress': progress})

@app.route('/api/progress', methods=['GET'])
def get_dashboard_progress():
    """
    Backwards-compatible progress endpoint used by the home dashboard.

    Attempts to identify the user from session or JWT token. If no user is
    authenticated, returns success=False so the frontend can simply hide
    the dashboard progress UI instead of breaking.
    """
    username = None

    # Session-based auth
    if 'username' in session and session.get('username'):
        username = session.get('username')
    else:
        # JWT-based auth (Authorization header or auth_token cookie)
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers.get('Authorization', '')
            parts = auth_header.split(' ')
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]

        if not token and 'auth_token' in request.cookies:
            token = request.cookies.get('auth_token')

        if token:
            from utils.auth_utils import verify_token  # local import to avoid circular
            username = verify_token(token)

    if not username:
        return jsonify({'success': False, 'error': 'Login required'}), 200

    progress = get_course_progress(username)
    return jsonify({'success': True, 'progress': progress})

@app.route('/api/update-progress', methods=['POST'])
@require_login
def update_progress():
    """Update progress for a topic"""
    username = getattr(request, 'username', None)
    if not username:
        return jsonify({'error': 'Login required'}), 401
    data = request.get_json()
    topic_id = data.get('topic_id')
    completed = data.get('completed', True)
    time_spent = data.get('time_spent', 0)
    modality = data.get('modality')
    event = data.get('event', 'completed' if completed else 'viewed')

    if not topic_id:
        return jsonify({'error': 'Topic ID is required'}), 400

    try:
        progress = update_topic_progress(
            username=username,
            topic_id=topic_id,
            completed=completed,
            time_spent=time_spent,
            modality=modality,
            event=event,
        )

        # Quiz checkpoint: when the user completes a topic, encourage a short quiz
        # so we can adapt the next recommendation.
        quiz_checkpoint = False
        if completed:
            try:
                # Only prompt a checkpoint quiz if the user hasn't already passed
                # a quiz for this topic.
                user_progress = get_course_progress(username)
                score = (user_progress.get('quiz_scores') or {}).get(topic_id)
                
                # Only trigger quiz if the module is completed
                module_id = get_module_for_topic(topic_id)
                if module_id and module_id not in user_progress.get('modules_completed', []):
                    quiz_checkpoint = False
                else:
                    quiz_checkpoint = not (score is not None and float(score) >= 70)
            except Exception:
                quiz_checkpoint = True
        return jsonify({
            'success': True,
            'progress': progress,
            'quiz_checkpoint': quiz_checkpoint,
            'quiz_topic_id': topic_id if quiz_checkpoint else None,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/course-progress', methods=['GET'])
@require_login
def get_course_progress_data():
    """Get user's course progress"""
    try:
        username = getattr(request, 'username', None)
        if not username:
            return jsonify({'error': 'Login required'}), 401
        progress = get_course_progress(username)
        return jsonify({'success': True, 'progress': progress})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/next-topic', methods=['GET'])
@require_login
def get_next_topic_api():
    """Get next recommended topic for user"""
    username = getattr(request, 'username', None)
    if not username:
        return jsonify({'error': 'Login required'}), 401
    next_topic = get_next_topic(username)
    return jsonify({'success': True, 'next_topic': next_topic})

@app.route('/api/available-topics', methods=['GET'])
@require_login
def get_available_topics_api():
    """Get all available topics for user"""
    username = getattr(request, 'username', None)
    if not username:
        return jsonify({'error': 'Login required'}), 401
    available_topics = get_available_topics(username)
    return jsonify({'success': True, 'available_topics': available_topics})

@app.route('/api/reset-progress', methods=['POST'])
@require_login
def reset_progress():
    """Reset user progress"""
    username = getattr(request, 'username', None)
    if not username:
        return jsonify({'error': 'Login required'}), 401
    reset_user_progress(username)
    return jsonify({'success': True, 'message': 'Progress reset successfully'})

@app.route('/api/course-statistics', methods=['GET'])
def course_statistics():
    """Get overall course statistics"""
    stats = get_course_statistics()
    return jsonify({'success': True, 'statistics': stats})

# ============================================
# API ROUTES - ENHANCED QUIZ SYSTEM (Real-time + AI)
# ============================================

@app.route('/api/quiz/generate', methods=['POST'])
@require_login
def generate_realtime_quiz():
    """Generate a real-time quiz using AI"""
    try:
        data = request.get_json()
        topic = data.get('topic', '')
        difficulty = data.get('difficulty', 'Intermediate')
        num_questions = data.get('num_questions', 5)

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        quiz_system = get_quiz_system()
        result = quiz_system.generate_realtime_quiz(topic, difficulty, num_questions)

        if result.get('success'):
            return jsonify(result)
        else:
            return jsonify({'error': result.get('error', 'Quiz generation failed')}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/adaptive', methods=['POST'])
@require_login
def get_adaptive_quiz():
    """Generate an adaptive quiz based on user performance"""
    try:
        username = getattr(request, 'username', None)
        if not username:
            return jsonify({'error': 'Login required'}), 401
        data = request.get_json()
        topic = data.get('topic', '')

        if not topic:
            return jsonify({'error': 'Topic is required'}), 400

        # Get user performance history
        user_progress = get_course_progress(username)
        quiz_history = user_progress.get('quiz_scores', {})

        # Convert quiz history to format expected by analytics
        quiz_results = []
        for topic_name, score in quiz_history.items():
            quiz_results.append({
                'score': score,
                'difficulty': 'Intermediate',  # Default assumption
                'time_taken': 300  # Default 5 minutes
            })

        quiz_system = get_quiz_system()

        # Analyze performance if we have data
        if quiz_results:
            performance_analysis = quiz_system.analyze_quiz_performance(quiz_results)
            if performance_analysis.get('success'):
                adaptive_result = quiz_system.get_adaptive_quiz(
                    performance_analysis.get('analytics', {}),
                    topic
                )
            else:
                # Fallback to regular quiz
                adaptive_result = quiz_system.generate_realtime_quiz(topic, 'Intermediate', 5)
        else:
            # No history, generate standard quiz
            adaptive_result = quiz_system.generate_realtime_quiz(topic, 'Intermediate', 5)

        if adaptive_result.get('success'):
            return jsonify(adaptive_result)
        else:
            return jsonify({'error': adaptive_result.get('error', 'Adaptive quiz generation failed')}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/analytics', methods=['POST'])
@require_login
def analyze_quiz_performance():
    """Analyze quiz performance using ML models"""
    try:
        username = getattr(request, 'username', None)
        if not username:
            return jsonify({'error': 'Login required'}), 401
        data = request.get_json()
        quiz_results = data.get('quiz_results', [])

        if not quiz_results:
            # Get user's quiz history
            user_progress = get_course_progress(username)
            quiz_history = user_progress.get('quiz_scores', {})

            quiz_results = []
            for topic_name, score in quiz_history.items():
                quiz_results.append({
                    'score': score,
                    'difficulty': 'Intermediate',
                    'time_taken': 300
                })

        if not quiz_results:
            return jsonify({
                'success': True,
                'analytics': {
                    'message': 'No quiz data available yet. Complete some quizzes to see analytics!'
                }
            })

        quiz_system = get_quiz_system()
        analysis = quiz_system.analyze_quiz_performance(quiz_results)

        return jsonify(analysis)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/quiz/submit', methods=['POST'])
@require_login
def submit_quiz():
    """Submit quiz answers and get results with AI analysis"""
    try:
        username = getattr(request, 'username', None)
        if not username:
            return jsonify({'error': 'Login required'}), 401
        data = request.get_json()

        quiz_id = data.get('quiz_id')
        answers = data.get('answers', [])
        time_taken = data.get('time_taken', 0)
        topic = data.get('topic', '')

        if not quiz_id or not answers:
            return jsonify({'error': 'Quiz ID and answers are required'}), 400

        quiz_system = get_quiz_system()

        # Get the quiz (either from file or generated)
        quiz_data = quiz_system.quizzes.get(quiz_id)
        if not quiz_data:
            return jsonify({'error': 'Quiz not found'}), 404

        # Calculate score
        questions = quiz_data.get('questions', [])
        correct_answers = 0
        total_questions = len(questions)
        detailed_results = []

        for i, question in enumerate(questions):
            user_answer = answers[i] if i < len(answers) else None
            correct_answer = question.get('correct', 0)

            is_correct = user_answer == correct_answer
            if is_correct:
                correct_answers += 1

            detailed_results.append({
                'question': question.get('question', ''),
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'explanation': question.get('explanation', '')
            })

        score_percentage = (correct_answers / total_questions) * 100 if total_questions > 0 else 0

        # Update user progress
        update_quiz_score(username, topic, score_percentage)

        # Generate AI-powered feedback
        feedback = quiz_system._generate_quiz_feedback(score_percentage, detailed_results, topic)

        result = {
            'success': True,
            'score': score_percentage,
            'correct_answers': correct_answers,
            'total_questions': total_questions,
            'time_taken': time_taken,
            'detailed_results': detailed_results,
            'feedback': feedback,
            'passed': score_percentage >= 70
        }

        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/get-quiz/<topic>', methods=['GET'])
def get_quiz(topic):
    """Get quiz for a specific topic"""
    try:
        quiz = get_quiz_system().get_quiz(topic)
        if not quiz:
            quiz = get_quiz_system().generate_quiz_for_topic(topic)
        
        if quiz:
            return jsonify({'success': True, 'quiz': quiz})
        else:
            return jsonify({'error': 'Could not generate quiz'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/error-teaching', methods=['POST'])
@require_login
def error_teaching():
    """Generate error-based teaching for incorrect answers"""
    try:
        data = request.get_json()
        topic = data.get('topic')
        incorrect_questions = data.get('incorrect_questions')
        
        if not topic or not incorrect_questions:
            return jsonify({'error': 'Topic and incorrect questions are required'}), 400
        
        # Persist a lightweight "error-based learning" signal in progress history
        try:
            username = getattr(request, 'username', None)
            if username:
                # mark as viewed/needs-review without completing topic
                update_topic_progress(
                    username=username,
                    topic_id=str(topic),
                    completed=False,
                    time_spent=0,
                    modality="text",
                    event="error_teaching_requested",
                )
        except Exception:
            pass

        teaching = get_quiz_system().generate_error_based_teaching(topic, incorrect_questions)
        return jsonify({'success': True, 'teaching': teaching})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# PAGE ROUTES - PROGRESS
# ============================================

@app.route('/api/course-modules')
def get_course_modules():
    """
    Get all course modules with progress.

    - If the user is authenticated (via JWT or session), include their progress.
    - If not authenticated, return the course structure with zero progress so
      guests can still browse modules.
    """
    try:
        username = None

        # Try to infer username from session first
        if 'username' in session:
            username = session.get('username')
        else:
            # Try to infer username from JWT token (Authorization header or cookie)
            token = None
            if 'Authorization' in request.headers:
                auth_header = request.headers.get('Authorization', '')
                parts = auth_header.split(' ')
                if len(parts) == 2 and parts[0].lower() == 'bearer':
                    token = parts[1]

            if not token and 'auth_token' in request.cookies:
                token = request.cookies.get('auth_token')

            if token:
                from utils.auth_utils import verify_token  # local import to avoid circulars
                username = verify_token(token)

        # Load course structure
        with open('data/course_structure.json', 'r') as f:
            course_data = json.load(f)

        # Determine which topics are completed for this user (if any)
        completed_topics = set()
        if username:
            try:
                user_progress = get_course_progress(username)
                # Build a set of completed topic IDs from detailed modules structure
                for module in user_progress.get('modules', []):
                    for topic in module.get('topics', []):
                        if topic.get('completed'):
                            completed_topics.add(topic['id'])
            except Exception:
                # If progress lookup fails, fall back to no-completion view
                completed_topics = set()

        # Add progress information to each module
        for module in course_data['course']['modules']:
            module['progress'] = 0
            module['completed_topics'] = 0

            for topic in module['topics']:
                topic_id = topic.get('id')
                is_completed = topic_id in completed_topics
                topic['completed'] = is_completed
                if is_completed:
                    module['completed_topics'] += 1

            if module['topics']:
                module['progress'] = int((module['completed_topics'] / len(module['topics'])) * 100)

        return jsonify({
            'success': True,
            'modules': course_data['course']['modules']
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/progress')
@require_login
def progress_dashboard():
    """Progress dashboard page"""
    return render_template('progress.html')

@app.route('/quiz/<topic>')
@require_login
def quiz_page(topic):
    """Quiz page for a specific topic"""
    username = getattr(request, 'username', None)
    if not username:
        return redirect(url_for('login'))
    progress = get_course_progress(username)
    
    # Inline get_module_for_topic with validation
    with open('data/course_structure.json', 'r') as f:
        course_structure = json.load(f)
    module_id = None
    for module in course_structure["course"]["modules"]:
        for t in module["topics"]:
            if t["id"] == topic:
                module_id = module["id"]
                break
        if module_id:
            break
    if not module_id:
        abort(404)
    
    if module_id and module_id not in progress.get('modules_completed', []):
        return redirect(url_for('progress_dashboard'))
    return render_template('quiz.html', topic=topic)

# ============================================
# API ROUTES - HUGGING FACE INTEGRATION
# ============================================

@app.route('/api/hf/generate', methods=['POST'])
@require_login
def hf_generate():
    """Generate text using Hugging Face models"""
    data = request.get_json()
    prompt = data.get('prompt', '')
    max_length = data.get('max_length', 100)

    if not prompt:
        return jsonify({"error": "Prompt is required"}), 400

    result = hf_manager.generate_text(prompt, max_length)
    return jsonify({"generated_text": result})

@app.route('/api/hf/summarize', methods=['POST'])
@require_login
def hf_summarize():
    """Summarize text using Hugging Face models"""
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "Text is required"}), 400

    result = hf_manager.summarize_text(text)
    return jsonify({"summary": result})

@app.route('/api/hf/answer', methods=['POST'])
@require_login
def hf_answer():
    """Answer questions based on context using Hugging Face models"""
    data = request.get_json()
    question = data.get('question', '')
    context = data.get('context', '')

    if not question or not context:
        return jsonify({"error": "Question and context are required"}), 400

    result = hf_manager.answer_question(question, context)
    return jsonify(result)

@app.route('/api/hf/sentiment', methods=['POST'])
@require_login
def hf_sentiment():
    """Analyze sentiment of text using Hugging Face models"""
    data = request.get_json()
    text = data.get('text', '')

    if not text:
        return jsonify({"error": "Text is required"}), 400

    result = hf_manager.analyze_sentiment(text)
    return jsonify(result)

# ============================================
# API ROUTES - SCIKIT-LEARN INTEGRATION
# ============================================

@app.route('/api/sklearn/train', methods=['POST'])
@require_login
def sklearn_train():
    """Train a scikit-learn model"""
    try:
        data = request.get_json()
        model_type = data.get('model_type')
        X = data.get('X')
        y = data.get('y')

        if not all([model_type, X, y]):
            return jsonify({"error": "model_type, X, and y are required"}), 400

        # Convert to numpy arrays
        X = np.array(X)
        y = np.array(y)

        # Train the model
        result = sklearn_manager.train_model(X, y, model_type)

        # Save the model
        model_name = f"{model_type}_{int(time.time())}"
        model_path = sklearn_manager.save_model(result['model'], model_name)

        return jsonify({
            "model_name": model_name,
            "metrics": result['metrics'],
            "model_path": model_path
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sklearn/predict', methods=['POST'])
@require_login
def sklearn_predict():
    """Make predictions using a trained scikit-learn model"""
    try:
        data = request.get_json()
        model_name = data.get('model_name')
        X = data.get('X')

        if not all([model_name, X]):
            return jsonify({"error": "model_name and X are required"}), 400

        # Load the model
        model = sklearn_manager.load_model(model_name)

        # Make predictions
        X = np.array(X)
        predictions = model.predict(X)

        return jsonify({
            "predictions": predictions.tolist()
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ============================================
# HEALTH CHECK
# ============================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'name': 'ML Learning Assistant',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat()
    })

# ============================================
# MAIN
# ============================================

if __name__ == '__main__':
    port = int(os.getenv('FLASK_PORT', 5000))
    host = '0.0.0.0'
    print(f"\n{'='*60}")
    print(f"🚀 Starting ML Learning Assistant...")
    print(f"🌐 Running on: http://localhost:{port}")
    print(f"🔧 Host: {host}")
    print(f"{'='*60}\n")
    
    app.run(
        debug=os.getenv('FLASK_ENV') == 'development',
        host=host,
        port=port
    )
