import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None
    loop = None

db_instance = Database()

def get_database():
    try:
        current_loop = asyncio.get_running_loop()
    except RuntimeError:
        current_loop = None

    if db_instance.client is None or db_instance.loop != current_loop:
        db_instance.client = AsyncIOMotorClient(settings.MONGO_URI)
        db_instance.db = db_instance.client[settings.MONGO_DB_NAME]
        db_instance.loop = current_loop
    return db_instance.db

async def connect_to_mongo():
    try:
        db = get_database()
        await db.command('ping')
        logger.info(f"Connecté à MongoDB : {settings.MONGO_DB_NAME}")
        
        # Création des index utiles
        await db.candidates.create_index("id", unique=True)
        await db.candidates.create_index("anonymous_id")
        await db.candidates.create_index("retention_date")
        await db.audit_logs.create_index("timestamp")
        await db.audit_logs.create_index("candidate_id")
    except Exception as e:
        logger.error(f"Erreur de connexion MongoDB : {e}")
        raise e

async def close_mongo_connection():
    if db_instance.client:
        db_instance.client.close()
        db_instance.client = None
        db_instance.db = None
        db_instance.loop = None
        logger.info("Connexion MongoDB fermée.")


