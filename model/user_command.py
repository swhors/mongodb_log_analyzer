"""
mysql> describe user_command;
+------------+--------------+------+-----+---------+----------------+
| Field      | Type         | Null | Key | Default | Extra          |
+------------+--------------+------+-----+---------+----------------+
| id         | bigint(20)   | NO   | PRI | NULL    | auto_increment |
| client     | varchar(255) | YES  |     | NULL    |                |
| cmd        | varchar(255) | YES  |     | NULL    |                |
| ctx        | varchar(255) | YES  |     | NULL    |                |
| date       | datetime(6)  | YES  |     | NULL    |                |
| db         | varchar(255) | YES  |     | NULL    |                |
| table_name | varchar(255) | YES  |     | NULL    |                |
| user       | varchar(255) | YES  |     | NULL    |                |
+------------+--------------+------+-----+---------+----------------+
8 rows in set (0.00 sec)
"""
from datetime import datetime

class_name = "UserCommand"
table_name = "user_command"


class UserCommand:
    id: int
    client: str
    cmd: str
    ctx: str
    date: datetime
    db: str
    table_name: str
    user: str
    
    def __init__(self,
                 id: int = 0,
                 client: str = "",
                 cmd: str = "",
                 ctx: str = "",
                 date: datetime = datetime.now(),
                 db: str = "",
                 table_name: str = "",
                 user: str = ""):
        self.id = id
        self.client = client
        self.cmd = cmd
        self.ctx = ctx
        self.date = date
        self.db = db
        self.table_name = table_name
        self.user = user
    
    def where_all(self):
        return f'date=\"{self.date}\" and ' \
            + f'ctx=\"{self.ctx}\" and ' \
            + f'cmd=\"{self.cmd}\" and ' \
            + f'user=\"{self.user}\" and ' \
            + f'client=\"{self.client}\" and ' \
            + f'db=\"{self.db}\" and ' \
            + f'table_name=\"{self.table_name}\"'
    
    def __str__(self) -> str:
        return f'\"{self.id}\", \"{self.client}\", \"{self.cmd}\", \"{self.ctx}\", \"{self.date}\", \"{self.db}\", \"{self.table_name}\", \"{self.user}\"'
    
    def __eq__(self, other):
        if self.date == other.date and self.ctx == other.ctx and self.cmd == other.cmd \
                and self.user == other.user and self.client == other.client and self.db == other.db and self.table_name == other.table_name:
            return True
        else:
            return False

    @staticmethod
    def create(client="", cmd="", ctx="", updated=datetime.now(), db="", table_name="", user=""):
        return UserCommand(
            date=updated,
            ctx=ctx,
            cmd=cmd,
            user=user,
            client=client,
            db=db,
            table_name=table_name
        )
