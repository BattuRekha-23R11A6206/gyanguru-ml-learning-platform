"""
Code Generation and Execution Module
Handles Python code generation, validation, and execution setup
"""

import os
import ast
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict

class CodeExecutor:
    def __init__(self, output_dir: str = "uploads/code"):
        """
        Initialize code executor
        Args:
            output_dir: Directory to store generated code files
        """
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def sanitize_code(self, code: str) -> str:
        if not code:
            return ""
        code = code.replace('\r\n', '\n')
        lines = code.split('\n')
        out = []
        in_fence = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('```'):
                if not in_fence:
                    in_fence = True
                    continue
                in_fence = False
                continue
            if in_fence:
                out.append(line)
            else:
                out.append(line)
        cleaned = "\n".join(out).strip().lstrip('\ufeff')

        # Remove common leading non-code lines (markdown titles, bold headers, etc.)
        cleaned_lines = cleaned.split('\n')
        while cleaned_lines:
            first = cleaned_lines[0].strip()
            if not first:
                cleaned_lines.pop(0)
                continue
            if first.startswith('#'):
                cleaned_lines.pop(0)
                continue
            if (first.startswith('**') and first.endswith('**')) or (first.startswith('*') and first.endswith('*')):
                cleaned_lines.pop(0)
                continue
            if first.lower() in ('python', 'python code', 'code'):
                cleaned_lines.pop(0)
                continue
            break

        # If there is still a prelude, start at the first likely Python statement
        starters = (
            'import ', 'from ', 'def ', 'class ', '@',
            'if __name__', '"""', "'''", '#!',
        )
        start_idx = None
        for i, ln in enumerate(cleaned_lines):
            s = ln.lstrip()
            if not s:
                continue
            if s.startswith(starters):
                start_idx = i
                break

        if start_idx is not None and start_idx > 0:
            cleaned_lines = cleaned_lines[start_idx:]

        # Strip trailing non-code lines (common when the model appends explanations)
        trailing_markers = (
            '```',
            '---',
            '###',
            '##',
            '# ',
            '**',
            '*',
        )
        while cleaned_lines:
            last = cleaned_lines[-1].strip()
            if not last:
                cleaned_lines.pop()
                continue
            if last.startswith(trailing_markers):
                cleaned_lines.pop()
                continue
            if last.lower().startswith(('explanation', 'note', 'notes', 'output', 'example output', 'usage:')):
                cleaned_lines.pop()
                continue
            break

        # Best-effort: if there's still a SyntaxError due to trailing text, trim until parse works
        # (only trims from the end to avoid removing actual code structure).
        for _ in range(200):
            candidate = "\n".join(cleaned_lines).strip()
            if not candidate:
                return ""
            try:
                ast.parse(candidate)
                return candidate
            except SyntaxError as e:
                # If the error points inside the current text, trim from the end and retry.
                if not cleaned_lines:
                    return candidate
                cleaned_lines.pop()
            except Exception:
                return candidate

        return "\n".join(cleaned_lines).strip()
        
    def save_code_file(self, code: str, filename: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """
        Save generated code to file
        Args:
            code: Python code to save
            filename: Optional custom filename
        Returns:
            Tuple of (file_path, file_url) or None if error
        """
        try:
            code = self.sanitize_code(code)
            if filename is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"code_generated_{timestamp}.py"
            
            filepath = os.path.join(self.output_dir, filename)
            
            # Ensure proper line endings
            code = code.replace('\r\n', '\n')
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(code)
            
            web_path = filepath.replace('\\', '/')
            return filepath, f"/{web_path}"
        except Exception as e:
            print(f"Error saving code file: {str(e)}")
            return None
    
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Python code syntax
        Args:
            code: Python code to validate
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            code = self.sanitize_code(code)
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            error_msg = f"Syntax Error at line {e.lineno}: {e.msg}\n{e.text}"
            return False, error_msg
        except Exception as e:
            return False, str(e)
    
    def detect_dependencies(self, code: str) -> List[str]:
        """
        Detect required Python dependencies from code
        Args:
            code: Python code to analyze
        Returns:
            List of required package names
        """
        dependencies = set()
        
        try:
            code = self.sanitize_code(code)
            tree = ast.parse(code)
            
            # Find all imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name.split('.')[0]
                        if module != '__main__':
                            dependencies.add(module)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        module = node.module.split('.')[0]
                        if module != '__main__':
                            dependencies.add(module)
            
            # Standard library modules to remove
            stdlib = {
                'os', 'sys', 'random', 'math', 'json', 'collections',
                'itertools', 'functools', 're', 'datetime', 'time',
                'pathlib', 'io', 'pickle', 'csv', 'sqlite3', 'unittest',
                'logging', 'argparse', 'subprocess', 'threading', 'multiprocessing',
                'typing', 'abc', 'warnings', 'traceback', 'gc', 'copy',
                'operator', 'string', 'textwrap', 'struct', 'codecs'
            }
            
            # Map common module names to package names
            mapping = {
                'cv2': 'opencv-python',
                'sklearn': 'scikit-learn',
                'PIL': 'Pillow',
                'yaml': 'PyYAML',
                'dotenv': 'python-dotenv',
                'google': 'google-generativeai',
                'gtts': 'gTTS',
                'requests': 'requests',
                'bs4': 'beautifulsoup4',
                'flask': 'Flask',
                'werkzeug': 'werkzeug'
            }
            
            detected = []
            for dep in dependencies:
                if dep not in stdlib:
                    detected.append(mapping.get(dep, dep))
            
            return sorted(list(set(detected)))
        except SyntaxError:
            return []
    
    def create_colab_notebook(self, code: str, title: str = "ML Project",
                            description: str = "") -> str:
        """
        Create notebook-ready code with installation commands
        Args:
            code: Python code
            title: Notebook title
            description: Notebook description
        Returns:
            Code wrapped with installation commands
        """
        dependencies = self.detect_dependencies(code)
        
        # Create enhanced code with setup instructions
        setup_code = f"""'''
{title}
{description}

To run this notebook:
1. Open Google Colab: https://colab.research.google.com
2. Create a new notebook
3. Copy and run the cells below

Required dependencies: {', '.join(dependencies)}
'''

# Install required packages
"""
        
        if dependencies:
            for dep in dependencies:
                setup_code += f"!pip install {dep}\n"
        
        setup_code += f"\n# ============================================\n# {title}\n# ============================================\n\n"
        setup_code += code
        
        return setup_code
    
    def create_jupyter_notebook_json(self, code: str, title: str = "ML Project") -> Dict:
        """
        Create Jupyter notebook JSON format
        Args:
            code: Python code
            title: Notebook title
        Returns:
            Notebook structure as dictionary
        """
        dependencies = self.detect_dependencies(code)
        
        cells = [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [f"# {title}\n", "Auto-generated learning notebook"]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": ["# Install dependencies\n"] + 
                          [f"!pip install {dep}\n" for dep in dependencies]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": code.split('\n')
            }
        ]
        
        notebook = {
            "cells": cells,
            "metadata": {
                "kernelspec": {
                    "display_name": "Python 3",
                    "language": "python",
                    "name": "python3"
                },
                "language_info": {
                    "name": "python",
                    "version": "3.8.0"
                }
            },
            "nbformat": 4,
            "nbformat_minor": 4
        }
        
        return notebook
    
    def add_inline_documentation(self, code: str) -> str:
        """
        Add inline documentation to code
        Args:
            code: Python code
        Returns:
            Code with added comments and docstrings
        """
        lines = code.split('\n')
        documented = []
        
        for line in lines:
            documented.append(line)
            # Add comments for function definitions
            if line.strip().startswith('def '):
                documented.append("    \"\"\"Function implementation\"\"\"")
        
        return '\n'.join(documented)
    
    def create_execution_guide(self, code: str, dependencies: Optional[List[str]] = None) -> str:
        """
        Create step-by-step execution guide
        Args:
            code: Python code
            dependencies: List of dependencies
        Returns:
            Formatted execution guide
        """
        if dependencies is None:
            dependencies = self.detect_dependencies(code)
        
        guide = """
# Execution Guide

## Option 1: Google Colab (Recommended for Beginners)
1. Open: https://colab.research.google.com
2. Create a new notebook
3. Run this cell to install dependencies:
```python
"""
        
        for dep in dependencies:
            guide += f"!pip install {dep}\n"
        
        guide += """```

4. Run this cell with your code:
```python
# Your code here
```

## Option 2: Local Python Environment
Requirements: Python 3.7+

1. Create a virtual environment:
```bash
python -m venv venv
```

2. Activate it:
- Windows: `venv\\Scripts\\activate`
- Mac/Linux: `source venv/bin/activate`

3. Install dependencies:
```bash
"""
        
        guide += "pip install " + " ".join(dependencies)
        
        guide += """
```

4. Save code to file (script.py) and run:
```bash
python script.py
```

## Option 3: Jupyter Notebook
1. Install Jupyter: `pip install jupyter`
2. Start Jupyter: `jupyter notebook`
3. Create a new Python notebook
4. Paste and run the code
"""
        
        return guide
    
    def list_generated_code_files(self) -> List[Dict]:
        """
        List all generated code files
        Returns:
            List of file information dictionaries
        """
        files = []
        try:
            for filename in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, filename)
                if os.path.isfile(filepath) and filename.endswith('.py'):
                    with open(filepath, 'r', encoding='utf-8') as f:
                        code = f.read()
                    
                    files.append({
                        'filename': filename,
                        'path': f"/{filepath.replace(chr(92), '/')}",
                        'dependencies': self.detect_dependencies(code),
                        'created': datetime.fromtimestamp(
                            os.path.getmtime(filepath)
                        ).strftime("%Y-%m-%d %H:%M:%S"),
                        'size': self._get_file_size(filepath)
                    })
        except Exception as e:
            print(f"Error listing code files: {str(e)}")
        
        return sorted(files, key=lambda x: x['created'], reverse=True)
    
    def _get_file_size(self, filepath: str) -> str:
        """Get human-readable file size"""
        try:
            size = os.path.getsize(filepath)
            for unit in ['B', 'KB', 'MB']:
                if size < 1024:
                    return f"{size:.1f} {unit}"
                size /= 1024
            return f"{size:.1f} GB"
        except:
            return "Unknown"

# Create global instance
code_executor = None

def init_code_executor(output_dir: str = "uploads/code"):
    """Initialize the code executor module"""
    global code_executor
    code_executor = CodeExecutor(output_dir)
    return code_executor

def get_code_executor():
    """Get the code executor instance"""
    global code_executor
    if code_executor is None:
        code_executor = CodeExecutor()
    return code_executor
