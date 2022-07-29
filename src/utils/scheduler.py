from apscheduler.schedulers.asyncio import AsyncIOScheduler

sched = AsyncIOScheduler()

def scheduler_setup():
    sched.start()

