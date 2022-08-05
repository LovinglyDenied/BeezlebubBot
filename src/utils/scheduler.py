from apscheduler.schedulers.asyncio import AsyncIOScheduler

sched = AsyncIOScheduler({'apscheduler.timezone': 'UTC'})

def scheduler_setup():
    """Congigures the global varibale sched, that contains the AsyncIOScheduler, and then starts it as a coroutine"""
    from database.connect import DBManager
    sched.add_jobstore(
            "mongodb",
            database = DBManager.db.name,
            client = DBManager.db.client
            )
    sched.start()
