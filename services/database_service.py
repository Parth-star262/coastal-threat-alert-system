import psycopg2
from psycopg2 import pool
from config import DB_CONFIG
import logging

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.connection_pool = None
        self._create_connection_pool()
    
    def _create_connection_pool(self):
        """Create database connection pool"""
        try:
            self.connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn=1,
                maxconn=10,
                **DB_CONFIG
            )
            logger.info("✅ Database connection pool created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create connection pool: {e}")
    
    def get_connection(self):
        """Get connection from pool"""
        if self.connection_pool:
            return self.connection_pool.getconn()
        return None
    
    def return_connection(self, conn):
        """Return connection to pool"""
        if self.connection_pool and conn:
            self.connection_pool.putconn(conn)
    
    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Execute database query with proper error handling"""
        conn = None
        cursor = None
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if fetch_one:
                result = cursor.fetchone()
            elif fetch_all:
                result = cursor.fetchall()
            else:
                result = None
            
            conn.commit()
            return result
            
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"❌ Database error: {e}")
            raise e
        finally:
            if cursor:
                cursor.close()
            if conn:
                self.return_connection(conn)