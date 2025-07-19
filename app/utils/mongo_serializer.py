"""
MongoDB document serialization utilities for FastAPI
"""
from datetime import datetime
from typing import Any, Dict, List, Union
from bson import ObjectId

def serialize_mongo_document(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB document to JSON-serializable format
    - Convert ObjectId to string
    - Convert datetime to ISO string
    - Handle nested documents recursively
    """
    if doc is None:
        return None
    
    result = {}
    
    for key, value in doc.items():
        if key == "_id":
            # Convert ObjectId to string with key "id"
            result["id"] = str(value)
        elif isinstance(value, ObjectId):
            # Convert any other ObjectId fields to string
            result[key] = str(value)
        elif isinstance(value, datetime):
            # Convert datetime to ISO string
            result[key] = value.isoformat()
        elif isinstance(value, dict):
            # Recursively handle nested documents
            result[key] = serialize_mongo_document(value)
        elif isinstance(value, list):
            # Handle lists that might contain documents
            result[key] = [
                serialize_mongo_document(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            # Keep other values as-is
            result[key] = value
    
    return result

def serialize_mongo_documents(docs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert list of MongoDB documents to JSON-serializable format
    """
    return [serialize_mongo_document(doc) for doc in docs]

def clean_mongo_response(data: Union[Dict[str, Any], List[Dict[str, Any]]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Clean MongoDB response data for JSON serialization
    """
    if isinstance(data, list):
        return serialize_mongo_documents(data)
    elif isinstance(data, dict):
        return serialize_mongo_document(data)
    else:
        return data
