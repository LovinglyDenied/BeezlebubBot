from apscheduler.schedulers.asyncio import AsyncIOScheduler

sched = AsyncIOScheduler({'apscheduler.timezone': 'UTC'})

def scheduler_setup():
    """Congigures the global varibale sched, that contains the AsyncIOScheduler, and then starts it as a coroutine

    Can be called multiple times without issue. 
    Each cog that uses sched should define any callables in on_connect, and call this function in on_ready"""
    from database.connect import DBManager
    try:
        sched.add_jobstore(
            "mongodb",
            database = DBManager.db.name,
            client = DBManager.db.client
            )
        sched.start()
    except ValueError:
        pass
 