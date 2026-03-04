# Installation Guide

## ML Learning Assistant

This guide will help you set up the ML Learning Assistant project.

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Virtual environment (recommended)

### Steps

1. **Clone the repository** (if applicable)
   ```bash
   git clone <repository-url>
   cd ML_LEARNING_ASSISTANT
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env file with your settings
   ```

6. **Run the application**
   ```bash
   python app.py
   ```

7. **Access the application**
   Open your browser and navigate to `http://localhost:5000`

### Project Structure

```
ML_LEARNING_ASSISTANT/
├── static/
│   ├── css/
│   │   └── style.css
│   ├── images/
│   └── js/
│       ├── audio_learning.js
│       ├── code_generation.js
│       ├── image_visualization.js
│       ├── main.js
│       ├── settings.js
│       └── text_explanation.js
├── templates/
│   ├── 404.html
│   ├── 500.html
│   ├── about.html
│   ├── audio_learning.html
│   ├── base.html
│   ├── code_generation.html
│   ├── image_visualization.html
│   ├── index.html
│   ├── settings.html
│   └── text_explanation.html
├── uploads/
├── utils/
├── app.py
├── .env
├── .gitignore
├── CHANGELOG.md
└── INSTALLATION.md
```

### Troubleshooting

- Make sure you're using Python 3.8 or higher
- Ensure the virtual environment is activated
- Check that all dependencies are installed with `pip list`

### Support

For issues or questions, please contact the development team.
