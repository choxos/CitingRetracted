#!/usr/bin/env python3
"""
Multi-Modal Machine Learning Classifier for Predatory Journal Detection
Ensemble approach using multiple algorithms
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
import joblib
import json
from datetime import datetime
from sklearn.model_selection import train_test_split, cross_val_score, StratifiedKFold
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.svm import SVC
from sklearn.neural_network import MLPClassifier
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score, 
    roc_auc_score, classification_report, confusion_matrix
)
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectKBest, f_classif, RFE
import xgboost as xgb
import lightgbm as lgb
try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    
from imblearn.over_sampling import SMOTE
from imblearn.under_sampling import RandomUnderSampler
from imblearn.pipeline import Pipeline as ImbPipeline
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    PLOTTING_AVAILABLE = True
except ImportError:
    PLOTTING_AVAILABLE = False
import logging

from config import Config
from ml_models.feature_extractor import FeatureExtractor

class PredatoryClassifier:
    """
    Multi-modal ensemble classifier for predatory journal detection
    Combines multiple ML algorithms with feature importance analysis
    """
    
    def __init__(self, config: Config = None):
        self.config = config or Config()
        self.logger = logging.getLogger(__name__)
        
        # Initialize feature extractor
        self.feature_extractor = FeatureExtractor()
        
        # Initialize models
        self.models = {}
        self.ensemble_weights = {}
        self.scaler = StandardScaler()
        self.feature_selector = None
        
        # Performance tracking
        self.training_history = []
        self.feature_importance = {}
        self.model_performance = {}
        
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize individual ML models"""
        
        # Random Forest - Good for interpretability
        self.models['random_forest'] = RandomForestClassifier(
            n_estimators=self.config.N_ESTIMATORS,
            max_features=self.config.MAX_FEATURES,
            random_state=self.config.MODEL_RANDOM_STATE,
            n_jobs=-1,
            class_weight='balanced'
        )
        
        # XGBoost - High performance gradient boosting
        self.models['xgboost'] = xgb.XGBClassifier(
            n_estimators=self.config.N_ESTIMATORS,
            random_state=self.config.MODEL_RANDOM_STATE,
            eval_metric='logloss',
            scale_pos_weight=1  # Will adjust based on class imbalance
        )
        
        # LightGBM - Fast gradient boosting
        self.models['lightgbm'] = lgb.LGBMClassifier(
            n_estimators=self.config.N_ESTIMATORS,
            random_state=self.config.MODEL_RANDOM_STATE,
            class_weight='balanced',
            verbose=-1
        )
        
        # Support Vector Machine - Good for high-dimensional data
        self.models['svm'] = SVC(
            kernel='rbf',
            probability=True,  # Enable probability predictions
            random_state=self.config.MODEL_RANDOM_STATE,
            class_weight='balanced'
        )
        
        # Neural Network - Can capture complex patterns
        self.models['neural_network'] = MLPClassifier(
            hidden_layer_sizes=(100, 50),
            max_iter=1000,
            random_state=self.config.MODEL_RANDOM_STATE,
            early_stopping=True,
            validation_fraction=0.1
        )
        
        # Gradient Boosting - Alternative boosting implementation
        self.models['gradient_boosting'] = GradientBoostingClassifier(
            n_estimators=self.config.N_ESTIMATORS,
            random_state=self.config.MODEL_RANDOM_STATE
        )
    
    def prepare_training_data(self, scraped_data_list: List[Dict], labels: List[int]) -> Tuple[pd.DataFrame, np.array, List[str]]:
        """
        Prepare training data from scraped journal data
        
        Args:
            scraped_data_list: List of scraped journal data dictionaries
            labels: List of binary labels (1=predatory, 0=legitimate)
            
        Returns:
            Tuple of (features_df, labels_array, feature_names)
        """
        self.logger.info(f"Preparing training data from {len(scraped_data_list)} samples")
        
        # Extract features
        features_list = []
        for data in scraped_data_list:
            try:
                features = self.feature_extractor.extract_features(data)
                features_list.append(features)
            except Exception as e:
                self.logger.warning(f"Failed to extract features from journal data: {e}")
                continue
        
        # Create ML dataset
        features_df, feature_names = self.feature_extractor.prepare_ml_dataset(features_list)
        labels_array = np.array(labels[:len(features_df)])  # Ensure same length
        
        self.logger.info(f"Prepared {len(features_df)} samples with {len(feature_names)} features")
        
        return features_df, labels_array, feature_names
    
    def train_models(self, X: pd.DataFrame, y: np.array, feature_names: List[str],
                    test_size: float = 0.2, balance_data: bool = True,
                    feature_selection: bool = True) -> Dict:
        """
        Train all models and evaluate performance
        
        Args:
            X: Feature DataFrame
            y: Labels array
            feature_names: List of feature names
            test_size: Proportion of data for testing
            balance_data: Whether to balance the dataset
            feature_selection: Whether to perform feature selection
            
        Returns:
            Dictionary containing training results and metrics
        """
        training_start = datetime.now()
        self.logger.info("Starting model training...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.config.MODEL_RANDOM_STATE,
            stratify=y
        )
        
        # Handle class imbalance
        if balance_data:
            X_train, y_train = self._balance_dataset(X_train, y_train)
        
        # Feature scaling
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Feature selection
        if feature_selection:
            X_train_scaled, X_test_scaled, selected_features = self._select_features(
                X_train_scaled, X_test_scaled, y_train, feature_names
            )
        else:
            selected_features = feature_names
        
        # Train individual models
        results = {
            'training_start': training_start.isoformat(),
            'models_trained': [],
            'individual_performance': {},
            'ensemble_performance': {},
            'feature_importance': {},
            'selected_features': selected_features,
            'class_distribution': {
                'train': {
                    'legitimate': int(np.sum(y_train == 0)),
                    'predatory': int(np.sum(y_train == 1))
                },
                'test': {
                    'legitimate': int(np.sum(y_test == 0)),
                    'predatory': int(np.sum(y_test == 1))
                }
            }
        }
        
        # Train each model
        trained_models = {}
        model_predictions = {}
        
        for model_name, model in self.models.items():
            try:
                self.logger.info(f"Training {model_name}...")
                
                # Train model
                if model_name == 'neural_network':
                    model.fit(X_train_scaled, y_train)
                else:
                    model.fit(X_train_scaled if model_name in ['svm', 'neural_network'] 
                             else X_train, y_train)
                
                # Predict
                if model_name in ['svm', 'neural_network']:
                    y_pred = model.predict(X_test_scaled)
                    y_pred_proba = model.predict_proba(X_test_scaled)[:, 1]
                else:
                    y_pred = model.predict(X_test)
                    y_pred_proba = model.predict_proba(X_test)[:, 1]
                
                # Evaluate
                performance = self._evaluate_model(y_test, y_pred, y_pred_proba, model_name)
                results['individual_performance'][model_name] = performance
                
                # Store for ensemble
                trained_models[model_name] = model
                model_predictions[model_name] = y_pred_proba
                
                # Feature importance (for tree-based models)
                if hasattr(model, 'feature_importances_'):
                    importance_dict = {}
                    for i, importance in enumerate(model.feature_importances_):
                        feature_name = selected_features[i] if i < len(selected_features) else f'feature_{i}'
                        importance_dict[feature_name] = float(importance)
                    results['feature_importance'][model_name] = importance_dict
                
                results['models_trained'].append(model_name)
                self.logger.info(f"✓ {model_name} trained successfully")
                
            except Exception as e:
                self.logger.error(f"✗ Failed to train {model_name}: {e}")
                continue
        
        # Create ensemble
        if len(trained_models) >= 2:
            ensemble_performance = self._create_ensemble(
                model_predictions, y_test, trained_models
            )
            results['ensemble_performance'] = ensemble_performance
        
        # Cross-validation
        cv_results = self._perform_cross_validation(X_train_scaled, y_train, selected_features)
        results['cross_validation'] = cv_results
        
        # SHAP analysis for interpretability (on best performing model)
        best_model_name = max(results['individual_performance'].keys(),
                             key=lambda x: results['individual_performance'][x]['f1_score'])
        
        shap_analysis = self._perform_shap_analysis(
            trained_models[best_model_name], X_test_scaled, selected_features
        )
        results['shap_analysis'] = shap_analysis
        
        # Store models and results
        self.trained_models = trained_models
        self.model_performance = results
        
        training_end = datetime.now()
        results['training_duration'] = (training_end - training_start).total_seconds()
        results['training_end'] = training_end.isoformat()
        
        self.logger.info(f"Training completed in {results['training_duration']:.2f} seconds")
        
        return results
    
    def _balance_dataset(self, X: pd.DataFrame, y: np.array) -> Tuple[np.array, np.array]:
        """Balance dataset using SMOTE oversampling"""
        self.logger.info("Balancing dataset with SMOTE...")
        
        # Use SMOTE for oversampling minority class
        smote = SMOTE(random_state=self.config.MODEL_RANDOM_STATE)
        X_balanced, y_balanced = smote.fit_resample(X, y)
        
        self.logger.info(f"Original distribution: {np.bincount(y)}")
        self.logger.info(f"Balanced distribution: {np.bincount(y_balanced)}")
        
        return X_balanced, y_balanced
    
    def _select_features(self, X_train: np.array, X_test: np.array, 
                        y_train: np.array, feature_names: List[str]) -> Tuple[np.array, np.array, List[str]]:
        """Select most important features"""
        self.logger.info("Performing feature selection...")
        
        # Use SelectKBest with f_classif
        k = min(50, X_train.shape[1])  # Select top 50 or all features if less
        selector = SelectKBest(score_func=f_classif, k=k)
        
        X_train_selected = selector.fit_transform(X_train, y_train)
        X_test_selected = selector.transform(X_test)
        
        # Get selected feature names
        selected_indices = selector.get_support(indices=True)
        selected_features = [feature_names[i] for i in selected_indices]
        
        self.feature_selector = selector
        
        self.logger.info(f"Selected {len(selected_features)} features out of {len(feature_names)}")
        
        return X_train_selected, X_test_selected, selected_features
    
    def _evaluate_model(self, y_true: np.array, y_pred: np.array, 
                       y_pred_proba: np.array, model_name: str) -> Dict:
        """Evaluate individual model performance"""
        
        metrics = {
            'accuracy': float(accuracy_score(y_true, y_pred)),
            'precision': float(precision_score(y_true, y_pred, average='weighted')),
            'recall': float(recall_score(y_true, y_pred, average='weighted')),
            'f1_score': float(f1_score(y_true, y_pred, average='weighted')),
            'roc_auc': float(roc_auc_score(y_true, y_pred_proba)),
            'confusion_matrix': confusion_matrix(y_true, y_pred).tolist(),
            'classification_report': classification_report(y_true, y_pred, output_dict=True)
        }
        
        return metrics
    
    def _create_ensemble(self, model_predictions: Dict, y_test: np.array, 
                        trained_models: Dict) -> Dict:
        """Create ensemble predictions"""
        self.logger.info("Creating ensemble predictions...")
        
        # Simple average ensemble
        ensemble_proba = np.mean(list(model_predictions.values()), axis=0)
        ensemble_pred = (ensemble_proba > 0.5).astype(int)
        
        # Weighted ensemble based on individual F1 scores
        f1_scores = {}
        for model_name in model_predictions.keys():
            performance = self.model_performance.get('individual_performance', {}).get(model_name, {})
            f1_scores[model_name] = performance.get('f1_score', 0)
        
        # Calculate weights
        total_f1 = sum(f1_scores.values())
        weights = {name: score/total_f1 for name, score in f1_scores.items()} if total_f1 > 0 else {}
        
        # Weighted ensemble
        if weights:
            weighted_proba = np.zeros_like(ensemble_proba)
            for model_name, proba in model_predictions.items():
                weighted_proba += weights[model_name] * proba
            weighted_pred = (weighted_proba > 0.5).astype(int)
        else:
            weighted_proba = ensemble_proba
            weighted_pred = ensemble_pred
        
        # Evaluate ensembles
        simple_performance = self._evaluate_model(y_test, ensemble_pred, ensemble_proba, 'simple_ensemble')
        weighted_performance = self._evaluate_model(y_test, weighted_pred, weighted_proba, 'weighted_ensemble')
        
        # Store ensemble weights
        self.ensemble_weights = weights
        
        return {
            'simple_ensemble': simple_performance,
            'weighted_ensemble': weighted_performance,
            'ensemble_weights': weights
        }
    
    def _perform_cross_validation(self, X: np.array, y: np.array, feature_names: List[str]) -> Dict:
        """Perform cross-validation on all models"""
        self.logger.info("Performing cross-validation...")
        
        cv_results = {}
        cv = StratifiedKFold(n_splits=self.config.CV_FOLDS, shuffle=True, 
                           random_state=self.config.MODEL_RANDOM_STATE)
        
        for model_name, model in self.models.items():
            try:
                # Use scaled data for SVM and NN
                X_cv = X if model_name not in ['svm', 'neural_network'] else X
                
                scores = cross_val_score(model, X_cv, y, cv=cv, scoring='f1_weighted')
                cv_results[model_name] = {
                    'mean_f1': float(np.mean(scores)),
                    'std_f1': float(np.std(scores)),
                    'scores': scores.tolist()
                }
            except Exception as e:
                self.logger.warning(f"Cross-validation failed for {model_name}: {e}")
                cv_results[model_name] = {'error': str(e)}
        
        return cv_results
    
    def _perform_shap_analysis(self, model, X_test: np.array, feature_names: List[str]) -> Dict:
        """Perform SHAP analysis for model interpretability"""
        if not SHAP_AVAILABLE:
            return {
                'error': 'SHAP not available. Install with: pip install shap',
                'feature_importance': {},
                'top_features': []
            }
        
        try:
            self.logger.info("Performing SHAP analysis...")
            
            # Create SHAP explainer
            if hasattr(model, 'predict_proba'):
                explainer = shap.Explainer(model.predict_proba, X_test[:100])  # Use sample for speed
                shap_values = explainer(X_test[:20])  # Explain first 20 predictions
                
                # Get mean absolute SHAP values for feature importance
                if hasattr(shap_values, 'values') and len(shap_values.values.shape) > 2:
                    # Multi-class case, take positive class
                    mean_shap = np.mean(np.abs(shap_values.values[:, :, 1]), axis=0)
                else:
                    mean_shap = np.mean(np.abs(shap_values.values), axis=0)
                
                # Create feature importance dictionary
                feature_importance = {}
                for i, importance in enumerate(mean_shap):
                    if i < len(feature_names):
                        feature_importance[feature_names[i]] = float(importance)
                
                return {
                    'feature_importance': feature_importance,
                    'top_features': sorted(feature_importance.items(), 
                                         key=lambda x: x[1], reverse=True)[:10]
                }
            else:
                return {'error': 'Model does not support probability prediction'}
                
        except Exception as e:
            self.logger.warning(f"SHAP analysis failed: {e}")
            return {'error': str(e)}
    
    def predict_journal(self, scraped_data: Dict, use_ensemble: bool = True) -> Dict:
        """
        Predict if a journal is predatory based on scraped data
        
        Args:
            scraped_data: Scraped journal data dictionary
            use_ensemble: Whether to use ensemble prediction
            
        Returns:
            Dictionary containing prediction results
        """
        try:
            # Extract features
            features = self.feature_extractor.extract_features(scraped_data)
            
            # Prepare for prediction
            features_df = pd.DataFrame([features])
            features_df, _ = self.feature_extractor.prepare_ml_dataset([features])
            
            # Scale features
            features_scaled = self.scaler.transform(features_df)
            
            # Apply feature selection if used during training
            if self.feature_selector:
                features_scaled = self.feature_selector.transform(features_scaled)
            
            # Make predictions with all models
            predictions = {}
            probabilities = {}
            
            for model_name, model in self.trained_models.items():
                if model_name in ['svm', 'neural_network']:
                    pred_proba = model.predict_proba(features_scaled)[0]
                else:
                    pred_proba = model.predict_proba(features_df)[0]
                
                predictions[model_name] = {
                    'predatory_probability': float(pred_proba[1]),
                    'legitimate_probability': float(pred_proba[0]),
                    'prediction': 'predatory' if pred_proba[1] > 0.5 else 'legitimate'
                }
                probabilities[model_name] = pred_proba[1]
            
            # Ensemble prediction
            if use_ensemble and self.ensemble_weights:
                ensemble_prob = sum(prob * self.ensemble_weights.get(name, 0) 
                                  for name, prob in probabilities.items())
            else:
                ensemble_prob = np.mean(list(probabilities.values()))
            
            # Calculate predatory score (0-100)
            predatory_score = ensemble_prob * 100
            
            # Determine risk level
            if predatory_score >= self.config.VERY_HIGH_RISK_THRESHOLD:
                risk_level = "Very High Risk"
                recommendation = "Almost certainly predatory - avoid"
            elif predatory_score >= self.config.HIGH_RISK_THRESHOLD:
                risk_level = "High Risk"
                recommendation = "Likely predatory - exercise extreme caution"
            elif predatory_score >= self.config.MODERATE_RISK_THRESHOLD:
                risk_level = "Moderate Risk"
                recommendation = "Requires careful investigation"
            elif predatory_score >= self.config.LEGITIMATE_THRESHOLD:
                risk_level = "Low Risk"
                recommendation = "Appears legitimate but verify independently"
            else:
                risk_level = "Very Low Risk"
                recommendation = "Appears to be a legitimate journal"
            
            result = {
                'journal_url': scraped_data.get('url', ''),
                'predatory_score': round(predatory_score, 2),
                'risk_level': risk_level,
                'recommendation': recommendation,
                'ensemble_prediction': 'predatory' if ensemble_prob > 0.5 else 'legitimate',
                'confidence': round(max(ensemble_prob, 1-ensemble_prob) * 100, 2),
                'individual_predictions': predictions,
                'analysis_timestamp': datetime.now().isoformat(),
                'model_version': '1.0'
            }
            
            return result
            
        except Exception as e:
            self.logger.error(f"Prediction failed: {e}")
            return {
                'error': str(e),
                'journal_url': scraped_data.get('url', ''),
                'predatory_score': 50,  # Neutral score for errors
                'risk_level': 'Unknown',
                'recommendation': 'Manual review required due to analysis error'
            }
    
    def save_model(self, filepath: str):
        """Save trained models and components"""
        model_data = {
            'models': self.trained_models,
            'scaler': self.scaler,
            'feature_selector': self.feature_selector,
            'ensemble_weights': self.ensemble_weights,
            'feature_extractor': self.feature_extractor,
            'performance': self.model_performance,
            'config': {
                'MODEL_RANDOM_STATE': self.config.MODEL_RANDOM_STATE,
                'CV_FOLDS': self.config.CV_FOLDS,
                'N_ESTIMATORS': self.config.N_ESTIMATORS
            },
            'save_timestamp': datetime.now().isoformat()
        }
        
        joblib.dump(model_data, filepath)
        self.logger.info(f"Model saved to {filepath}")
    
    def load_model(self, filepath: str):
        """Load trained models and components"""
        try:
            model_data = joblib.load(filepath)
            
            self.trained_models = model_data['models']
            self.scaler = model_data['scaler']
            self.feature_selector = model_data['feature_selector']
            self.ensemble_weights = model_data['ensemble_weights']
            self.feature_extractor = model_data['feature_extractor']
            self.model_performance = model_data.get('performance', {})
            
            self.logger.info(f"Model loaded from {filepath}")
            
        except Exception as e:
            self.logger.error(f"Failed to load model: {e}")
            raise
    
    def get_model_summary(self) -> Dict:
        """Get summary of trained models"""
        if not hasattr(self, 'trained_models'):
            return {'error': 'No models trained yet'}
        
        summary = {
            'models_count': len(self.trained_models),
            'model_names': list(self.trained_models.keys()),
            'performance_summary': {},
            'best_model': None,
            'ensemble_available': bool(self.ensemble_weights)
        }
        
        # Performance summary
        if hasattr(self, 'model_performance'):
            individual_perf = self.model_performance.get('individual_performance', {})
            for model_name, metrics in individual_perf.items():
                summary['performance_summary'][model_name] = {
                    'accuracy': metrics.get('accuracy', 0),
                    'f1_score': metrics.get('f1_score', 0),
                    'roc_auc': metrics.get('roc_auc', 0)
                }
            
            # Best model by F1 score
            if individual_perf:
                best_model = max(individual_perf.keys(),
                               key=lambda x: individual_perf[x].get('f1_score', 0))
                summary['best_model'] = best_model
        
        return summary
