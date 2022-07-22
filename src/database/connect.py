from ming import create_datastore
from ming.odm import ThreadLocalODMSession

def initialse(datastore:str):
    global database_session
    database_session = ThreadLocalODMSession(
        bind=create_datastore(datastore)
    )

