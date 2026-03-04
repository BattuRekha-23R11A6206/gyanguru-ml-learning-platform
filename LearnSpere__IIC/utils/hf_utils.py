# utils/hf_utils.py
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import torch
from typing import Dict, List, Union
import os

class HFModelManager:
    def __init__(self):
        self.models = {}
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load_model(self, task: str, model_name: str = None):
        """Load a Hugging Face model for a specific task"""
        if task not in self.models:
            try:
                if task == "text-generation":
                    model_name = model_name or "gpt2"
                    self.models[task] = pipeline("text-generation", model=model_name, device=self.device)
                elif task == "summarization":
                    model_name = model_name or "facebook/bart-large-cnn"
                    self.models[task] = pipeline("summarization", model=model_name, device=self.device)
                elif task == "question-answering":
                    model_name = model_name or "deepset/roberta-base-squad2"
                    self.models[task] = pipeline("question-answering", model=model_name, device=self.device)
                elif task == "sentiment-analysis":
                    model_name = model_name or "distilbert-base-uncased-finetuned-sst-2-english"
                    self.models[task] = pipeline("sentiment-analysis", model=model_name, device=self.device)
                return True
            except Exception as e:
                print(f"Error loading {task} model: {str(e)}")
                return False
        return True

    def generate_text(self, prompt: str, max_length: int = 100, **kwargs) -> str:
        """Generate text using a language model"""
        if not self.load_model("text-generation"):
            return "Error: Could not load text generation model"

        try:
            result = self.models["text-generation"](
                prompt,
                max_length=max_length,
                num_return_sequences=1,
                **kwargs
            )
            return result[0]['generated_text']
        except Exception as e:
            return f"Error generating text: {str(e)}"

    def summarize_text(self, text: str, max_length: int = 130, min_length: int = 30) -> str:
        """Summarize text using a summarization model"""
        if not self.load_model("summarization"):
            return "Error: Could not load summarization model"

        try:
            result = self.models["summarization"](
                text,
                max_length=max_length,
                min_length=min_length,
                do_sample=False
            )
            return result[0]['summary_text']
        except Exception as e:
            return f"Error summarizing text: {str(e)}"

    def answer_question(self, question: str, context: str) -> Dict[str, Union[str, float]]:
        """Answer a question based on the given context"""
        if not self.load_model("question-answering"):
            return {"error": "Could not load QA model"}

        try:
            result = self.models["question-answering"](question=question, context=context)
            return {
                "answer": result['answer'],
                "score": float(result['score']),
                "start": result['start'],
                "end": result['end']
            }
        except Exception as e:
            return {"error": f"Error answering question: {str(e)}"}

    def analyze_sentiment(self, text: str) -> Dict[str, Union[str, float]]:
        """Analyze sentiment of the given text"""
        if not self.load_model("sentiment-analysis"):
            return {"error": "Could not load sentiment analysis model"}

        try:
            result = self.models["sentiment-analysis"](text)
            return {
                "label": result[0]['label'],
                "score": float(result[0]['score'])
            }
        except Exception as e:
            return {"error": f"Error analyzing sentiment: {str(e)}"}

# Initialize a global instance
hf_manager = HFModelManager()

def init_hf_models():
    """Initialize Hugging Face models in the background - now lazy loading"""
    # Models will be loaded on first use instead of at startup
    # This prevents the app from hanging during startup
    return True
