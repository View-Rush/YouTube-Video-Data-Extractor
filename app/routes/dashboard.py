import logging
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

from ..extractor import extractor

logger = logging.getLogger(__name__)
router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Main dashboard showing extraction status and statistics."""
    try:
        # Get extraction status
        status = extractor.get_extraction_status()
        
        # Get basic statistics
        stats = {
            "total_videos": 0,
            "videos_today": 0,
            "sri_lankan_videos": 0,
            "api_calls_today": 0,
            "last_extraction": "Never",
            "database_size": 0
        }
        
        try:
            # Get database statistics
            db_stats = extractor.database_service.get_statistics()
            if db_stats:
                stats.update(db_stats)
        except Exception as e:
            logger.warning(f"Failed to get database statistics: {e}")
        
        # Get BigQuery statistics if available
        bigquery_stats = {}
        try:
            bigquery_stats = extractor.bigquery_service.get_statistics()
        except Exception as e:
            logger.warning(f"Failed to get BigQuery statistics: {e}")
        
        # Get GCS statistics if available
        gcs_stats = {}
        try:
            gcs_stats = extractor.gcs_service.get_storage_statistics()
        except Exception as e:
            logger.warning(f"Failed to get GCS statistics: {e}")
        
        context = {
            "request": request,
            "status": status,
            "stats": stats,
            "bigquery_stats": bigquery_stats,
            "gcs_stats": gcs_stats,
            "current_time": datetime.now().isoformat(),
            "search_strategies_count": len(extractor.search_strategies)
        }
        
        return templates.TemplateResponse("dashboard.html", context)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        # Return a simple error page
        error_context = {
            "request": request,
            "error": str(e),
            "current_time": datetime.now().isoformat()
        }
        return templates.TemplateResponse("dashboard.html", error_context)


@router.get("/api/dashboard/stats")
async def get_dashboard_stats():
    """Get dashboard statistics as JSON."""
    try:
        # Get extraction status
        status = extractor.get_extraction_status()
        
        # Get database statistics
        db_stats = {}
        try:
            db_stats = extractor.database_service.get_statistics()
        except Exception as e:
            logger.warning(f"Failed to get database statistics: {e}")
        
        # Get BigQuery statistics
        bigquery_stats = {}
        try:
            bigquery_stats = extractor.bigquery_service.get_statistics()
        except Exception as e:
            logger.warning(f"Failed to get BigQuery statistics: {e}")
        
        # Get GCS statistics
        gcs_stats = {}
        try:
            gcs_stats = extractor.gcs_service.get_storage_statistics()
        except Exception as e:
            logger.warning(f"Failed to get GCS statistics: {e}")
        
        return {
            "status": status,
            "database": db_stats,
            "bigquery": bigquery_stats,
            "gcs": gcs_stats,
            "search_strategies_count": len(extractor.search_strategies),
            "last_updated": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.get("/api/dashboard/recent-videos")
async def get_recent_videos(limit: int = 20):
    """Get recently extracted videos."""
    try:
        # This would require adding a method to database_service
        # For now, return a placeholder
        return {
            "videos": [],
            "total": 0,
            "limit": limit,
            "message": "Recent videos endpoint not yet implemented"
        }
        
    except Exception as e:
        logger.error(f"Error getting recent videos: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent videos: {str(e)}")


@router.get("/api/dashboard/activity")
async def get_activity_log(limit: int = 50):
    """Get recent activity log."""
    try:
        # This would require adding activity logging
        # For now, return extraction status changes
        status = extractor.get_extraction_status()
        
        activity = [
            {
                "timestamp": datetime.now().isoformat(),
                "type": "status_check",
                "message": f"Extraction status: {'Running' if status.get('is_running') else 'Idle'}",
                "details": status
            }
        ]
        
        return {
            "activity": activity,
            "total": len(activity),
            "limit": limit
        }
        
    except Exception as e:
        logger.error(f"Error getting activity log: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get activity: {str(e)}")


@router.get("/api/dashboard/performance")
async def get_performance_metrics():
    """Get system performance metrics."""
    try:
        import psutil
        import sys
        
        # Get system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get Python process metrics
        process = psutil.Process()
        process_memory = process.memory_info()
        
        metrics = {
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "disk_percent": disk.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2)
            },
            "process": {
                "memory_mb": round(process_memory.rss / (1024**2), 2),
                "cpu_percent": process.cpu_percent(),
                "python_version": sys.version.split()[0],
                "pid": process.pid
            },
            "extractor": {
                "is_running": extractor.is_running,
                "session_id": getattr(extractor, 'current_session_id', None),
                "api_keys_count": len(extractor.youtube_service.api_keys),
                "search_strategies_count": len(extractor.search_strategies)
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return metrics
        
    except ImportError:
        return {
            "error": "psutil not installed",
            "message": "Performance metrics require psutil package",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")
