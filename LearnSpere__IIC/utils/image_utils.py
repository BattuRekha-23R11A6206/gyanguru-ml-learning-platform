"""
Image Generation and Processing Module
Handles creation of educational diagrams and visual content
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, List, Dict
import base64
from io import BytesIO
import requests
import random

try:
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

class ImageUtils:
    def __init__(self, output_dir: str = "uploads/images"):
        """
        Initialize image utilities
        Args:
            output_dir: Directory to store generated images
        """
        self.output_dir = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

    def _unique_stamp(self) -> str:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        return f"{ts}_{random.randint(1000, 9999)}"
        
    def generate_image_from_prompt(self, prompt: str, filename: Optional[str] = None,
                                  diagram_type: str = "Conceptual", use_api: str = "gemini",
                                  topic: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """
        Main entry point for generating images/diagrams.
        Tries Pollinations AI first, then falls back to enhanced programmatic diagrams.
        """
        try:
            print(f"DEBUG: Entering generate_image_from_prompt")
            print(f"DEBUG: Argument prompt='{prompt[:30]}...'")
            print(f"DEBUG: Argument topic='{topic}'")
            
            # If topic isn't provided, try to extract a clean one from the prompt
            if not topic:
                prefixes = [
                    "create a clear, detailed infographic about ",
                    "create a clear, detailed infographic for ",
                    "a technical diagram illustrating ",
                    "a process flowchart for ",
                    "concept: ",
                    "diagram of "
                ]
                topic_candidate = prompt.strip()
                for prefix in prefixes:
                    if topic_candidate.lower().startswith(prefix):
                        topic_candidate = topic_candidate[len(prefix):].strip()
                        break
                
                # Further cleaning
                topic = topic_candidate.split(':')[0].strip() if ':' in topic_candidate else topic_candidate.strip()
                topic = topic.split('\n')[0].strip()
                
                # Final length check - if still too long (e.g. prompt didn't match prefix), 
                # take first few words to avoid "Create a clear,"
                if len(topic) > 40:
                    topic = " ".join(topic.split()[:4])
            
            print(f"Creating {diagram_type} diagram for clean topic: {topic}")
            
            # Step 1: Extract aspects using the clean topic
            aspects = self._extract_topic_aspects(topic)
            print(f"Extracted aspects for uniqueness: {aspects}")
            
            # Step 2: Try real AI generation using Pollinations
            print("Attempting AI image generation via Pollinations...")
            result = self._generate_with_pollinations(prompt, filename)
            
            if result:
                print(f"AI diagram generated successfully via Pollinations")
                return result
            
            # Step 3: Fallback to local programmatic diagrams if AI fails
            print(f"AI generation failed, falling back to enhanced programmatic: {topic} ({diagram_type})")
            result = self._generate_enhanced_fallback(topic, filename, aspects, diagram_type)
            
            if result:
                print(f"Enhanced programmatic {diagram_type} diagram created as fallback")
                return result
            else:
                # Default to smart placeholder diagram generation
                return self._generate_placeholder_diagram(prompt, filename, diagram_type, variation)
        except Exception as e:
            print(f"Error generating image: {str(e)}")
            return None

    def _generate_svg_placeholder(self, prompt: str, filename: Optional[str] = None) -> Optional[Tuple[str, str]]:
        try:
            if filename is None:
                filename = f"diagram_generated_{self._unique_stamp()}.svg"
            if not filename.lower().endswith('.svg'):
                filename = os.path.splitext(filename)[0] + '.svg'

            filepath = os.path.join(self.output_dir, filename)
            title = (prompt or "Concept Visualization").strip().replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            if len(title) > 80:
                title = title[:77] + '...'

            svg = f"""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"900\" height=\"500\" viewBox=\"0 0 900 500\">
  <rect x=\"0\" y=\"0\" width=\"900\" height=\"500\" fill=\"#ffffff\"/>
  <rect x=\"40\" y=\"40\" width=\"820\" height=\"420\" rx=\"18\" fill=\"#f8f9fa\" stroke=\"#667eea\" stroke-width=\"3\"/>
  <text x=\"450\" y=\"120\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"26\" fill=\"#333\">ML Concept Diagram</text>
  <text x=\"450\" y=\"190\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"18\" fill=\"#555\">{title}</text>
  <circle cx=\"250\" cy=\"320\" r=\"55\" fill=\"#667eea\" opacity=\"0.85\"/>
  <circle cx=\"450\" cy=\"320\" r=\"55\" fill=\"#764ba2\" opacity=\"0.85\"/>
  <circle cx=\"650\" cy=\"320\" r=\"55\" fill=\"#28a745\" opacity=\"0.85\"/>
  <line x1=\"305\" y1=\"320\" x2=\"395\" y2=\"320\" stroke=\"#999\" stroke-width=\"3\"/>
  <line x1=\"505\" y1=\"320\" x2=\"595\" y2=\"320\" stroke=\"#999\" stroke-width=\"3\"/>
  <text x=\"250\" y=\"326\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"14\" fill=\"#fff\">Input</text>
  <text x=\"450\" y=\"326\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"14\" fill=\"#fff\">Model</text>
  <text x=\"650\" y=\"326\" text-anchor=\"middle\" font-family=\"Arial\" font-size=\"14\" fill=\"#fff\">Output</text>
</svg>"""

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(svg)

            web_path = filepath.replace('\\', '/')
            return filepath, f"/{web_path}"
        except Exception as e:
            print(f"Error generating SVG diagram: {str(e)}")
            return None
    
    def _generate_with_stable_diffusion(self, prompt: str, filename: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """
        Generate image using Stable Diffusion via HuggingFace
        Requires HF_TOKEN environment variable
        """
        try:
            hf_token = os.getenv('HUGGINGFACE_API_KEY', '').strip()
            
            # Check if token is valid (not placeholder or empty)
            if not hf_token or len(hf_token) < 10:
                print("[ERROR] HUGGINGFACE_API_KEY not set or is invalid for Stable Diffusion")
                print("   Get your token from: https://huggingface.co/settings/tokens")
                print("   Set the HUGGINGFACE_API_KEY environment variable")
                return None
                
        except Exception as e:
            print(f"Error in image generation: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _extract_topic_aspects(self, prompt: str) -> List[str]:
        """
        Extract 4 key aspects from a prompt to use as labels in fallback diagrams
        """
        try:
            from utils.genai_utils import get_groq
            groq = get_groq()
            query = f"Provide 4 short (1-2 words) technical sub-topics or components for the topic: {prompt}. Return only the labels separated by commas."
            response = groq.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": query}]
            )
            labels = response.choices[0].message.content.split(',')
            return [l.strip() for l in labels if l.strip()][:4]
        except:
            # High quality fallbacks
            return ["Core Architecture", "Data Flow", "Key Logic", "Implementation"]

    def _generate_enhanced_fallback(self, topic: str, filename: Optional[str], aspects: List[str], diagram_type: str = "Conceptual") -> Optional[Tuple[str, str]]:
        """
        Choose the best programmatic diagram based on topic, diagram_type, and aspects
        """
        topic_lower = topic.lower()
        
        # Route based on diagram type first, then topic for finer control
        if diagram_type == "Flowchart":
            # All topics can have flowcharts
            return self._create_flowchart_diagram(topic, filename, aspects)
        elif diagram_type == "Technical":
            # Create technical detailed diagrams
            if "neural" in topic_lower or "network" in topic_lower:
                return self._create_technical_neural_diagram(topic, filename, aspects)
            elif "decision" in topic_lower or "tree" in topic_lower:
                return self._create_technical_decision_tree_diagram(topic, filename, aspects)
            else:
                return self._create_technical_overview_diagram(topic, filename, aspects)
        else:  # "Conceptual" or default
            # Topic-specific visualizations
            if "neural" in topic_lower or "network" in topic_lower:
                return self._create_enhanced_neural_diagram(topic, filename, aspects)
            elif "decision" in topic_lower or "tree" in topic_lower:
                return self._create_enhanced_decision_tree_diagram(topic, filename, aspects)
            elif "support vector" in topic_lower or "svm" in topic_lower:
                return self._create_enhanced_svm_diagram(topic, filename, aspects)
            elif "regression" in topic_lower or "linear" in topic_lower:
                return self._create_enhanced_regression_diagram(topic, filename, aspects)
            elif "clustering" in topic_lower or "k-means" in topic_lower:
                return self._create_enhanced_clustering_diagram(topic, filename, aspects)
            elif "pca" in topic_lower or "principal" in topic_lower:
                return self._create_enhanced_pca_diagram(topic, filename, aspects)
            else:
                return self._create_enhanced_conceptual_diagram(topic, filename, aspects)

    def _generate_with_pollinations(self, prompt: str, filename: Optional[str] = None) -> Optional[Tuple[str, str]]:
        """
        Generate image using Pollinations.ai API
        """
        try:
            clean_prompt = "".join(c if c.isalnum() or c in " -_" else " " for c in prompt)
            style = "high quality educational infographic, clean white background, logical layout, professional illustration, 4k"
            encoded_prompt = requests.utils.quote(f"{clean_prompt.strip()} {style}")
            url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&nologo=true"
            
            print(f"Fetching from Pollinations: {url[:80]}...")
            response = requests.get(url, timeout=30)
            
            if response.status_code == 200:
                if filename is None:
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"ai_diagram_{timestamp}.png"
                
                filepath = os.path.join(self.output_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                print(f"[SUCCESS] Image saved to: {filepath}")
                web_path = filepath.replace('\\', '/')
                return filepath, f"/{web_path}"
            
            elif response.status_code == 503:
                print(f"[ERROR] Stable Diffusion model is loading (503 error). Try again in a moment.")
                try:
                    error_data = response.json()
                    if 'estimated_time' in error_data:
                        print(f"   Estimated reload time: {error_data['estimated_time']} seconds")
                except:
                    pass
                return None
            
            elif response.status_code == 401:
                print(f"[ERROR] Authentication failed (401). Invalid HUGGINGFACE_API_KEY.")
                return None
            
            elif response.status_code == 429:
                print(f"[ERROR] Rate limited (429). Too many requests. Please wait.")
                return None
            
            else:
                print(f"[ERROR] Stable Diffusion API error ({response.status_code}): {response.text[:200]}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"[ERROR] Stable Diffusion request timed out (30 seconds). Model may be slow to respond.")
            return None
        except:
            return None

    def _create_enhanced_neural_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create a detailed neural network visualization"""
        try:
            img = Image.new('RGB', (1000, 700), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((350, 30), f"Neural Network Architecture: {topic[:25]}", fill='#1a202c', font=None)
            
            # Draw network layers
            layers = [
                {'name': 'Input Layer', 'neurons': 4, 'x': 100},
                {'name': 'Hidden Layer 1', 'neurons': 6, 'x': 300},
                {'name': 'Hidden Layer 2', 'neurons': 5, 'x': 500},
                {'name': 'Output Layer', 'neurons': 3, 'x': 700}
            ]
            
            neuron_radius = 15
            layer_height = 500
            start_y = 150
            
            # Draw connections between layers
            for i in range(len(layers) - 1):
                current_layer = layers[i]
                next_layer = layers[i + 1]
                
                current_neurons = current_layer['neurons']
                next_neurons = next_layer['neurons']
                current_spacing = layer_height / current_neurons
                next_spacing = layer_height / next_neurons
                
                for j in range(current_neurons):
                    for k in range(next_neurons):
                        y1 = start_y + j * current_spacing
                        y2 = start_y + k * next_spacing
                        draw.line([current_layer['x'] + 30, y1, next_layer['x'] - 30, y2], 
                                fill='#cbd5e1', width=1)
            
            # Draw neurons
            colors = ['#3b82f6', '#8b5cf6', '#ec4899', '#f97316']
            for layer_idx, layer in enumerate(layers):
                spacing = layer_height / layer['neurons']
                for j in range(layer['neurons']):
                    y = start_y + j * spacing
                    # Draw neuron circle
                    draw.ellipse([layer['x'] - neuron_radius, y - neuron_radius,
                                layer['x'] + neuron_radius, y + neuron_radius],
                               fill=colors[layer_idx % len(colors)], outline='#1a202c', width=2)
            
            # Draw layer labels
            for layer in layers:
                draw.text((layer['x'] - 40, start_y + layer_height + 30), layer['name'], 
                        fill='#1a202c', font=None)
            
            # Add legend
            legend_y = 670
            draw.text((50, legend_y), "-> Weight connections between neurons", fill='#666666', font=None)
            draw.ellipse([45, legend_y - 8, 55, legend_y + 2], fill='#3b82f6')
            draw.text((300, legend_y), "* Neurons | Data flows left to right (Input -> Output)", fill='#666666', font=None)
            
            if not filename: 
                filename = f"nn_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e: 
            print(f"Error creating neural diagram: {e}")
            return None

    def _create_enhanced_decision_tree_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create a detailed decision tree visualization"""
        try:
            img = Image.new('RGB', (1000, 800), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((350, 30), f"Decision Tree: {topic[:35]}", fill='#1a202c', font=None)
            
            # Helper function to draw a node
            def draw_node(x, y, text, is_leaf=False):
                box_width, box_height = 120, 60
                color = '#22c55e' if is_leaf else '#3b82f6'
                outline_color = '#16a34a' if is_leaf else '#1e40af'
                
                draw.rectangle([x - box_width//2, y - box_height//2, 
                              x + box_width//2, y + box_height//2],
                             fill=color, outline=outline_color, width=2)
                
                # Wrap text
                draw.text((x - box_width//2 + 10, y - 15), text[:15], fill='white', font=None)
            
            # Draw tree structure
            # Root
            root_x, root_y = 500, 100
            draw_node(root_x, root_y, "Feature A?")
            
            # Level 1
            left_x, left_y = 250, 250
            right_x, right_y = 750, 250
            draw_node(left_x, left_y, "Feature B?")
            draw_node(right_x, right_y, "Feature C?")
            
            # Connections
            draw.line([root_x - 50, root_y + 30, left_x + 50, left_y - 30], fill='#64748b', width=2)
            draw.line([root_x + 50, root_y + 30, right_x - 50, right_y - 30], fill='#64748b', width=2)
            
            # Leaf nodes
            leaf_y = 400
            leaf_nodes = [
                (100, "Class A"),
                (250, "Class B"),
                (400, "Class A"),
                (600, "Class C"),
                (750, "Class B"),
                (900, "Class C")
            ]
            
            for leaf_x, label in leaf_nodes:
                draw_node(leaf_x, leaf_y, label, is_leaf=True)
            
            # Connections to leaves
            draw.line([left_x - 50, left_y + 30, 175, leaf_y - 30], fill='#64748b', width=2)
            draw.line([left_x + 50, left_y + 30, 325, leaf_y - 30], fill='#64748b', width=2)
            draw.line([right_x - 50, right_y + 30, 475, leaf_y - 30], fill='#64748b', width=2)
            draw.line([right_x + 50, right_y + 30, 675, leaf_y - 30], fill='#64748b', width=2)
            
            # Add legend
            draw.text((50, 680), "Decision Nodes (Blue): Feature split points", fill='#1a202c', font=None)
            draw.text((50, 720), "Leaf Nodes (Green): Final classification outcomes", fill='#1a202c', font=None)
            draw.text((50, 760), "Lines: Decision paths based on feature values", fill='#1a202c', font=None)
            
            if not filename: 
                filename = f"dt_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e: 
            print(f"Error creating decision tree diagram: {e}")
            return None

    def _create_enhanced_svm_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create an SVM classification visualization with hyperplane"""
        try:
            img = Image.new('RGB', (900, 700), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((300, 30), f"Support Vector Machine: {topic[:30]}", fill='#1a202c', font=None)
            
            # Draw scatter points for two classes
            import random
            random.seed(42)
            
            # Class 1 (Red)
            for _ in range(20):
                x = random.randint(150, 350)
                y = random.randint(150, 400)
                draw.ellipse([x-5, y-5, x+5, y+5], fill='#ef4444', outline='#7f1d1d', width=2)
            
            # Class 2 (Blue)
            for _ in range(20):
                x = random.randint(500, 700)
                y = random.randint(150, 400)
                draw.ellipse([x-5, y-5, x+5, y+5], fill='#3b82f6', outline='#1e3a8a', width=2)
            
            # Draw decision boundary (hyperplane)
            draw.line([400, 100, 450, 450], fill='#000000', width=3)
            
            # Draw margin lines
            draw.line([380, 90, 430, 460], fill='#f97316', width=2)
            draw.line([420, 110, 470, 440], fill='#f97316', width=2)
            
            # Highlight support vectors
            support_vectors = [(375, 200), (425, 250), (475, 300)]
            for sv_x, sv_y in support_vectors:
                draw.ellipse([sv_x-8, sv_y-8, sv_x+8, sv_y+8], outline='#fbbf24', width=3)
            
            # Add annotations
            draw.text((100, 450), "Class 1: Red Points", fill='#ef4444', font=None)
            draw.text((500, 450), "Class 2: Blue Points", fill='#3b82f6', font=None)
            draw.text((300, 550), "-- Decision Boundary (Hyperplane)", fill='#000000', font=None)
            draw.text((300, 580), "-- Margin (Maximum separation)", fill='#f97316', font=None)
            draw.text((300, 610), "O Support Vectors (Critical points)", fill='#fbbf24', font=None)
            
            # Add title annotations
            draw.text((50, 80), "Feature 1 ->", fill='#666666', font=None)
            draw.text((50, 450), "Feature 2 ^", fill='#666666', font=None)
            
            if not filename: 
                filename = f"svm_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e: 
            print(f"Error creating SVM diagram: {e}")
            return None

    def _create_enhanced_conceptual_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create a comprehensive conceptual diagram with central concept and related aspects"""
        try:
            img = Image.new('RGB', (1000, 800), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((350, 30), f"Conceptual Overview: {topic}", fill='#1a202c', font=None)
            
            # Central concept
            center_x, center_y = 500, 300
            central_radius = 80
            draw.ellipse([center_x - central_radius, center_y - central_radius,
                         center_x + central_radius, center_y + central_radius],
                        fill='#3b82f6', outline='#1e40af', width=3)
            
            # Wrap topic text for center
            topic_words = topic.split()[:3]
            topic_text = ' '.join(topic_words)
            draw.text((center_x - 60, center_y - 20), topic_text, fill='white', font=None)
            
            # Related concepts around the center
            num_aspects = 6
            import math
            aspect_labels = aspects[:num_aspects] if aspects and len(aspects) > 0 else [
                "Theory", "Applications", 
                "Benefits", "Algorithms",
                "Challenges", "Implementation"
            ]
            
            # Ensure we have exactly 6 labels by padding if needed
            while len(aspect_labels) < num_aspects:
                aspect_labels.append(f"Aspect {len(aspect_labels) + 1}")
            
            for i in range(num_aspects):
                angle = (i / num_aspects) * 2 * math.pi
                aspect_x = int(center_x + 250 * math.cos(angle))
                aspect_y = int(center_y + 250 * math.sin(angle))
                
                # Draw aspect circle
                aspect_radius = 50
                colors = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#06b6d4', '#8b5cf6']
                draw.ellipse([aspect_x - aspect_radius, aspect_y - aspect_radius,
                             aspect_x + aspect_radius, aspect_y + aspect_radius],
                            fill=colors[i % len(colors)], outline='#1a202c', width=2)
                
                # Draw connection line
                draw.line([center_x, center_y, aspect_x, aspect_y], fill='#cbd5e1', width=2)
                
                # Draw label (safe access)
                label = aspect_labels[i] if i < len(aspect_labels) else f"Aspect {i+1}"
                label_x = aspect_x - 40
                label_y = aspect_y - 10
                draw.text((label_x, label_y), label, fill='white', font=None)
            
            # Add information box at bottom
            draw.rectangle([50, 650, 950, 780], outline='#cbd5e1', width=2)
            draw.text((70, 670), "Key Concepts & Relationships:", fill='#1a202c', font=None)
            draw.text((70, 700), f"- {topic} involves multiple interconnected concepts and applications", fill='#666666', font=None)
            draw.text((70, 730), "- Each colored circle represents a different perspective or aspect", fill='#666666', font=None)
            draw.text((70, 760), "- Lines show how concepts are related and influence each other", fill='#666666', font=None)
            
            if not filename: 
                filename = f"concept_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e: 
            print(f"Error creating conceptual diagram: {e}")
            return None

    def _create_enhanced_regression_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create a regression visualization with data points and trend line"""
        try:
            img = Image.new('RGB', (1000, 700), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((300, 30), f"Regression Analysis: {topic[:35]}", fill='#1a202c', font=None)
            
            # Draw axes
            axis_x, axis_y = 100, 600
            draw.line([axis_x, axis_y, 900, axis_y], fill='#1a202c', width=2)  # X-axis
            draw.line([axis_x, axis_y, axis_x, 100], fill='#1a202c', width=2)  # Y-axis
            
            # Labels
            draw.text((850, 620), "Independent Variable →", fill='#1a202c', font=None)
            draw.text((30, 50), "Dependent\nVariable ↑", fill='#1a202c', font=None)
            
            # Draw scatter points
            import random
            random.seed(42)
            for i in range(25):
                x = random.randint(150, 850)
                y = random.randint(150, 550)
                draw.ellipse([x-6, y-6, x+6, y+6], fill='#ef4444', outline='#7f1d1d', width=2)
            
            # Draw trend line (regression line)
            draw.line([150, 500, 850, 200], fill='#3b82f6', width=3)
            
            # Draw confidence interval bands
            draw.line([150, 480, 850, 180], fill='#bfdbfe', width=2)
            draw.line([150, 520, 850, 220], fill='#bfdbfe', width=2)
            
            # Draw residuals (errors)
            for i in range(5):
                point_x = 250 + i * 120
                point_y = 450 - i * 100
                draw.ellipse([point_x-6, point_y-6, point_x+6, point_y+6], fill='#ef4444', outline='#7f1d1d', width=2)
                
                # Trend line y at this x
                trend_y = int(500 - (point_x - 150) * 300 / 700)
                draw.line([point_x, point_y, point_x, trend_y], fill='#f97316', width=1)
            
            # Legend
            draw.text((100, 650), "* Data Points", fill='#ef4444', font=None)
            draw.text((300, 650), "-- Regression Line (Best Fit)", fill='#3b82f6', font=None)
            draw.text((550, 650), "--- Confidence Interval", fill='#bfdbfe', font=None)
            draw.text((750, 650), "| Residuals (Errors)", fill='#f97316', font=None)
            
            if not filename: 
                filename = f"regression_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e: 
            print(f"Error creating regression diagram: {e}")
            return None

    def _create_enhanced_clustering_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create a clustering visualization with multiple clusters"""
        try:
            img = Image.new('RGB', (1000, 700), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((300, 30), f"Clustering Analysis: {topic[:35]}", fill='#1a202c', font=None)
            
            # Define cluster centers and colors
            clusters = [
                {'center': (250, 250), 'color': '#ef4444', 'name': 'Cluster 1'},
                {'center': (700, 250), 'color': '#3b82f6', 'name': 'Cluster 2'},
                {'center': (475, 500), 'color': '#22c55e', 'name': 'Cluster 3'},
            ]
            
            import random
            random.seed(42)
            
            # Draw data points for each cluster
            for cluster in clusters:
                cx, cy = cluster['center']
                for _ in range(20):
                    x = cx + random.randint(-80, 80)
                    y = cy + random.randint(-80, 80)
                    draw.ellipse([x-5, y-5, x+5, y+5], fill=cluster['color'], outline='#1a202c', width=1)
                
                # Draw cluster center (centroid)
                draw.ellipse([cx-10, cy-10, cx+10, cy+10], fill='#1a202c', outline=cluster['color'], width=3)
                draw.text((cx-15, cy-25), 'X', fill=cluster['color'], font=None)
            
            # Draw axes
            draw.line([100, 600, 900, 600], fill='#cbd5e1', width=1)
            draw.line([100, 100, 100, 600], fill='#cbd5e1', width=1)
            draw.text((850, 620), "Feature 1 ->", fill='#666666', font=None)
            draw.text((30, 550), "Feature 2 ^", fill='#666666', font=None)
            
            # Legend
            legend_y = 650
            for i, cluster in enumerate(clusters):
                x = 150 + i * 300
                draw.ellipse([x-6, legend_y-6, x+6, legend_y+6], fill=cluster['color'])
                draw.text((x+20, legend_y-10), f"{cluster['name']}", fill='#1a202c', font=None)
            
            draw.text((500, 680), "X = Centroid (Cluster Center)", fill='#1a202c', font=None)
            
            if not filename: 
                filename = f"clustering_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e: 
            print(f"Error creating clustering diagram: {e}")
            return None

    def _create_enhanced_pca_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create a PCA dimensionality reduction visualization"""
        try:
            img = Image.new('RGB', (1000, 700), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            draw.text((250, 30), f"Principal Component Analysis (PCA): {topic[:25]}", fill='#1a202c', font=None)
            
            # Left side: High-dimensional original data (conceptual)
            draw.text((150, 100), "Original: High-Dimensional Data", fill='#1a202c', font=None)
            draw.rectangle([50, 150, 350, 500], outline='#3b82f6', width=2)
            
            # Represent 3D data as scattered points
            import random
            random.seed(42)
            for _ in range(30):
                x = random.randint(60, 340)
                y = random.randint(160, 490)
                draw.ellipse([x-5, y-5, x+5, y+5], fill='#3b82f6', outline='#1e40af', width=1)
            
            draw.text((80, 520), "• Many dimensions (features)", fill='#666666', font=None)
            draw.text((80, 545), "• High complexity", fill='#666666', font=None)
            draw.text((80, 570), "• Difficult to visualize", fill='#666666', font=None)
            
            # Arrow in middle
            draw.line([400, 300, 550, 300], fill='#22c55e', width=3)
            draw.text((420, 280), "PCA", fill='#22c55e', font=None)
            
            # Right side: Reduced dimensional data
            draw.text((700, 100), "Reduced: Low-Dimensional Data", fill='#1a202c', font=None)
            draw.rectangle([650, 150, 950, 500], outline='#22c55e', width=2)
            
            # Draw 2D scatter
            for _ in range(30):
                x = random.randint(660, 940)
                y = random.randint(160, 490)
                draw.ellipse([x-5, y-5, x+5, y+5], fill='#22c55e', outline='#16a34a', width=1)
            
            draw.text((680, 520), "• Few dimensions (2 or 3)", fill='#666666', font=None)
            draw.text((680, 545), "• Low complexity", fill='#666666', font=None)
            draw.text((680, 570), "• Easy to visualize", fill='#666666', font=None)
            
            # Add PC1 and PC2 labels on the right
            draw.text((900, 510), "PC1 ->", fill='#1a202c', font=None)
            draw.text((630, 150), "^ PC2", fill='#1a202c', font=None)
            
            if not filename: 
                filename = f"pca_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e: 
            print(f"Error creating PCA diagram: {e}")
            return None

    def _create_flowchart_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create a flowchart showing process flow for any topic"""
        try:
            img = Image.new('RGB', (1000, 800), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            title_text = f"Process Flowchart: {topic[:35]}"
            draw.text((250, 30), title_text, fill='#1a202c', font=None)
            
            # Define process steps
            steps = [
                "Start",
                "Input Data",
                "Processing",
                "Model Eval",
                "Decision",
                "Optimize",
                "Output"
            ]
            
            if aspects and len(aspects) > 0:
                steps = [aspects[i] if i < len(aspects) else steps[i+1] for i in range(min(6, len(aspects)))]
                steps.append("Output")
            
            # Draw flowchart boxes and arrows
            box_width, box_height = 140, 60
            positions = []
            
            # Top row positions (0-2)
            for i in range(3):
                x = 120 + i * 280
                y = 150
                positions.append((x, y))
                
                # Draw box
                box_color = '#10b981' if i == 0 else '#3b82f6' if i < 2 else '#8b5cf6'
                draw.rectangle([x - box_width//2, y - box_height//2, x + box_width//2, y + box_height//2],
                             fill=box_color, outline='#1a202c', width=2)
                
                # Draw text
                step_text = steps[i][:13]
                draw.text((x - 60, y - 20), step_text, fill='white', font=None)
            
            # Arrows from top to middle
            draw.line([positions[2][0], positions[2][1] + box_height//2, positions[2][0], 230], fill='#64748b', width=2)
            
            # Middle row position
            middle_x, middle_y = 500, 320
            positions.append((middle_x, middle_y))
            
            # Decision diamond
            diamond_size = 60
            draw.polygon([
                (middle_x, middle_y - diamond_size),
                (middle_x + diamond_size, middle_y),
                (middle_x, middle_y + diamond_size),
                (middle_x - diamond_size, middle_y)
            ], fill='#f59e0b', outline='#1a202c', width=2)
            draw.text((middle_x - 25, middle_y - 15), "Condition?", fill='white', font=None)
            
            # Arrows to and from decision
            draw.line([positions[2][0], 230, middle_x, middle_y - diamond_size], fill='#64748b', width=2)
            
            # Bottom row - two paths from decision
            bottom_y = 500
            left_x, right_x = 280, 720
            
            # Left path (No)
            positions.append((left_x, bottom_y))
            draw.rectangle([left_x - box_width//2, bottom_y - box_height//2, left_x + box_width//2, bottom_y + box_height//2],
                         fill='#ef4444', outline='#1a202c', width=2)
            draw.text((left_x - 40, bottom_y - 20), "Adjust", fill='white', font=None)
            draw.line([middle_x - diamond_size, middle_y, left_x, bottom_y], fill='#64748b', width=2)
            draw.text((middle_x - 80, middle_y + 40), "No", fill='#666666', font=None)
            
            # Right path (Yes)
            positions.append((right_x, bottom_y))
            draw.rectangle([right_x - box_width//2, bottom_y - box_height//2, right_x + box_width//2, bottom_y + box_height//2],
                         fill='#22c55e', outline='#1a202c', width=2)
            draw.text((right_x - 35, bottom_y - 20), "Output", fill='white', font=None)
            draw.line([middle_x + diamond_size, middle_y, right_x, bottom_y], fill='#64748b', width=2)
            draw.text((middle_x + 60, middle_y + 40), "Yes", fill='#666666', font=None)
            
            # Feedback loop from left back to processing
            draw.line([left_x, bottom_y + box_height//2, left_x, 650], fill='#64748b', width=2)
            draw.line([left_x, 650, 100, 650], fill='#64748b', width=2)
            draw.line([100, 650, 100, 150], fill='#64748b', width=2)
            draw.text((50, 630), "Feedback Loop", fill='#666666', font=None)
            
            # Add legend
            draw.text((100, 730), "Start/End: Green  |  Process: Blue  |  Decision: Orange  |  Retry: Red  |  Output: Green", 
                     fill='#1a202c', font=None)
            
            if not filename:
                filename = f"flowchart_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e:
            print(f"Error creating flowchart: {e}")
            return None

    def _create_technical_neural_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create a detailed technical neural network diagram with specifications"""
        try:
            img = Image.new('RGB', (1200, 700), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            title_text = f"Technical Neural Network: {topic[:40]}"
            draw.text((300, 30), title_text, fill='#1a202c', font=None)
            
            # Left section: Architecture
            draw.rectangle([50, 100, 450, 650], outline='#3b82f6', width=2)
            draw.text((60, 110), "Network Architecture", fill='#3b82f6', font=None)
            
            arch_items = [
                "Layer Configuration:",
                "  Input Layer: 784 neurons",
                "  Hidden Layer 1: 256 neurons",
                "    Activation: ReLU",
                "  Hidden Layer 2: 128 neurons",
                "    Activation: ReLU",
                "  Output Layer: 10 neurons",
                "    Activation: Softmax",
                "",
                "Total Parameters: 237K",
                "Trainable: 236K",
            ]
            
            y_pos = 150
            for item in arch_items:
                draw.text((60, y_pos), item, fill='#666666', font=None)
                y_pos += 28
            
            # Middle section: Hyperparameters
            draw.rectangle([470, 100, 870, 650], outline='#8b5cf6', width=2)
            draw.text((480, 110), "Hyperparameters & Config", fill='#8b5cf6', font=None)
            
            hyper_items = [
                "Learning Rate: 0.001",
                "Decay: 1e-6",
                "Optimizer: Adam (beta1=0.9, beta2=0.999)",
                "Loss Function: CrossEntropy",
                "Batch Size: 32",
                "Epochs: 100",
                "Validation Split: 0.2",
                "Dropout Rate: 0.5",
                "Weight Init: Xavier",
                "Normalization: BatchNorm",
            ]
            
            y_pos = 150
            for item in hyper_items:
                draw.text((480, y_pos), item, fill='#666666', font=None)
                y_pos += 35
            
            # Right section: Performance Metrics
            draw.rectangle([890, 100, 1150, 650], outline='#22c55e', width=2)
            draw.text((900, 110), "Performance Metrics", fill='#22c55e', font=None)
            
            metrics_items = [
                "Training Acc: 0.985",
                "Training Loss: 0.045",
                "",
                "Validation Acc: 0.972",
                "Validation Loss: 0.089",
                "",
                "Test Acc: 0.968",
                "Precision: 0.975",
                "Recall: 0.968",
                "F1-Score: 0.971",
            ]
            
            y_pos = 150
            for item in metrics_items:
                draw.text((900, y_pos), item, fill='#666666', font=None)
                y_pos += 40
            
            if not filename:
                filename = f"technical_neural_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e:
            print(f"Error creating technical neural diagram: {e}")
            return None

    def _create_technical_decision_tree_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create a detailed technical decision tree with metrics"""
        try:
            img = Image.new('RGB', (1200, 700), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            title_text = f"Technical Decision Tree: {topic[:40]}"
            draw.text((350, 30), title_text, fill='#1a202c', font=None)
            
            # Left section: Tree specifications
            draw.rectangle([50, 100, 380, 650], outline='#3b82f6', width=2)
            draw.text((60, 110), "Tree Specifications", fill='#3b82f6', font=None)
            
            specs = [
                "max_depth: 10",
                "min_samples_split: 2",
                "min_samples_leaf: 1",
                "criterion: Gini",
                "splitter: best",
                "random_state: 42",
                "",
                "Total Nodes: 47",
                "Leaf Nodes: 24",
                "Tree Depth: 9",
                "Feature Count: 4",
            ]
            
            y_pos = 150
            for item in specs:
                draw.text((60, y_pos), item, fill='#666666', font=None)
                y_pos += 35
            
            # Middle section: Feature importance
            draw.rectangle([400, 100, 730, 650], outline='#8b5cf6', width=2)
            draw.text((410, 110), "Feature Importance", fill='#8b5cf6', font=None)
            
            features = [
                ("Feature_1", 0.45),
                ("Feature_2", 0.32),
                ("Feature_3", 0.18),
                ("Feature_4", 0.05),
            ]
            
            y_pos = 160
            for feat_name, importance in features:
                # Bar
                bar_width = int(importance * 300)
                draw.rectangle([410, y_pos - 15, 410 + bar_width, y_pos + 15],
                             fill='#8b5cf6', outline='#1a202c', width=1)
                # Label
                draw.text((420 + bar_width, y_pos - 10), f"{importance:.2f}", fill='#1a202c', font=None)
                draw.text((410, y_pos + 30), feat_name, fill='#666666', font=None)
                y_pos += 80
            
            # Right section: Metrics
            draw.rectangle([750, 100, 1150, 650], outline='#22c55e', width=2)
            draw.text((760, 110), "Performance Metrics", fill='#22c55e', font=None)
            
            perf_metrics = [
                "Accuracy: 0.923",
                "Precision: 0.918",
                "Recall: 0.928",
                "F1-Score: 0.923",
                "",
                "Gini Impurity: 0.156",
                "Entropy: 0.452",
                "",
                "Training Time: 2.5ms",
                "Prediction Time: 0.1ms",
            ]
            
            y_pos = 150
            for item in perf_metrics:
                draw.text((760, y_pos), item, fill='#666666', font=None)
                y_pos += 40
            
            if not filename:
                filename = f"technical_tree_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e:
            print(f"Error creating technical decision tree: {e}")
            return None

    def _create_technical_overview_diagram(self, topic: str, filename: Optional[str] = None, aspects: Optional[List[str]] = None) -> Optional[Tuple[str, str]]:
        """Create a technical overview diagram for generic topics"""
        try:
            img = Image.new('RGB', (1000, 700), '#ffffff')
            draw = ImageDraw.Draw(img)
            
            # Title
            title_text = f"Technical Overview: {topic}"
            draw.text((300, 30), title_text, fill='#1a202c', font=None)
            
            # Three columns of technical specifications
            columns = [
                {
                    'title': 'Architecture',
                    'x': 75,
                    'color': '#3b82f6',
                    'items': [
                        'Component A',
                        '  - Subcomponent A1',
                        '  - Subcomponent A2',
                        'Component B',
                        '  - Subcomponent B1',
                    ]
                },
                {
                    'title': 'Implementation',
                    'x': 375,
                    'color': '#8b5cf6',
                    'items': [
                        'Framework: TensorFlow',
                        'Library: Keras',
                        'Language: Python 3.9',
                        'Backend: CUDA',
                        'GPU Memory: 8GB',
                    ]
                },
                {
                    'title': 'Performance',
                    'x': 675,
                    'color': '#22c55e',
                    'items': [
                        'Throughput: 1000 ops/s',
                        'Latency: 10ms',
                        'Memory: 2.5GB',
                        'Accuracy: 96.8%',
                        'F1-Score: 0.968',
                    ]
                }
            ]
            
            col_width = 300
            
            for col in columns:
                x = col['x']
                color = col['color']
                
                # Column header
                draw.rectangle([x, 100, x + col_width, 150], outline=color, width=2)
                draw.text((x + 80, 115), col['title'], fill=color, font=None)
                
                # Column content
                y_pos = 170
                for item in col['items']:
                    draw.text((x + 20, y_pos), item, fill='#666666', font=None)
                    y_pos += 30
            
            # Add notes at bottom
            draw.text((100, 650), "All specifications are technical parameters used in the implementation and evaluation.", fill='#999999', font=None)
            
            if not filename:
                filename = f"technical_overview_{topic.replace(' ', '_')}_{datetime.now().strftime('%H%M%S')}.png"
            save_path = os.path.join(self.output_dir, filename)
            img.save(save_path)
            return save_path, f"/uploads/images/{filename}"
        except Exception as e:
            print(f"Error creating technical overview: {e}")
            return None

    def encode_image_to_base64(self, filepath: str) -> Optional[str]:
        try:
            with open(filepath, 'rb') as f:
                return base64.b64encode(f.read()).decode('utf-8')
        except: return None
    
    def list_generated_images(self) -> List[dict]:
        images = []
        try:
            for filename in os.listdir(self.output_dir):
                filepath = os.path.join(self.output_dir, filename)
                if os.path.isfile(filepath) and filename.lower().endswith(('.png', '.jpg', '.jpeg', '.svg')):
                    images.append({
                        'filename': filename,
                        'path': f"/uploads/images/{filename}",
                        'created': datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y-%m-%d %H:%M:%S")
                    })
        except: pass
        return sorted(images, key=lambda x: x['created'], reverse=True)

# Factory methods
_image_utils = None
def init_images(output_dir: str = "uploads/images"):
    global _image_utils
    _image_utils = ImageUtils(output_dir)
    return _image_utils

def get_images():
    global _image_utils
    if _image_utils is None: _image_utils = ImageUtils()
    return _image_utils
