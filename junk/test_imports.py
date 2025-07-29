#!/usr/bin/env python3
"""Test script to debug import issues"""

import sys
import traceback

try:
    print("🔍 Testing imports step by step...")
    
    print("Step 1: Testing app.config import...")
    from app.config import settings
    print(f"✅ Config imported. YouTube API keys: {len(settings.youtube_api_keys)}")
    
    print("Step 2: Testing services import...")
    from app.services.youtube_service import YouTubeAPIService
    print("✅ YouTube service imported")
    
    from app.services.bigquery_service import BigQueryService
    print("✅ BigQuery service imported")
    
    from app.services.gcs_service import GCSService
    print("✅ GCS service imported")
    
    from app.services.database_service import DatabaseService
    print("✅ Database service imported")
    
    from app.services.content_analysis_service import ContentAnalysisService
    print("✅ Content analysis service imported")
    
    print("Step 3: Testing extractor import...")
    from app.extractor import extractor
    print("✅ Extractor imported")
    
    print("Step 4: Testing routes import...")
    from app.routes import extraction, analytics, dashboard, health
    print("✅ Routes imported")
    
    print("Step 5: Testing main app import...")
    from app.main import app
    print("✅ Main app imported successfully!")
    
    print("\n🎉 All imports successful! The modular structure is working correctly.")
    
except Exception as e:
    print(f"\n❌ Import failed at: {e}")
    print("\n📍 Full traceback:")
    traceback.print_exc()
    sys.exit(1)
