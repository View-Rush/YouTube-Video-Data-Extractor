import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from ..extractor import extractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "YouTube Video Data Extractor"
    }


@router.get("/detailed")
async def detailed_health_check():
    """Detailed health check including all services."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {}
    }
    
    overall_healthy = True
    
    # Check YouTube API service
    try:
        youtube_health = await check_youtube_service_health()
        health_status["services"]["youtube_api"] = youtube_health
        if not youtube_health["healthy"]:
            overall_healthy = False
    except Exception as e:
        health_status["services"]["youtube_api"] = {
            "healthy": False,
            "error": str(e)
        }
        overall_healthy = False
    
    # Check BigQuery service
    try:
        bigquery_health = await check_bigquery_service_health()
        health_status["services"]["bigquery"] = bigquery_health
        if not bigquery_health["healthy"]:
            overall_healthy = False
    except Exception as e:
        health_status["services"]["bigquery"] = {
            "healthy": False,
            "error": str(e)
        }
        overall_healthy = False
    
    # Check GCS service
    try:
        gcs_health = await check_gcs_service_health()
        health_status["services"]["gcs"] = gcs_health
        if not gcs_health["healthy"]:
            overall_healthy = False
    except Exception as e:
        health_status["services"]["gcs"] = {
            "healthy": False,
            "error": str(e)
        }
        overall_healthy = False
    
    # Check Database service
    try:
        db_health = await check_database_service_health()
        health_status["services"]["database"] = db_health
        if not db_health["healthy"]:
            overall_healthy = False
    except Exception as e:
        health_status["services"]["database"] = {
            "healthy": False,
            "error": str(e)
        }
        overall_healthy = False
    
    # Check Content Analysis service
    try:
        content_health = await check_content_analysis_service_health()
        health_status["services"]["content_analysis"] = content_health
        if not content_health["healthy"]:
            overall_healthy = False
    except Exception as e:
        health_status["services"]["content_analysis"] = {
            "healthy": False,
            "error": str(e)
        }
        overall_healthy = False
    
    health_status["status"] = "healthy" if overall_healthy else "unhealthy"
    
    if not overall_healthy:
        return health_status, 503
    
    return health_status


async def check_youtube_service_health() -> Dict[str, Any]:
    """Check YouTube API service health."""
    try:
        # Test API connectivity
        test_result = extractor.youtube_service.test_api_connectivity()
        
        return {
            "healthy": test_result["success"],
            "api_keys_count": len(extractor.youtube_service.api_keys),
            "current_key_index": extractor.youtube_service.current_key_index,
            "quota_status": test_result.get("quota_status", "unknown"),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }


async def check_bigquery_service_health() -> Dict[str, Any]:
    """Check BigQuery service health."""
    try:
        # Test BigQuery connectivity
        test_result = extractor.bigquery_service.test_connection()
        
        return {
            "healthy": test_result["success"],
            "project_id": extractor.bigquery_service.project_id,
            "dataset_id": extractor.bigquery_service.dataset_id,
            "tables_exist": test_result.get("tables_exist", False),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }


async def check_gcs_service_health() -> Dict[str, Any]:
    """Check Google Cloud Storage service health."""
    try:
        # Test GCS connectivity
        test_result = extractor.gcs_service.test_connection()
        
        return {
            "healthy": test_result["success"],
            "bucket_name": extractor.gcs_service.bucket_name,
            "bucket_exists": test_result.get("bucket_exists", False),
            "storage_stats": test_result.get("storage_stats", {}),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }


async def check_database_service_health() -> Dict[str, Any]:
    """Check SQLite database service health."""
    try:
        # Test database connectivity
        test_result = extractor.database_service.test_connection()
        
        return {
            "healthy": test_result["success"],
            "database_path": extractor.database_service.db_path,
            "tables_exist": test_result.get("tables_exist", False),
            "record_count": test_result.get("record_count", 0),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }


async def check_content_analysis_service_health() -> Dict[str, Any]:
    """Check Content Analysis service health."""
    try:
        # Test content analysis functionality
        test_content = {
            "title": "Sri Lankan cricket team wins match in Colombo",
            "description": "A great victory for the Sri Lankan team"
        }
        
        analysis_result = extractor.content_analysis_service.analyze_content(test_content)
        
        return {
            "healthy": analysis_result is not None,
            "test_analysis_score": analysis_result.get("sri_lankan_score", 0) if analysis_result else 0,
            "indicators_loaded": len(extractor.content_analysis_service.sri_lankan_indicators),
            "last_check": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "healthy": False,
            "error": str(e),
            "last_check": datetime.now().isoformat()
        }


@router.get("/status")
async def get_extraction_status():
    """Get current extraction status."""
    try:
        status = extractor.get_extraction_status()
        return status
    except Exception as e:
        logger.error(f"Error getting extraction status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/services")
async def get_services_info():
    """Get information about all configured services."""
    try:
        services_info = {
            "youtube_api": {
                "configured": len(extractor.youtube_service.api_keys) > 0,
                "api_keys_count": len(extractor.youtube_service.api_keys),
                "service_name": "YouTube Data API v3"
            },
            "bigquery": {
                "configured": bool(extractor.bigquery_service.project_id),
                "project_id": extractor.bigquery_service.project_id,
                "dataset_id": extractor.bigquery_service.dataset_id,
                "service_name": "Google BigQuery"
            },
            "gcs": {
                "configured": bool(extractor.gcs_service.bucket_name),
                "bucket_name": extractor.gcs_service.bucket_name,
                "service_name": "Google Cloud Storage"
            },
            "database": {
                "configured": bool(extractor.database_service.db_path),
                "database_path": extractor.database_service.db_path,
                "service_name": "SQLite Database"
            },
            "content_analysis": {
                "configured": True,  # Always available
                "indicators_count": len(extractor.content_analysis_service.sri_lankan_indicators),
                "service_name": "Content Analysis Service"
            }
        }
        
        return {
            "services": services_info,
            "total_services": len(services_info),
            "configured_services": sum(1 for service in services_info.values() if service["configured"]),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting services info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get services info: {str(e)}")


@router.post("/test/{service_name}")
async def test_service(service_name: str):
    """Test a specific service."""
    try:
        if service_name == "youtube":
            result = await check_youtube_service_health()
        elif service_name == "bigquery":
            result = await check_bigquery_service_health()
        elif service_name == "gcs":
            result = await check_gcs_service_health()
        elif service_name == "database":
            result = await check_database_service_health()
        elif service_name == "content_analysis":
            result = await check_content_analysis_service_health()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service_name}")
        
        return {
            "service": service_name,
            "test_result": result,
            "tested_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing service {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test service: {str(e)}")


@router.get("/metrics")
async def get_health_metrics():
    """Get system health metrics."""
    try:
        import psutil
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        metrics = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "application": {
                "extraction_running": extractor.is_running,
                "services_count": 5,  # Total number of services
                "uptime": "Unknown"  # Would need to track application start time
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
        
    except ImportError:
        return {
            "error": "psutil not installed",
            "message": "System metrics require psutil package",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting health metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
