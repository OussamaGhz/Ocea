"""
Anomaly Detection Module for Pond Monitoring

This module provides anomaly detection capabilities using either:
1. Machine Learning models (Random Forest + Isolation Forest) if scikit-learn is available
2. Rule-based detection as fallback
"""

import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

# Try to import ML libraries
try:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier, IsolationForest
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import classification_report
    import joblib
    SKLEARN_AVAILABLE = True
    logger.info("scikit-learn is available - ML models enabled")
except ImportError as e:
    SKLEARN_AVAILABLE = False
    logger.warning(f"scikit-learn not available ({e}) - using rule-based detection only")


class AnomalyDetector:
    """Anomaly detector with ML and rule-based fallback"""
    
    def __init__(self):
        self.feature_columns = [
            'temperature', 'ph', 'dissolved_oxygen', 'turbidity',
            'ammonia', 'nitrite', 'nitrate', 'salinity', 'water_level'
        ]
        
        # Normal ranges for water quality parameters
        self.normal_ranges = {
            'temperature': (20.0, 30.0),      # Celsius
            'ph': (6.5, 8.5),                # pH units
            'dissolved_oxygen': (5.0, 12.0),  # mg/L
            'turbidity': (0.0, 50.0),         # NTU
            'ammonia': (0.0, 0.5),            # mg/L
            'nitrite': (0.0, 0.1),            # mg/L
            'nitrate': (0.0, 40.0),           # mg/L
            'salinity': (0.0, 35.0),          # ppt
            'water_level': (50.0, 200.0)      # cm
        }
        
        # Critical thresholds
        self.critical_ranges = {
            'temperature': (15.0, 35.0),
            'ph': (6.0, 9.0),
            'dissolved_oxygen': (3.0, 15.0),
            'turbidity': (0.0, 100.0),
            'ammonia': (0.0, 1.0),
            'nitrite': (0.0, 0.5),
            'nitrate': (0.0, 80.0),
            'salinity': (0.0, 40.0),
            'water_level': (30.0, 250.0)
        }
        
        self.is_trained = False
        
        # Initialize ML models if available
        if SKLEARN_AVAILABLE:
            self.random_forest = RandomForestClassifier(
                n_estimators=100, random_state=42, class_weight='balanced'
            )
            self.isolation_forest = IsolationForest(
                contamination=0.1, random_state=42
            )
            self.scaler = StandardScaler()

    def detect_anomaly(self, reading) -> Tuple[bool, float, List[str]]:
        """
        Detect if a reading is anomalous
        
        Returns: (is_anomaly, anomaly_score, reasons)
        """
        if SKLEARN_AVAILABLE and self.is_trained:
            return self._ml_detection(reading)
        else:
            return self._rule_based_detection(reading)

    def _rule_based_detection(self, reading) -> Tuple[bool, float, List[str]]:
        """Rule-based anomaly detection"""
        reasons = []
        severity_scores = []
        
        for param, (min_val, max_val) in self.normal_ranges.items():
            value = getattr(reading, param, None)
            if value is not None:
                if value < min_val:
                    severity = min((min_val - value) / min_val, 1.0)
                    reasons.append(f"{param} below normal: {value:.2f} < {min_val}")
                    severity_scores.append(severity)
                elif value > max_val:
                    severity = min((value - max_val) / max_val, 1.0)
                    reasons.append(f"{param} above normal: {value:.2f} > {max_val}")
                    severity_scores.append(severity)
                
                # Check critical ranges for higher severity
                critical_min, critical_max = self.critical_ranges.get(param, (min_val, max_val))
                if value < critical_min or value > critical_max:
                    severity_scores.append(1.0)
        
        anomaly_score = max(severity_scores) if severity_scores else 0.0
        is_anomaly = len(reasons) > 0
        
        return is_anomaly, anomaly_score, reasons

    def _ml_detection(self, reading) -> Tuple[bool, float, List[str]]:
        """ML-based anomaly detection (when sklearn is available)"""
        try:
            # Prepare features
            features = []
            for col in self.feature_columns:
                value = getattr(reading, col, None)
                features.append(value if value is not None else 0.0)
            
            # Add temporal features
            features.extend([reading.timestamp.hour, reading.timestamp.weekday()])
            
            # Scale features
            features_array = np.array(features).reshape(1, -1)
            scaled_features = self.scaler.transform(features_array)
            
            # Get predictions
            rf_pred = 0
            rf_prob = 0.0
            if hasattr(self.random_forest, 'classes_'):
                rf_pred = self.random_forest.predict(scaled_features)[0]
                if len(self.random_forest.classes_) > 1:
                    rf_prob = self.random_forest.predict_proba(scaled_features)[0][1]
            
            iso_pred = self.isolation_forest.predict(scaled_features)[0]
            iso_score = abs(self.isolation_forest.decision_function(scaled_features)[0])
            
            # Combine results
            is_anomaly_rf = rf_pred == 1
            is_anomaly_iso = iso_pred == -1
            is_anomaly = is_anomaly_rf or is_anomaly_iso
            
            anomaly_score = max(rf_prob, iso_score if is_anomaly_iso else 0)
            
            # Get reasons
            reasons = []
            if is_anomaly_rf:
                reasons.append("ML model detected unusual pattern")
            if is_anomaly_iso:
                reasons.append("Outlier detection triggered")
            
            # Add rule-based reasons for context
            _, _, rule_reasons = self._rule_based_detection(reading)
            reasons.extend(rule_reasons)
            
            return is_anomaly, min(anomaly_score, 1.0), reasons
            
        except Exception as e:
            logger.error(f"ML detection failed: {e}, falling back to rule-based")
            return self._rule_based_detection(reading)

    def train_model(self, readings: List) -> Dict:
        """Train ML models or configure rule-based detector"""
        if not SKLEARN_AVAILABLE:
            return self._configure_rule_based(readings)
        
        if len(readings) < 50:
            logger.warning("Insufficient data for ML training, configuring rule-based detector")
            return self._configure_rule_based(readings)
        
        try:
            # Prepare training data
            features_list = []
            labels = []
            
            for reading in readings:
                # Extract features
                features = []
                for col in self.feature_columns:
                    value = getattr(reading, col, None)
                    features.append(value if value is not None else 0.0)
                
                # Add temporal features
                features.extend([reading.timestamp.hour, reading.timestamp.weekday()])
                features_list.append(features)
                
                # Use existing anomaly labels or create from rules
                if hasattr(reading, 'is_anomaly') and reading.is_anomaly is not None:
                    labels.append(1 if reading.is_anomaly else 0)
                else:
                    # Generate label from rule-based detection
                    is_anomaly, _, _ = self._rule_based_detection(reading)
                    labels.append(1 if is_anomaly else 0)
            
            # Convert to numpy arrays
            X = np.array(features_list)
            y = np.array(labels)
            
            # Scale features
            X_scaled = self.scaler.fit_transform(X)
            
            # Train Random Forest if we have both classes
            if len(np.unique(y)) > 1:
                self.random_forest.fit(X_scaled, y)
                logger.info("Random Forest model trained successfully")
            
            # Train Isolation Forest
            self.isolation_forest.fit(X_scaled)
            logger.info("Isolation Forest model trained successfully")
            
            self.is_trained = True
            
            return {
                "status": "success",
                "message": f"ML models trained on {len(readings)} readings",
                "anomaly_ratio": np.mean(y),
                "features_used": len(self.feature_columns) + 2  # +2 for temporal features
            }
            
        except Exception as e:
            logger.error(f"ML training failed: {e}, using rule-based detector")
            return self._configure_rule_based(readings)

    def _configure_rule_based(self, readings: List) -> Dict:
        """Configure rule-based detector with data statistics"""
        param_stats = {}
        
        for param in self.feature_columns:
            values = []
            for reading in readings:
                value = getattr(reading, param, None)
                if value is not None:
                    values.append(value)
            
            if values:
                param_stats[param] = {
                    'mean': sum(values) / len(values),
                    'min': min(values),
                    'max': max(values),
                    'count': len(values)
                }
        
        self.is_trained = True
        
        return {
            "status": "success",
            "message": f"Rule-based detector configured with {len(readings)} readings",
            "method": "rule_based",
            "parameter_statistics": param_stats
        }

    def get_feature_importance(self) -> Dict[str, float]:
        """Get feature importance"""
        if SKLEARN_AVAILABLE and self.is_trained and hasattr(self.random_forest, 'feature_importances_'):
            features = self.feature_columns + ['hour', 'day_of_week']
            importance = dict(zip(features, self.random_forest.feature_importances_))
            return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
        else:
            # Return equal importance for rule-based
            importance = 1.0 / len(self.feature_columns)
            return {feature: importance for feature in self.feature_columns}

    def save_model(self, filepath: str):
        """Save model to file"""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if SKLEARN_AVAILABLE and self.is_trained:
            try:
                model_data = {
                    'random_forest': self.random_forest,
                    'isolation_forest': self.isolation_forest,
                    'scaler': self.scaler,
                    'feature_columns': self.feature_columns,
                    'normal_ranges': self.normal_ranges,
                    'is_trained': self.is_trained,
                    'sklearn_available': True
                }
                joblib.dump(model_data, filepath)
                logger.info(f"ML model saved to {filepath}")
                return
            except Exception as e:
                logger.error(f"Failed to save ML model: {e}")
        
        # Fallback to JSON
        config = {
            'normal_ranges': self.normal_ranges,
            'critical_ranges': self.critical_ranges,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained,
            'sklearn_available': False
        }
        
        json_filepath = filepath.replace('.pkl', '.json')
        with open(json_filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Rule-based configuration saved to {json_filepath}")

    def load_model(self, filepath: str):
        """Load model from file"""
        if SKLEARN_AVAILABLE:
            try:
                model_data = joblib.load(filepath)
                if model_data.get('sklearn_available', False):
                    self.random_forest = model_data['random_forest']
                    self.isolation_forest = model_data['isolation_forest']
                    self.scaler = model_data['scaler']
                    self.feature_columns = model_data['feature_columns']
                    self.normal_ranges = model_data.get('normal_ranges', self.normal_ranges)
                    self.is_trained = model_data['is_trained']
                    logger.info(f"ML model loaded from {filepath}")
                    return
            except Exception as e:
                logger.warning(f"Failed to load ML model: {e}, trying JSON config")
        
        # Try loading JSON config
        json_filepath = filepath.replace('.pkl', '.json')
        if os.path.exists(json_filepath):
            try:
                with open(json_filepath, 'r') as f:
                    config = json.load(f)
                
                self.normal_ranges = config.get('normal_ranges', self.normal_ranges)
                self.critical_ranges = config.get('critical_ranges', self.critical_ranges)
                self.feature_columns = config.get('feature_columns', self.feature_columns)
                self.is_trained = config.get('is_trained', False)
                
                logger.info(f"Rule-based configuration loaded from {json_filepath}")
            except Exception as e:
                logger.error(f"Failed to load configuration: {e}")


# Global instance
anomaly_detector = AnomalyDetector()
