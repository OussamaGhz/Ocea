import logging
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Simple rule-based anomaly detector for pond monitoring"""
    
    def __init__(self):
        self.is_trained = False
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
        
        # Critical thresholds for severe anomalies
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

    def detect_anomaly(self, reading) -> Tuple[bool, float, List[str]]:
        """
        Detect if a reading is anomalous using rule-based approach
        
        Args:
            reading: SensorReading object
            
        Returns:
            Tuple of (is_anomaly, anomaly_score, reasons)
        """
        reasons = []
        anomaly_score = 0.0
        severity_scores = []
        
        for param, (min_val, max_val) in self.normal_ranges.items():
            value = getattr(reading, param, None)
            if value is not None:
                # Check normal ranges
                if value < min_val:
                    severity = (min_val - value) / min_val
                    reasons.append(f"{param} below normal: {value:.2f} < {min_val}")
                    severity_scores.append(severity)
                elif value > max_val:
                    severity = (value - max_val) / max_val
                    reasons.append(f"{param} above normal: {value:.2f} > {max_val}")
                    severity_scores.append(severity)
                
                # Check critical ranges
                critical_min, critical_max = self.critical_ranges.get(param, (min_val, max_val))
                if value < critical_min or value > critical_max:
                    if f"{param} below normal" not in ' '.join(reasons) and f"{param} above normal" not in ' '.join(reasons):
                        reasons.append(f"{param} at critical level: {value:.2f}")
                    severity_scores.append(1.0)  # Maximum severity for critical values
        
        # Calculate overall anomaly score
        if severity_scores:
            anomaly_score = min(max(severity_scores), 1.0)
        
        is_anomaly = len(reasons) > 0
        
        # Log anomaly detection
        if is_anomaly:
            logger.info(f"Anomaly detected for pond {reading.pond_id}: {reasons}")
        
        return is_anomaly, anomaly_score, reasons

    def train_model(self, readings: List) -> Dict:
        """
        Placeholder for model training - currently rule-based only
        
        Args:
            readings: List of SensorReading objects
            
        Returns:
            Dictionary with training status
        """
        if len(readings) < 10:
            return {
                "status": "insufficient_data", 
                "message": f"Only {len(readings)} readings provided, need at least 10"
            }
        
        # Analyze the data to potentially adjust normal ranges
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
            "parameter_statistics": param_stats,
            "normal_ranges": self.normal_ranges
        }

    def get_feature_importance(self) -> Dict[str, float]:
        """
        Return equal importance for all features in rule-based approach
        """
        if not self.feature_columns:
            return {}
        
        importance = 1.0 / len(self.feature_columns)
        return {feature: importance for feature in self.feature_columns}

    def save_model(self, filepath: str):
        """Save detector configuration to JSON file"""
        config = {
            'normal_ranges': self.normal_ranges,
            'critical_ranges': self.critical_ranges,
            'feature_columns': self.feature_columns,
            'is_trained': self.is_trained
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"Detector configuration saved to {filepath}")

    def load_model(self, filepath: str):
        """Load detector configuration from JSON file"""
        try:
            with open(filepath, 'r') as f:
                config = json.load(f)
            
            self.normal_ranges = config.get('normal_ranges', self.normal_ranges)
            self.critical_ranges = config.get('critical_ranges', self.critical_ranges)
            self.feature_columns = config.get('feature_columns', self.feature_columns)
            self.is_trained = config.get('is_trained', False)
            
            logger.info(f"Detector configuration loaded from {filepath}")
        except Exception as e:
            logger.error(f"Failed to load detector configuration: {e}")

    def update_normal_ranges(self, new_ranges: Dict[str, Tuple[float, float]]):
        """Update normal ranges for parameters"""
        for param, (min_val, max_val) in new_ranges.items():
            if param in self.normal_ranges:
                self.normal_ranges[param] = (min_val, max_val)
                logger.info(f"Updated normal range for {param}: {min_val} - {max_val}")


# Global instance
anomaly_detector = AnomalyDetector()
