import logging
from datetime import datetime
from typing import List
from fastapi import APIRouter, BackgroundTasks, HTTPException

from ..extractor import extractor
from ..models import ExtractionConfig

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["extraction"])


@router.post("/extract")
async def start_enhanced_extraction(config: ExtractionConfig, background_tasks: BackgroundTasks):
    """Start enhanced video extraction for a specific query."""
    if extractor.is_running:
        raise HTTPException(status_code=409, detail="Extraction already running")
    
    # Validate configuration
    if not config.query or not config.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    if config.max_results > 500:
        raise HTTPException(status_code=400, detail="Max results cannot exceed 500")
    
    background_tasks.add_task(extractor.run_extraction_cycle, config)
    
    return {
        "message": "Enhanced extraction started",
        "config": config.dict(),
        "estimated_duration": "2-10 minutes",
        "started_at": datetime.now().isoformat()
    }


@router.post("/extract/scheduled")
async def start_comprehensive_scheduled_extraction(background_tasks: BackgroundTasks):
    """Start comprehensive scheduled extraction for all Sri Lankan content."""
    if extractor.is_running:
        raise HTTPException(status_code=409, detail="Extraction already running")
    
    background_tasks.add_task(extractor.run_comprehensive_scheduled_extraction)
    
    return {
        "message": "Comprehensive scheduled extraction started",
        "estimated_duration": "30-60 minutes",
        "strategies_count": len(extractor.search_strategies),
        "started_at": datetime.now().isoformat()
    }


@router.post("/extract/targeted")
async def start_targeted_extraction(
    targets: List[str], 
    max_results: int = 25, 
    background_tasks: BackgroundTasks = None
):
    """Start targeted extraction for specific queries."""
    if extractor.is_running:
        raise HTTPException(status_code=409, detail="Extraction already running")
    
    if not targets:
        raise HTTPException(status_code=400, detail="No targets provided")
    
    if len(targets) > 20:
        raise HTTPException(status_code=400, detail="Too many targets (max 20)")
    
    if max_results > 100:
        raise HTTPException(status_code=400, detail="Max results per target cannot exceed 100")
    
    background_tasks.add_task(extractor.run_targeted_extraction, targets, max_results)
    
    return {
        "message": "Targeted extraction started",
        "targets": targets,
        "max_results_per_target": max_results,
        "estimated_duration": f"{len(targets) * 2}-{len(targets) * 5} minutes",
        "started_at": datetime.now().isoformat()
    }


@router.post("/extract/stop")
async def stop_extraction():
    """Stop current extraction process."""
    if not extractor.is_running:
        raise HTTPException(status_code=400, detail="No extraction currently running")
    
    success = extractor.stop_extraction()
    
    if success:
        return {
            "message": "Extraction stopped successfully",
            "stopped_at": datetime.now().isoformat()
        }
    else:
        raise HTTPException(status_code=500, detail="Failed to stop extraction")


@router.get("/status")
async def get_extraction_status():
    """Get detailed extraction status, progress, and metrics."""
    try:
        status = extractor.get_extraction_status()
        return status
    except Exception as e:
        logger.error(f"Error getting extraction status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/sessions/{session_id}")
async def get_extraction_session(session_id: str):
    """Get details of a specific extraction session."""
    try:
        session_data = extractor.database_service.get_extraction_session(session_id)
        
        if not session_data:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return session_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting extraction session: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get session: {str(e)}")


@router.get("/sessions")
async def list_extraction_sessions(limit: int = 20, status: str = None):
    """List recent extraction sessions."""
    try:
        # This would require adding a method to database_service
        # For now, return a simple response
        return {
            "message": "Session listing not yet implemented",
            "limit": limit,
            "status_filter": status
        }
    except Exception as e:
        logger.error(f"Error listing extraction sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


@router.get("/queries")
async def get_search_queries():
    """Get available search queries and categories."""
    try:
        return {
            "strategies": extractor.search_strategies,
            "total_strategies": len(extractor.search_strategies),
            "categories": list(set(strategy.get("category", "general") for strategy in extractor.search_strategies))
        }
    except Exception as e:
        logger.error(f"Error getting search queries: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get queries: {str(e)}")


@router.post("/queries/validate")
async def validate_search_query(query: str):
    """Validate a search query and provide suggestions."""
    try:
        if not query or not query.strip():
            raise HTTPException(status_code=400, detail="Query cannot be empty")
        
        # Basic validation
        validation_result = {
            "query": query,
            "is_valid": True,
            "suggestions": [],
            "warnings": []
        }
        
        # Check query length
        if len(query) > 100:
            validation_result["warnings"].append("Query is very long, consider shortening it")
        
        # Check for Sri Lankan relevance
        sri_lankan_keywords = ["sri lanka", "colombo", "kandy", "sinhala", "tamil", "ceylon"]
        has_sri_lankan_keyword = any(keyword in query.lower() for keyword in sri_lankan_keywords)
        
        if not has_sri_lankan_keyword:
            validation_result["suggestions"].append("Consider adding 'Sri Lanka' to improve relevance")
        
        return validation_result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error validating search query: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate query: {str(e)}")
        raise HTTPException(status_code=409, detail="Extraction already running")
    
    if not targets:
        raise HTTPException(status_code=400, detail="No targets provided")
    
    if len(targets) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 targets allowed")
    
    if background_tasks:
        background_tasks.add_task(extractor.run_targeted_extraction, targets, max_results)
        return {
            "message": f"Targeted extraction started for {len(targets)} targets",
            "targets": targets,
            "max_results_per_target": max_results,
            "started_at": datetime.now().isoformat()
        }
    else:
        # Synchronous execution for immediate results
        results = await extractor.run_targeted_extraction(targets, max_results)
        return {
            "message": "Targeted extraction completed",
            "results": results,
            "completed_at": datetime.now().isoformat()
        }