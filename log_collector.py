import time
import os
import logging
import argparse
import json
import sys
import signal

log_format = "%(levelname)s %(asctime)s = %(message)s"

logging.basicConfig(stream=sys.stdout, filemode="a", format=log_format, level=logging.INFO)
logger = logging.getLogger()

retry_this = True
is_log_trace = True

ignore_lines = ["No drop-pending idents have expired",
                "Removing historical entries older than",
                "Slow query",
                "Received interrupt request for unknown op",
                "Scanning sessions",
                "running TTL job for index",
                "Completed unstable checkpoint.",
                "Finished checkpoint, updated iteration counter",
                "WiredTiger message",
                "Checkpoint thread sleeping",
                "Deleted expired documents using index",
                "cleaning up unused lock buckets of the global lock manager",
                "Collection does not exist. Using EOF plan",
                "WiredTigerSizeStorer::store",
                "Using idhack",
                "Connection ended",
                "Received first command on ingress connection since session start or auth handshake",
                "Checking authorization failed",
                "User assertion",
                "Terminating session due to error",
                "Ending session",
                "Session from remote encountered a network error during SourceMessage",
                "Assertion while executing command",
                "Command not found in registry",
                "Interrupted operation as its client disconnected",
                "client metadata",
                "Auth metrics report",
                "Only one plan is available",
                ]

exclude_cmds = ['hello',
                'ping',
                'ismaster',
                'getLog',
                'isMaster',
                'getParameter',
                'isClusterMember',
                'aggregate',
                'buildInfo',
                'saslStart',
                'saslContinue',
                'endSessions',
                'connectionStatus',
                'listCollections',
                'listDatabases',
                'hostInfo',
                'top',
                'replSetUpdatePosition',
                'replSetHeartbeat',
                'getMore',
                'serverStatus',
                'dbStats',
                'getCmdLineOpts',
                ]

exclude_dbs = ['config']
exclude_users = ['__system']

retry_count = 0

api_server_url_pre = "http://eimmo-infra-manager.koreacentral.cloudapp.azure.com:8080/mongodb/user/put"


def send_data(data, api_url):
    import requests
    headers = {'Content-type': 'application/json'}
    date = data['date']
    if date.endswith('Z'):
        date = date.replace('Z', '')
        data['date'] = date
        try:
            r = requests.post(api_url, json=data, headers=headers)
            logging.info(f'send_data: result = {r}')
        except Exception as e:
            logging.error(f'send_data: Exception\n\t\t{e}')


def send_user_access(date: str, ctx: str, cmd: str, client: str, user: str, db: str):
    data = {'date': date, 'ctx': ctx, 'cmd': cmd, 'client': client, 'user': user, 'db': db}
    api_url = api_server_url_pre + "/access"
    if db not in exclude_dbs:
        if user is None or (user is not None and (user not in exclude_users)):
            send_data(data=data, api_url=api_url)


def send_user_command(date: str, ctx: str, cmd: str, client: str, table_name: str, db: str):
    data = {'date': date, 'ctx': ctx, 'cmd': cmd, 'client': client, 'table': table_name, 'db': db}
    api_url = api_server_url_pre + "/command"
    if db not in exclude_dbs:
        send_data(data=data, api_url=api_url)


def check_command(log_dict):
    cmd_info = log_dict["attr"]["commandArgs"]
    cmd_keys = list(cmd_info.keys())
    cmd = cmd_keys[0]
    client = log_dict["attr"]["client"]
    if cmd not in exclude_cmds and len(client) > 0:
        table = cmd_info.get(cmd)
        db = log_dict["attr"]["db"]
        date = log_dict["t"]["$date"]
        ctx = log_dict["ctx"]
        logging.info(f'=== {date} ctx = {ctx}, cmd = {cmd}, client = {client}, table = {table}, db = {db}')
        send_user_command(date=date, ctx=ctx, cmd=cmd, client=client, table_name=table, db=db)
        return
    if "speculativeAuthenticate" in cmd_info.keys:
        auth_info = cmd_info['speculativeAuthenticate']
        db = auth_info['db']
        user = "userdb.won@aimmo.co.kr".replace(db + ".", "")
        ctx = log_dict["ctx"]
        date = log_dict["t"]["$date"]
        send_user_access(date=date, ctx=ctx, cmd=cmd, client=client, user=user, db=db)


def check_accept_state(log_dict):
    pass


def check_authenticated(log_dict):
    date = log_dict["t"]["$date"]
    client = log_dict["attr"]["client"]
    user = log_dict["attr"]["user"]
    db = log_dict["attr"]["db"]
    ctx = log_dict["ctx"]
    logging.info(f'check_authenticated: {date} ctx = {ctx}, cmd = AUTH, client = {client}, user = {user}, db = {db}')
    send_user_access(date=date, ctx=ctx, cmd="AUTH", client=client, user=user, db=db)


def check_connection_ended(log_dict):
    date = log_dict["t"]["$date"]
    client = log_dict["attr"]["remote"]
    ctx = log_dict["ctx"]
    logging.info(f'check_connection_ended: {date} ctx = {ctx}, cmd = DISCON, client = {client}')


def check_returning_user_from_cache(log_dict):
    pass


monitoring_lines = {"Connection accepted": check_accept_state,
                    "Returning user from cache": check_returning_user_from_cache,
                    "About to run the command": check_command,
                    "Successfully authenticated": check_authenticated,
                    "Connection ended": check_connection_ended,
                    }


def trace_log(log_fd):
    global retry_this
    global retry_count
    
    logging.info(f'start follow - {log_fd}')
    log_fd.seek(0, 2)
    retry_this = False
    not_read_cnt = 0
    while is_log_trace:
        try:
            os.stat(log_fd.name)
            line = log_fd.readline()
            if not line:
                if not_read_cnt > 600:
                    retry_this = True
                    return False
                not_read_cnt += 1
                time.sleep(0.1)
                continue
            else:
                not_read_cnt = 0
                retry_this = False
                if line.startswith('{'):
                    log_dict = json.loads(line)
                    if log_dict["msg"] in monitoring_lines.keys():
                        monitoring_lines.get(log_dict["msg"])(log_dict)
        except FileNotFoundError as file_not_found:
            logging.info('trace_log: FileNotFoundError\n\t\t{file_not_found}')
            retry_this = True
            return False
        except Exception as general_except:
            logging.info('trace_log: Exception\n\t\t{file_not_found}')
            retry_this = False
            return False
    logging.info(f'end follow - {log_fd}')
    return True


def get_arg_logpath():
    parser = argparse.ArgumentParser(description='Mongodb Log Monitoring.')
    parser.add_argument('--filepath', dest='filepath', action='store', default="")
    args = parser.parse_args()
    return args.filepath


def log_monitor(file_name: str):
    global retry_this
    global retry_count
    global is_log_trace
    try:
        with open(file_name, "rt") as fd:
            logging.info(f'log_monitor: success to open file {fd}')
            is_log_trace = True
            result = trace_log(fd)
            fd.close()
            return result
    except FileNotFoundError as file_not_found:
        logging.info(f'log_monitor: FileNotFoundError\n\t\t{file_not_found}')
        retry_this = True
        return False
    retry_this = False
    return False


def retry_run(log_path):
    global retry_count
    global retry_this
    
    while retry_this:
        log_monitor(file_name=log_path)
        logging.info(f'retry_run: retry_count={retry_count} retry_this={retry_this}')
        if retry_count < 600:
            retry_count += 1
            time.sleep(1)
        else:
            logging.info('retry_run: exit')
            break


def sig_handler(sig_num, frame):
    global is_log_trace
    global retry_this
    global retry_count
    
    if sig_num == signal.SIGUSR1:
        logging.info('sig_handler: reload_log_trace')
        is_log_trace = False
        retry_count = 0
        retry_this = True
    if sig_num in [signal.SIGKILL, signal.SIGTERM, signal.SIGSEGV, signal.SIGHUP, signal.SIGABRT]:
        logging.info(f'sig_handler: {sig_num}')
        sys.exit()


def write_pid():
    with open("log_collector.pid", "wt") as fd:
        fd.write(f"{os.getpid()}")
        fd.close()


if __name__ == "__main__":
    try:
        mongodb_log_path = os.environ['MONGO_LOG']
    except Exception as e:
        mongodb_log_path = get_arg_logpath()
    
    write_pid()
    
    signal.signal(signal.SIGUSR1, sig_handler)
    
    logging.info(f'main: log_path={mongodb_log_path}')
    retry_run(log_path=mongodb_log_path)
