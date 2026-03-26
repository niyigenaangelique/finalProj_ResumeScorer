import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import joblib
import os
import matplotlib.pyplot as plt
import seaborn as sns
from data_preprocessor import ResumePreprocessor

class ResumeModelTrainer:
    def __init__(self):
        self.models = {
            'random_forest': RandomForestRegressor(random_state=42),
            'gradient_boosting': GradientBoostingRegressor(random_state=42),
            'linear_regression': LinearRegression(),
            'ridge': Ridge(random_state=42)
        }
        self.best_model = None
        self.best_model_name = None
        self.preprocessor = ResumePreprocessor()
        
    def train_models(self, X, y):
        """Train multiple models and find the best one"""
        # Split the data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        results = {}
        
        for name, model in self.models.items():
            print(f"\nTraining {name}...")
            
            # Train the model
            model.fit(X_train, y_train)
            
            # Make predictions
            y_pred = model.predict(X_test)
            
            # Calculate metrics
            mse = mean_squared_error(y_test, y_pred)
            rmse = np.sqrt(mse)
            mae = mean_absolute_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            # Cross-validation
            cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')
            
            results[name] = {
                'model': model,
                'mse': mse,
                'rmse': rmse,
                'mae': mae,
                'r2': r2,
                'cv_mean': cv_scores.mean(),
                'cv_std': cv_scores.std()
            }
            
            print(f"  MSE: {mse:.4f}")
            print(f"  RMSE: {rmse:.4f}")
            print(f"  MAE: {mae:.4f}")
            print(f"  R²: {r2:.4f}")
            print(f"  CV R²: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
        
        # Find the best model based on R² score
        best_name = max(results.keys(), key=lambda x: results[x]['r2'])
        self.best_model = results[best_name]['model']
        self.best_model_name = best_name
        
        print(f"\nBest model: {best_name} with R² = {results[best_name]['r2']:.4f}")
        
        return results, X_test, y_test
    
    def hyperparameter_tuning(self, X, y):
        """Perform hyperparameter tuning for the best model"""
        if self.best_model_name == 'random_forest':
            param_grid = {
                'n_estimators': [100, 200, 300],
                'max_depth': [10, 20, None],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4]
            }
        elif self.best_model_name == 'gradient_boosting':
            param_grid = {
                'n_estimators': [100, 200, 300],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'subsample': [0.8, 0.9, 1.0]
            }
        elif self.best_model_name == 'ridge':
            param_grid = {
                'alpha': [0.1, 1.0, 10.0, 100.0]
            }
        else:
            print("No hyperparameter tuning available for this model")
            return
        
        print(f"\nPerforming hyperparameter tuning for {self.best_model_name}...")
        
        grid_search = GridSearchCV(
            self.best_model, param_grid, cv=5, scoring='r2', n_jobs=-1
        )
        
        grid_search.fit(X, y)
        
        self.best_model = grid_search.best_estimator_
        
        print(f"Best parameters: {grid_search.best_params_}")
        print(f"Best cross-validation R²: {grid_search.best_score_:.4f}")
    
    def save_model(self, model_path="models/resume_model.pkl"):
        """Save the trained model"""
        os.makedirs("models", exist_ok=True)
        
        model_data = {
            'model': self.best_model,
            'model_name': self.best_model_name,
            'preprocessor': self.preprocessor
        }
        
        joblib.dump(model_data, model_path)
        print(f"Model saved to {model_path}")
    
    def load_model(self, model_path="models/resume_model.pkl"):
        """Load a trained model"""
        if os.path.exists(model_path):
            model_data = joblib.load(model_path)
            self.best_model = model_data['model']
            self.best_model_name = model_data['model_name']
            self.preprocessor = model_data['preprocessor']
            print(f"Model loaded from {model_path}")
            return True
        else:
            print(f"No model found at {model_path}")
            return False
    
    def plot_feature_importance(self, X, top_n=20):
        """Plot feature importance for tree-based models"""
        if hasattr(self.best_model, 'feature_importances_'):
            importances = self.best_model.feature_importances_
            feature_names = X.columns
            
            # Create a DataFrame for better visualization
            feature_importance_df = pd.DataFrame({
                'feature': feature_names,
                'importance': importances
            }).sort_values('importance', ascending=False)
            
            # Plot top features
            plt.figure(figsize=(12, 8))
            top_features = feature_importance_df.head(top_n)
            
            sns.barplot(data=top_features, x='importance', y='feature')
            plt.title(f'Top {top_n} Feature Importance - {self.best_model_name}')
            plt.xlabel('Importance')
            plt.tight_layout()
            
            # Save the plot
            os.makedirs("plots", exist_ok=True)
            plt.savefig("plots/feature_importance.png")
            plt.show()
            
            return feature_importance_df
        else:
            print("Feature importance not available for this model")
            return None
    
    def evaluate_model(self, X_test, y_test):
        """Detailed evaluation of the best model"""
        y_pred = self.best_model.predict(X_test)
        
        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print(f"\nFinal Model Evaluation ({self.best_model_name}):")
        print(f"  MSE: {mse:.4f}")
        print(f"  RMSE: {rmse:.4f}")
        print(f"  MAE: {mae:.4f}")
        print(f"  R²: {r2:.4f}")
        
        # Plot actual vs predicted
        plt.figure(figsize=(10, 6))
        plt.scatter(y_test, y_pred, alpha=0.6)
        plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
        plt.xlabel('Actual Scores')
        plt.ylabel('Predicted Scores')
        plt.title('Actual vs Predicted Resume Scores')
        plt.tight_layout()
        
        os.makedirs("plots", exist_ok=True)
        plt.savefig("plots/actual_vs_predicted.png")
        plt.show()
        
        return {
            'mse': mse,
            'rmse': rmse,
            'mae': mae,
            'r2': r2,
            'predictions': y_pred
        }

def main():
    """Main training pipeline"""
    # Check if data exists
    data_files = []
    if os.path.exists("./data"):
        data_files = [f for f in os.listdir("./data") if f.endswith(('.csv', '.xlsx', '.json'))]
    
    if not data_files:
        print("No data files found. Please run download_data.py first.")
        return
    
    # Use the first available data file
    data_path = f"./data/{data_files[0]}"
    print(f"Using data file: {data_path}")
    
    # Initialize trainer
    trainer = ResumeModelTrainer()
    
    # Load and preprocess data
    try:
        X, y, processed_df = trainer.preprocessor.load_and_process_data(data_path)
        print(f"Features shape: {X.shape}")
        print(f"Target shape: {y.shape}")
    except Exception as e:
        print(f"Error processing data: {e}")
        return
    
    # Train models
    results, X_test, y_test = trainer.train_models(X, y)
    
    # Hyperparameter tuning
    trainer.hyperparameter_tuning(X, y)
    
    # Final evaluation
    evaluation = trainer.evaluate_model(X_test, y_test)
    
    # Plot feature importance
    feature_importance = trainer.plot_feature_importance(X)
    
    # Save the model
    trainer.save_model()
    
    print("\nTraining completed successfully!")

if __name__ == "__main__":
    main()
