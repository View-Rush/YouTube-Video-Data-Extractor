import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query

from ..extractor import extractor

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/overview")
async def get_analytics_overview():
    """Get comprehensive analytics overview."""
    try:
        # Get data from BigQuery if available
        bigquery_stats = {}
        try:
            bigquery_stats = extractor.bigquery_service.get_analytics_overview()
        except Exception as e:
            logger.warning(f"Failed to get BigQuery analytics: {e}")
        
        # Get database statistics
        db_stats = {}
        try:
            db_stats = extractor.database_service.get_statistics()
        except Exception as e:
            logger.warning(f"Failed to get database statistics: {e}")
        
        # Combine analytics
        overview = {
            "summary": {
                "total_videos": db_stats.get("total_videos", 0),
                "sri_lankan_videos": db_stats.get("sri_lankan_videos", 0),
                "total_views": bigquery_stats.get("total_views", 0),
                "total_likes": bigquery_stats.get("total_likes", 0),
                "unique_channels": bigquery_stats.get("unique_channels", 0),
                "last_updated": datetime.now().isoformat()
            },
            "bigquery": bigquery_stats,
            "database": db_stats
        }
        
        return overview
        
    except Exception as e:
        logger.error(f"Error getting analytics overview: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get overview: {str(e)}")


@router.get("/trending")
async def get_trending_analysis(
    time_period: str = Query("7d", description="Time period: 1d, 7d, 30d, 90d"),
    limit: int = Query(50, description="Number of videos to return")
):
    """Get trending video analysis."""
    try:
        # Parse time period
        days_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}
        days = days_map.get(time_period, 7)
        
        # Get trending data from BigQuery
        trending_data = {}
        try:
            trending_data = extractor.bigquery_service.get_trending_analysis(days, limit)
        except Exception as e:
            logger.warning(f"Failed to get trending analysis: {e}")
            trending_data = {
                "videos": [],
                "message": f"BigQuery trending analysis not available: {str(e)}"
            }
        
        return {
            "time_period": time_period,
            "days": days,
            "limit": limit,
            "trending": trending_data,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting trending analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get trending data: {str(e)}")


@router.get("/channels")
async def get_channel_analytics(
    sort_by: str = Query("subscriber_count", description="Sort by: subscriber_count, video_count, avg_views"),
    limit: int = Query(25, description="Number of channels to return")
):
    """Get top channels analytics."""
    try:
        # Get channel data from BigQuery
        channel_data = {}
        try:
            channel_data = extractor.bigquery_service.get_channel_analytics(sort_by, limit)
        except Exception as e:
            logger.warning(f"Failed to get channel analytics: {e}")
            channel_data = {
                "channels": [],
                "message": f"BigQuery channel analytics not available: {str(e)}"
            }
        
        return {
            "sort_by": sort_by,
            "limit": limit,
            "channels": channel_data,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting channel analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get channel data: {str(e)}")


@router.get("/categories")
async def get_category_distribution():
    """Get video category distribution."""
    try:
        # Get category data from BigQuery
        category_data = {}
        try:
            category_data = extractor.bigquery_service.get_category_distribution()
        except Exception as e:
            logger.warning(f"Failed to get category distribution: {e}")
            category_data = {
                "categories": [],
                "message": f"BigQuery category analysis not available: {str(e)}"
            }
        
        return {
            "distribution": category_data,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting category distribution: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get category data: {str(e)}")


@router.get("/publishing-patterns")
async def get_publishing_patterns(
    granularity: str = Query("daily", description="Granularity: hourly, daily, weekly, monthly")
):
    """Get video publishing time patterns."""
    try:
        # Get publishing pattern data from BigQuery
        pattern_data = {}
        try:
            pattern_data = extractor.bigquery_service.get_publishing_patterns(granularity)
        except Exception as e:
            logger.warning(f"Failed to get publishing patterns: {e}")
            pattern_data = {
                "patterns": [],
                "message": f"BigQuery publishing pattern analysis not available: {str(e)}"
            }
        
        return {
            "granularity": granularity,
            "patterns": pattern_data,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting publishing patterns: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get pattern data: {str(e)}")


@router.get("/content-analysis")
async def get_content_analysis():
    """Get Sri Lankan content analysis."""
    try:
        # Get content analysis data
        analysis_data = {}
        try:
            analysis_data = extractor.bigquery_service.get_content_analysis()
        except Exception as e:
            logger.warning(f"Failed to get content analysis: {e}")
            analysis_data = {
                "message": f"BigQuery content analysis not available: {str(e)}"
            }
        
        # Add content analysis service insights
        sri_lankan_indicators = {
            "locations": extractor.content_analysis_service.sri_lankan_indicators["locations"],
            "cultural_terms": extractor.content_analysis_service.sri_lankan_indicators["cultural_terms"],
            "political_terms": extractor.content_analysis_service.sri_lankan_indicators["political_terms"],
            "business_terms": extractor.content_analysis_service.sri_lankan_indicators["business_terms"]
        }
        
        return {
            "analysis": analysis_data,
            "indicators": sri_lankan_indicators,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting content analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get content analysis: {str(e)}")


@router.get("/search-performance")
async def get_search_performance():
    """Get search query performance analytics."""
    try:
        # Get database statistics about searches
        search_stats = {}
        try:
            search_stats = extractor.database_service.get_search_performance()
        except Exception as e:
            logger.warning(f"Failed to get search performance: {e}")
            search_stats = {"message": f"Search performance data not available: {str(e)}"}
        
        # Add search strategies information
        strategies_info = {
            "total_strategies": len(extractor.search_strategies),
            "strategies": extractor.search_strategies[:10],  # First 10 for preview
            "categories": list(set(strategy.get("category", "general") for strategy in extractor.search_strategies))
        }
        
        return {
            "performance": search_stats,
            "strategies": strategies_info,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting search performance: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get search performance: {str(e)}")


@router.get("/api-usage")
async def get_api_usage_analytics(
    time_period: str = Query("7d", description="Time period: 1d, 7d, 30d")
):
    """Get YouTube API usage analytics."""
    try:
        # Parse time period
        days_map = {"1d": 1, "7d": 7, "30d": 30}
        days = days_map.get(time_period, 7)
        
        # Get API usage data
        api_stats = {}
        try:
            api_stats = extractor.database_service.get_api_usage_stats(days)
        except Exception as e:
            logger.warning(f"Failed to get API usage stats: {e}")
            api_stats = {"message": f"API usage data not available: {str(e)}"}
        
        # Add current API key status
        api_status = {
            "total_keys": len(extractor.youtube_service.api_keys),
            "current_key_index": extractor.youtube_service.current_key_index,
            "quota_exceeded_count": getattr(extractor.youtube_service, 'quota_exceeded_count', 0)
        }
        
        return {
            "time_period": time_period,
            "days": days,
            "usage": api_stats,
            "status": api_status,
            "generated_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting API usage analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get API usage: {str(e)}")


@router.post("/export")
async def export_analytics_data(
    format: str = Query("json", description="Export format: json, csv"),
    data_type: str = Query("overview", description="Data type: overview, videos, channels, analytics")
):
    """Export analytics data in specified format."""
    try:
        if format not in ["json", "csv"]:
            raise HTTPException(status_code=400, detail="Format must be 'json' or 'csv'")
        
        if data_type not in ["overview", "videos", "channels", "analytics"]:
            raise HTTPException(status_code=400, detail="Invalid data type")
        
        # For now, return a placeholder
        return {
            "message": "Export functionality not yet implemented",
            "format": format,
            "data_type": data_type,
            "generated_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to export data: {str(e)}")
