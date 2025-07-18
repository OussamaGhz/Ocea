from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from app.database.connection import get_database
from app.services.database_service import SensorReadingService
from app.ml.anomaly_detection import anomaly_detector
from app.auth.auth import get_current_admin_user
from app.models.models import User

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.post("/train")
async def train_anomaly_model(
    db=Depends(get_database),
    current_user: User = Depends(get_current_admin_user)
):
    """Train the anomaly detection model (Admin only)"""
    reading_service = SensorReadingService(db)
    
    # Get all sensor readings for training
    # Note: In production, you might want to limit this or use pagination
    try:
        # Get readings from multiple ponds
        all_readings = []
        
        # This is a simplified approach - in production you'd want to:
        # 1. Get readings from all ponds the admin has access to
        # 2. Use pagination to handle large datasets
        # 3. Implement more sophisticated data selection
        
        # For now, we'll get a sample of readings
        # You can modify this logic based on your specific needs
        cursor = db.sensor_readings.find().limit(10000)
        async for reading_data in cursor:
            from app.models.models import SensorReading
            reading = SensorReading(**reading_data)
            all_readings.append(reading)
        
        if len(all_readings) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient data for training. Need at least 50 readings."
            )
        
        # Train the model
        result = anomaly_detector.train_model(all_readings)
        
        # Save the trained model
        anomaly_detector.save_model("models/anomaly_detector.pkl")
        
        return {
            "message": "Model training completed",
            "training_result": result,
            "readings_used": len(all_readings)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error training model: {str(e)}"
        )


@router.get("/model-info")
async def get_model_info(
    current_user: User = Depends(get_current_admin_user)
):
    """Get information about the current ML model (Admin only)"""
    try:
        feature_importance = anomaly_detector.get_feature_importance()
        
        return {
            "is_trained": anomaly_detector.is_trained,
            "feature_columns": anomaly_detector.feature_columns,
            "normal_ranges": anomaly_detector.normal_ranges,
            "feature_importance": feature_importance
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting model info: {str(e)}"
        )


@router.post("/predict/{reading_id}")
async def predict_anomaly(
    reading_id: str,
    db=Depends(get_database),
    current_user: User = Depends(get_current_admin_user)
):
    """Run anomaly detection on a specific reading (Admin only)"""
    reading_service = SensorReadingService(db)
    
    # Get the reading
    reading = await reading_service.get_reading_by_id(reading_id)
    if not reading:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reading not found"
        )
    
    try:
        # Perform anomaly detection
        is_anomaly, anomaly_score, reasons = anomaly_detector.detect_anomaly(reading)
        
        # Update the reading with results
        updated_reading = await reading_service.update_reading_anomaly(
            reading_id, is_anomaly, anomaly_score, reasons
        )
        
        return {
            "reading_id": reading_id,
            "is_anomaly": is_anomaly,
            "anomaly_score": anomaly_score,
            "reasons": reasons,
            "updated": updated_reading is not None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error predicting anomaly: {str(e)}"
        )


@router.get("/stats")
async def get_ml_stats(
    db=Depends(get_database),
    current_user: User = Depends(get_current_admin_user)
):
    """Get ML-related statistics (Admin only)"""
    try:
        # Get statistics from database
        total_readings = await db.sensor_readings.count_documents({})
        anomaly_readings = await db.sensor_readings.count_documents({"is_anomaly": True})
        
        anomaly_rate = (anomaly_readings / total_readings * 100) if total_readings > 0 else 0
        
        # Get recent anomalies by pond
        pipeline = [
            {"$match": {"is_anomaly": True}},
            {"$group": {
                "_id": "$pond_id",
                "count": {"$sum": 1},
                "latest_anomaly": {"$max": "$timestamp"}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 10}
        ]
        
        anomalies_by_pond = []
        async for doc in db.sensor_readings.aggregate(pipeline):
            anomalies_by_pond.append(doc)
        
        return {
            "total_readings": total_readings,
            "anomaly_readings": anomaly_readings,
            "anomaly_rate_percent": round(anomaly_rate, 2),
            "model_trained": anomaly_detector.is_trained,
            "anomalies_by_pond": anomalies_by_pond
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting ML stats: {str(e)}"
        )
