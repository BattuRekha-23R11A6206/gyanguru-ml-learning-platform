# utils/sklearn_utils.py
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.svm import SVC, SVR
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error
import numpy as np
import joblib
import os

class SklearnModelManager:
    def __init__(self, models_dir="saved_models"):
        self.models = {}
        self.models_dir = models_dir
        os.makedirs(self.models_dir, exist_ok=True)

    def create_model(self, model_type: str, **kwargs):
        """Create a scikit-learn model of the specified type"""
        model_map = {
            "random_forest_classifier": RandomForestClassifier,
            "random_forest_regressor": RandomForestRegressor,
            "linear_regression": LinearRegression,
            "logistic_regression": LogisticRegression,
            "svm_classifier": SVC,
            "svm_regressor": SVR
        }

        if model_type not in model_map:
            raise ValueError(f"Unsupported model type: {model_type}")

        return model_map[model_type](**kwargs)

    def train_model(self, X, y, model_type: str, test_size: float = 0.2, random_state: int = 42, **kwargs):
        """Train a model and return the trained model and metrics"""
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )

        model = self.create_model(model_type, **kwargs)
        model.fit(X_train, y_train)

        # Make predictions
        y_pred = model.predict(X_test)

        # Calculate metrics based on problem type
        if model_type in ["random_forest_classifier", "logistic_regression", "svm_classifier"]:
            accuracy = accuracy_score(y_test, y_pred)
            metrics = {"accuracy": float(accuracy)}
        else:
            mse = mean_squared_error(y_test, y_pred)
            metrics = {"mean_squared_error": float(mse)}

        return {
            "model": model,
            "metrics": metrics,
            "X_test": X_test,
            "y_test": y_test,
            "y_pred": y_pred
        }

    def save_model(self, model, name: str):
        """Save a trained model to disk"""
        path = os.path.join(self.models_dir, f"{name}.joblib")
        joblib.dump(model, path)
        return path

    def load_model(self, name: str):
        """Load a trained model from disk"""
        path = os.path.join(self.models_dir, f"{name}.joblib")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Model {name} not found")
        return joblib.load(path)

# Initialize a global instance
sklearn_manager = SklearnModelManager()
