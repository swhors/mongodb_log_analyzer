from service.redis_svc import redis_init
from lib.mysql import db_init
from config import db_host, db_port, db_user, db_db, db_passwd

redis_client = redis_init()
db_handle = db_init(db_host=db_host,
                    db_user=db_user,
                    db_passwd=db_passwd,
                    db_db=db_db,
                    db_port=db_port)
