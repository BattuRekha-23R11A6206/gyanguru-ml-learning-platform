"""
Groq AI Integration Module
Handles text generation using Groq API
"""

from groq import Groq
import os
from typing import Optional, List
import json

class GroqAIUtils:
    def __init__(self, api_key: Optional[str] = None):
        """Initialize Groq AI with API key"""
        self.api_key = api_key or os.getenv('GROQ_API_KEY')
        self.client = None
        self.model = "llama-3.1-8b-instant"  # Add missing model attribute
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is required but not set")
        
        try:
            self.client = Groq(api_key=self.api_key)
        except Exception as e:
            raise ValueError(f"Failed to initialize Groq client: {str(e)}")
        
    def generate_text_explanation(self, topic: str, complexity_level: str = "Intermediate") -> str:
        """
        Generate comprehensive text explanation for ML topics
        Args:
            topic: ML topic to explain
            complexity_level: "Beginner", "Intermediate", "Comprehensive"
        Returns:
            Structured explanation text
        """
        prompt = f"""You are an expert ML educator. Provide a comprehensive explanation of the following topic: {topic}.

Your response should be structured in markdown format with clear headings and sections.

Cover the following aspects:

- Basic definition and intuition
- Key concepts and terminology
- Mathematical foundations (if applicable)
- Practical applications
- Common pitfalls and best practices

Keep the explanation educational, clear, and engaging. Use simple language and avoid jargon where possible.

IMPORTANT: Provide ONLY text explanation. Absolutely NO code, NO code snippets, NO code examples, NO programming code at all. Even if the topic involves algorithms or programming concepts, explain them in plain text without writing any code. Focus purely on explanatory prose.

Include these sections (use headings):
1. Brief Overview (2-3 sentences)
2. Key Concepts (bullet points)
3. Intuition (plain-language explanation)
4. Mathematical Foundation (only if applicable; keep concise)
5. Practical Examples (real-world use-cases; not full code)
6. Common Misconceptions
7. Resources for Further Learning
"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an expert ML educator."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating explanation: {str(e)}"
    
    def generate_code_example(self, algorithm: str, complexity: str = "Detailed") -> str:
        """
        Generate Python code examples with detailed comments
        Args:
            algorithm: Algorithm or concept to implement
            complexity: "Simple", "Detailed", "Production"
        Returns:
            Python code with comments and documentation
        """
        # Determine code type based on algorithm topic
        algorithm_lower = algorithm.lower()
        
        if any(keyword in algorithm_lower for keyword in ['neural network', 'cnn', 'rnn', 'lstm', 'transformer']):
            code_type = "neural network implementation"
        elif any(keyword in algorithm_lower for keyword in ['linear regression', 'logistic regression', 'svm', 'decision tree', 'random forest']):
            code_type = "machine learning model implementation"
        elif any(keyword in algorithm_lower for keyword in ['preprocessing', 'feature engineering', 'data cleaning']):
            code_type = "data preprocessing pipeline"
        elif any(keyword in algorithm_lower for keyword in ['clustering', 'pca', 'dimensionality']):
            code_type = "unsupervised learning algorithm"
        elif any(keyword in algorithm_lower for keyword in ['evaluation', 'metrics', 'validation']):
            code_type = "model evaluation and metrics"
        else:
            code_type = "machine learning algorithm implementation"
        
        prompt = f"""You are an expert Python developer specializing in machine learning. Generate a complete, runnable Python code example for {code_type} of "{algorithm}".

Requirements for {complexity} complexity:
1. Include all necessary imports at the top
2. Create a well-structured class or function with proper docstrings
3. Add comprehensive inline comments explaining the code logic
4. Include example usage with sample data
5. Add error handling where appropriate
6. Follow Python best practices and PEP 8 style

The code should be immediately executable and demonstrate the {algorithm} concept clearly.

Format as complete Python code that can be copied and run."""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an expert Python developer."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating code: {str(e)}"
    
    def generate_audio_script(self, topic: str, length: str = "Medium") -> str:
        """
        Generate bullet point audio script for educational content
        Args:
            topic: Topic to create script for
            length: "Brief", "Medium", "Comprehensive"
        Returns:
            Structured bullet point audio script
        """
        prompt = f"""Create structured learning notes for audio format about: {topic}
Duration: {length} (Brief: 2-3 min, Medium: 5-8 min, Comprehensive: 10-15 min)

Use ONLY bullet points and sub-bullets - NO bold formatting, NO music cues, NO [INTRO/OUTRO] markers.
Just clean, direct text that sounds natural when read aloud.

Overview and Key Definition
• What this topic is and why it matters
• Core definition and importance in machine learning

Main Concepts and Components
• Key concept 1
• Key concept 2
• Key concept 3

How It Works
• Step or mechanism 1
• Step or mechanism 2
• Step or mechanism 3

Real-World Applications and Examples
• Practical application 1
• Practical application 2

Important Considerations
• Advantages of this approach
• Limitations or challenges
• Common misconceptions

Key Takeaways
• Main learning point 1
• Main learning point 2
• Next steps for deeper learning

Rules:
- NO bold text markers (** or __)
- NO music cues or stage directions
- NO special formatting
- Simple bullet points only
- Clear, educational language
- Each point complete but concise"""
        
        try:
            response = self.client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are an engaging ML educator creating audio lesson scripts."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Error generating audio script: {str(e)}"
    
    def generate_image_prompt(self, concept: str, diagram_type: str = "Conceptual", perspective: str = None) -> str:
        """
        Generate intelligent, detailed prompts for educational diagram creation
        """
        concept_lower = concept.lower()
        
        # NEURAL NETWORK PROMPTS
        if "neural network" in concept_lower or "neural" in concept_lower:
            if diagram_type == "Conceptual":
                if perspective == "architecture":
                    return f"""Create a detailed neural network architecture diagram for {concept}. 
                    Show 4 vertical layers: Input Layer (4 nodes), Hidden Layer 1 (6 nodes), Hidden Layer 2 (5 nodes), Output Layer (3 nodes).
                    Each node is a colored circle. Draw lines connecting all nodes between adjacent layers showing the network structure.
                    Use blue for input nodes, purple for hidden layers, and orange for output.
                    Label each layer clearly. Add arrows showing data flow from left (input) to right (output).
                    Professional educational style, clean white background, suitable for ML textbook."""
                elif perspective == "training":
                    return f"""Create an educational diagram showing neural network training process for {concept}.
                    Left side: raw data with scattered points. Middle: network diagram with arrows showing forward pass.
                    Right side: loss curve decreasing over iterations, backpropagation arrows.
                    Show weights/parameters updating with red arrows indicating error flow backwards.
                    Use green for correctly predicted items, red for errors. Modern infographic style."""
                elif perspective == "applications":
                    return f"""Create a visual showing real-world applications of {concept}.
                    Divide into 4 quadrants: Image Recognition (show face/object detection), NLP (text/language), 
                    Speech Recognition (audio waveforms), and Time Series (stock charts). 
                    Each quadrant shows a neural network connected to the application domain.
                    Use relevant icons and colors. Professional educational poster style."""
                else:
                    return f"""Create a beautiful, intuitive diagram for neural networks ({concept}).
                    Show a neural network with clear layers, colorful nodes, connecting lines.
                    Illustrate how neurons work together. Include a small example of pattern recognition.
                    Use gradient colors from blue to purple to orange. Clean, modern educational design."""
            
            elif diagram_type == "Technical":
                if perspective == "mathematics":
                    return f"""Create a technical mathematical diagram for {concept}.
                    Show mathematical equations: forward propagation formula (z = wx + b), activation function (sigmoid/relu curve),
                    backpropagation gradient formula, and loss function graph.
                    Include a small network diagram with weights labeled as w1, w2, etc.
                    Display these formulas cleanly with proper mathematical notation.
                    Academic paper quality, with clear mathematical symbols."""
                else:
                    return f"""Create a technical neural network architecture diagram for {concept}.
                    Show detailed network with specific layer counts, neuron counts labeled at each layer.
                    Include activation function names for each layer, weight matrices represented as WH1, WH2, W0.
                    Show bias terms, learning rate notation. Include mathematical notation for forward pass.
                    Engineering blueprint style, professional and precise."""
            
            elif diagram_type == "Flowchart":
                if perspective == "training":
                    return f"""Create a training flowchart for {concept}.
                    Steps: Load Data → Initialize Weights → Forward Pass → Calculate Loss → Backward Pass → Update Weights → 
                    Check Convergence (yes=stop, no=repeat). Show with rounded rectangles, clear arrows, decision diamonds.
                    Color coding: blue for data steps, orange for computation, green for convergence.
                    Include iteration counter and loss curve on the side. Professional workflow diagram."""
                else:
                    return f"""Create a neural network workflow flowchart for {concept}.
                    Show main process: Input → Preprocessing → Network Inference → Output → Postprocessing.
                    Each box contains sub-steps. Include feedback loops for training iterations.
                    Use standard flowchart symbols with clear labels and arrows. Professional diagram."""
        
        # DECISION TREE PROMPTS
        elif "decision tree" in concept_lower or "tree" in concept_lower:
            if diagram_type == "Conceptual":
                if perspective == "splitting":
                    return f"""Create a detailed decision tree diagram for {concept}.
                    Show a complete binary tree with: Root node asking about a feature, multiple decision nodes below it each asking about different features.
                    Each path splits based on feature values (yes/no or thresholds). Leaf nodes show final classifications (Class A, Class B, Class C).
                    Use blue for decision nodes, green for leaf nodes, red for rejected outcomes.
                    Label each split with feature names. Professional educational diagram."""
                elif perspective == "outcomes":
                    return f"""Create a decision tree visualization for {concept} showing outcomes.
                    Display multiple paths from root to leaf, with each complete path highlighted.
                    Show the final classification at each leaf node with examples of data points in each class.
                    Color code the paths by outcome class. Include a legend showing what variables mean.
                    Clear and educational, suitable for explaining decision logic."""
                else:
                    return f"""Create a clear decision tree diagram for {concept}.
                    Show hierarchical structure with branching decisions at each level.
                    Root node at top, decision nodes in middle levels, leaf nodes at bottom showing classifications.
                    Use distinct colors for different depths and outcomes. Label branches with decision criteria.
                    Professional educational style."""
            
            elif diagram_type == "Technical":
                if perspective == "algorithms":
                    return f"""Create a technical decision tree algorithm diagram for {concept}.
                    Show the recursive splitting process with Gini impurity or information gain calculations at each node.
                    Include mathematical notation for splitting criteria. Show how Gini changes at each split.
                    Display the decision boundary in feature space with threshold values labeled.
                    Academic technical diagram style."""
                else:
                    return f"""Create a technical decision tree diagram for {concept}.
                    Show detailed tree structure with entropy/Gini values at each node.
                    Include threshold values for splits, number of samples at each node.
                    Display the pruning point and optimal tree size chart on the side.
                    Engineering documentation style."""
            
            elif diagram_type == "Flowchart":
                return f"""Create a decision tree construction flowchart for {concept}.
                Steps: Select Best Feature → Split Data → Recursive Call on Subsets → Check Stopping Criteria → Prune Tree → Validate.
                Show with clear boxes and arrows. Include decision diamonds for stopping conditions.
                Color code by process type: blue for selection, orange for splitting, green for validation.
                Professional algorithm flowchart."""
        
        # SVM PROMPTS
        elif "support vector" in concept_lower or "svm" in concept_lower:
            if diagram_type == "Conceptual":
                if perspective == "margin":
                    return f"""Create an SVM visualization for {concept} emphasizing margins.
                    Show 2D scatter plot with: Red dots for Class 1 (left side), Blue dots for Class 2 (right side).
                    Draw the decision boundary (black line) separating the classes perfectly.
                    Highlight the margins on both sides (orange dashed lines) showing the maximum margin.
                    Circle the support vectors (critical points). Show the margin width with arrows.
                    Professional ML educational diagram."""
                elif perspective == "kernels":
                    return f"""Create an SVM kernel transformation diagram for {concept}.
                    Left side: 2D plot showing non-linearly separable data (scattered mixed points).
                    Arrow labeled "Kernel Transformation" in middle.
                    Right side: 3D plot showing how data transforms to be linearly separable in higher dimension.
                    Show the hyperplane clearly separating classes in the transformed space.
                    Use gradient colors to show the transformation. Educational poster style."""
                else:
                    return f"""Create a clear SVM diagram for {concept}.
                    Show 2D scatter plot with two distinct classes of points in different colors.
                    Draw the optimal separating hyperplane (decision boundary) as a straight line.
                    Highlight the support vectors and the margin region.
                    Include legend explaining each element. Professional educational diagram."""
            
            elif diagram_type == "Technical":
                return f"""Create a technical SVM diagram for {concept}.
                Show: data points, decision boundary, margin width with measurements, support vectors highlighted.
                Include mathematical notation for the optimization objective: minimize ||w|| subject to constraints.
                Show the kernel function selection options (linear, RBF, polynomial).
                Display the dual problem formulation with alpha coefficients.
                Academic technical diagram."""
            
            elif diagram_type == "Flowchart":
                return f"""Create an SVM training flowchart for {concept}.
                Steps: Load Data → Choose Kernel → Solve Optimization Problem → Find Support Vectors → 
                Compute Decision Boundary → Validate → Deploy. Show with clear boxes,decision points for parameter tuning.
                Professional algorithm workflow diagram."""
        
        # REGRESSION PROMPTS
        elif "regression" in concept_lower or "linear" in concept_lower:
            if diagram_type == "Conceptual":
                return f"""Create a regression visualization for {concept}.
                Show: X-Y scatter plot with red data points, blue regression line fitting through the data.
                Display confidence interval bands around the line in light blue. Show some residuals as vertical orange lines.
                Include labels for axes: Feature on X-axis, Target/Prediction on Y-axis.
                Show R-squared value. Professional statistical diagram."""
            elif diagram_type == "Technical":
                return f"""Create a technical regression diagram for {concept}.
                Show: scatter points, fitted line, residuals clearly marked, loss function curve, gradient descent steps.
                Include mathematical notation for least squares formula, R-squared calculation.
                Display the cost curve decreasing over iterations. Professional technical diagram."""
            elif diagram_type == "Flowchart":
                return f"""Create a regression training flowchart for {concept}.
                Show: Initialize Parameters → Compute Predictions → Calculate Loss → Gradient Descent → Update Parameters → 
                Check Convergence → Make Predictions. Professional workflow style."""
        
        # CLUSTERING PROMPTS  
        elif "clustering" in concept_lower or "k-means" in concept_lower:
            if diagram_type == "Conceptual":
                return f"""Create a clustering visualization for {concept}.
                Show: 2D scatter plot with points in 3 distinct clusters (red, blue, green colors).
                Mark the centroid of each cluster with a larger X symbol.
                Show cluster boundaries with faint circles around each cluster.
                Display some arrows pointing from points to their nearest centroid.
                Educational data science diagram."""
            elif diagram_type == "Technical":
                return f"""Create a technical clustering diagram for {concept}.
                Show multiple iterations: Initial random centroids → First assignment → First update → 
                Convergence after iterations. Show separated clusters, distance calculations, within-cluster sum of squares.
                Professional technical diagram."""
            elif diagram_type == "Flowchart":
                return f"""Create a K-means flowchart for {concept}.
                Steps: Initialize K Centroids → Assign Points to Nearest Centroid → Update Centroids →
                Check Convergence (yes=stop, no=repeat). Show iteration counter and convergence metric.
                Professional algorithm diagram."""
        
        # GENERIC FALLBACK
        else:
            if diagram_type == "Conceptual":
                return f"""Create an educational diagram for {concept}.
                Show the main topic in the center connected to 6 related concepts around it.
                Use different colors for different aspects. Draw connecting lines showing relationships.
                Label everything clearly. Professional educational infographic style."""
            elif diagram_type == "Technical":
                return f"""Create a detailed technical diagram for {concept}.
                Show system architecture with components, data flow, processing steps.
                Include technical labels and measurements. Professional documentation style."""
            elif diagram_type == "Flowchart":
                return f"""Create a process flowchart for {concept}.
                Show main steps in sequence with decision points and feedback loops.
                Use standard flowchart symbols. Professional workflow diagram."""
        
        return f"Create an educational diagram for {concept}"
    
    def get_diverse_perspectives(self, topic: str) -> list:
        """
        Generate diverse perspectives/aspects for a topic to create unique visualizations
        Returns list of (diagram_type, perspective) tuples for varied image generation
        """
        topic_lower = topic.lower()
        perspectives = []
        
        if "neural network" in topic_lower or "neural" in topic_lower:
            perspectives = [
                ("Conceptual", "architecture"),
                ("Technical", "mathematics"),
                ("Flowchart", "training"),
                ("Conceptual", "applications"),
            ]
        elif "decision tree" in topic_lower or "tree" in topic_lower:
            perspectives = [
                ("Conceptual", "splitting"),
                ("Technical", "algorithms"),
                ("Flowchart", "construction"),
                ("Technical", "metrics"),
            ]
        elif "support vector" in topic_lower or "svm" in topic_lower:
            perspectives = [
                ("Conceptual", "margin"),
                ("Technical", "classification"),
                ("Conceptual", "kernels"),
                ("Flowchart", None),
            ]
        elif "regression" in topic_lower or "linear" in topic_lower:
            perspectives = [
                ("Conceptual", None),
                ("Technical", "mathematics"),
                ("Flowchart", "optimization"),
                ("Conceptual", "applications"),
            ]
        elif "clustering" in topic_lower or "k-means" in topic_lower:
            perspectives = [
                ("Conceptual", None),
                ("Technical", "algorithms"),
                ("Flowchart", None),
                ("Conceptual", "applications"),
            ]
        else:
            # Generic perspectives for any topic
            perspectives = [
                ("Conceptual", None),
                ("Technical", None),
                ("Flowchart", None),
                ("Conceptual", "applications"),
            ]
        
        return perspectives
    
    def detect_dependencies(self, code: str) -> List[str]:
        """
        Detect Python dependencies from generated code using AST
        Args:
            code: Python code to analyze
        Returns:
            List of required dependencies
        """
        import ast
        import re
        
        dependencies = set()
        
        try:
            tree = ast.parse(code)
            
            # Find imports
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
            
            # Map common module names to package names
            mapping = {
                'cv2': 'opencv-python',
                'sklearn': 'scikit-learn',
                'PIL': 'Pillow',
                'yaml': 'PyYAML'
            }
            
            detected = []
            for dep in dependencies:
                detected.append(mapping.get(dep, dep))
            
            return sorted(list(set(detected)))
        except SyntaxError:
            return []
    
    def generate_quiz(self, topic: str, difficulty: str = "Intermediate", num_questions: int = 5) -> str:
        """
        Generate quiz questions in JSON format
        Args:
            topic: Topic for the quiz
            difficulty: Difficulty level (Beginner, Intermediate, Advanced)
            num_questions: Number of questions to generate
        Returns:
            JSON formatted string with quiz questions
        """
        if not self.client:
            raise ValueError("Groq client not initialized. Please check API key.")
        
        prompt = f"""Return ONLY valid JSON (no markdown, no backticks, no extra text).

Generate exactly {num_questions} multiple-choice questions for a {difficulty} level quiz on "{topic}" in Machine Learning.

JSON schema:
{{
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "questions": [
    {{
      "question": "... ?",
      "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
      "correct": 0,
      "explanation": "..."
    }}
  ]
}}

Rules:
- "correct" must be an integer index 0-3 corresponding to "options".
- "options" must contain exactly 4 strings.
- Each question must be unique and relevant to the topic.
- Questions should be appropriate for {difficulty} level.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert ML educator creating quiz questions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"Error generating quiz: {str(e)}")

# Create global instance
groq_utils = None

def init_groq(api_key: Optional[str] = None):
    """Initialize the Groq utility module"""
    global groq_utils
    groq_utils = GroqAIUtils(api_key)

def get_groq():
    """Get or initialize the global Groq utility instance.

    Always returns a `GroqAIUtils` instance. If an API key is not set or
    initialization fails, returns an instance with client=None and methods
    will handle API unavailability gracefully.
    """
    global groq_utils
    if groq_utils is None:
        try:
            api_key = os.getenv('GROQ_API_KEY')
            groq_utils = GroqAIUtils(api_key)
        except ValueError as e:
            print(f"[WARN] Groq initialization failed: {e}")
            # Create a fallback instance with client=None
            groq_utils = GroqAIUtils.__new__(GroqAIUtils)
            groq_utils.api_key = None
            groq_utils.client = None
            groq_utils.model = "llama-3.1-8b-instant"
    return groq_utils
