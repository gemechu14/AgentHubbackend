# app/services/scheduler_service.py
"""
Scheduler service for pipeline jobs and background tasks.
Uses APScheduler for managing scheduled tasks.
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
import logging

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: BackgroundScheduler | None = None


def get_scheduler() -> BackgroundScheduler | None:
    """Get the global scheduler instance."""
    return _scheduler


def start_scheduler() -> None:
    """
    Start the background scheduler.
    This will initialize APScheduler and start running scheduled jobs.
    """
    global _scheduler
    
    if _scheduler is not None and _scheduler.running:
        logger.warning("Scheduler is already running")
        return
    
    # Configure scheduler with thread pool executor
    executors = {
        'default': ThreadPoolExecutor(5)
    }
    
    job_defaults = {
        'coalesce': True,  # Combine multiple pending executions into one
        'max_instances': 3,  # Maximum number of concurrently executing instances
        'misfire_grace_time': 30  # Seconds after which a missed job is considered expired
    }
    
    _scheduler = BackgroundScheduler(
        executors=executors,
        job_defaults=job_defaults,
        timezone='UTC'
    )
    
    # Add scheduled jobs here
    # Example:
    # _scheduler.add_job(
    #     func=some_pipeline_job,
    #     trigger='cron',
    #     hour=0,  # Run at midnight
    #     minute=0,
    #     id='daily_pipeline_job'
    # )
    
    _scheduler.start()
    logger.info("Pipeline scheduler started successfully")


def stop_scheduler() -> None:
    """
    Stop the background scheduler gracefully.
    This will shutdown the scheduler and wait for running jobs to complete.
    """
    global _scheduler
    
    if _scheduler is None:
        return
    
    if not _scheduler.running:
        logger.warning("Scheduler is not running")
        return
    
    try:
        _scheduler.shutdown(wait=True)
        logger.info("Pipeline scheduler stopped successfully")
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
    finally:
        _scheduler = None










