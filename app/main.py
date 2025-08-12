import os
from dotenv import load_dotenv
import logging
from fastapi import FastAPI
from fastapi.concurrency import asynccontextmanager
import schedule
import asyncio
import time
import threading
from .extractor import extractor
from .routes import extraction, analytics, dashboard, health

load_dotenv()

os.makedirs('logs', exist_ok=True)

# Handlers
file_handler = logging.FileHandler('logs/youtube_extractor.log')
error_handler = logging.FileHandler('logs/error.log')
error_handler.setLevel(logging.ERROR)  # Set level after creation
console_handler = logging.StreamHandler()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        file_handler,
        error_handler,
        console_handler
    ]
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting YouTube Data Extractor FastAPI application")
    
    # Start background scheduler for automatic extractions
    def run_scheduler():
        # Schedule extraction every 2 minutes
        schedule.every(2).minutes.do(lambda: asyncio.create_task(extractor.run_comprehensive_scheduled_extraction()))
        
        # Schedule quick updates every hour
        schedule.every(1).hour.do(lambda: asyncio.create_task(extractor.run_targeted_extraction(['Sri Lanka news', 'Sri Lanka'], 25)))
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    
    yield
    
    # Shutdown
    logger.info("Shutting down YouTube Data Extractor")

app = FastAPI(
    title="YouTube Data Extractor for Sri Lanka",
    description="Comprehensive YouTube video data collection and analysis platform for Sri Lankan content",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(extraction.router)
app.include_router(analytics.router)
app.include_router(dashboard.router)
app.include_router(health.router)