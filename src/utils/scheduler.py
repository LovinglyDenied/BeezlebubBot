from apscheduler.schedulers.asyncio import AsyncIOScheduler

sched = AsyncIOScheduler({'apscheduler.timezone': 'UTC'})

def scheduler_setup():
    from database.connect import DBManager
    sched.add_jobstore(
            "mongodb",
            database = DBManager.db.name,
            client = DBManager.db.client
            )
    sched.start()
