from log import logger

api_server_url_pre = "http://eimmo-infra-manager.koreacentral.cloudapp.azure.com:8080/mongodb/user/put"


def send_to_api(data, api_url):
    import requests
    headers = {'Content-type': 'application/json'}
    date = data['date']
    if date.endswith('Z'):
        date = date.replace('Z', '')
        data['date'] = date
        try:
            r = requests.post(api_url, json=data, headers=headers)
            logger.info(f'send_to_api: result = {r}')
        except Exception as e:
            logger.error(f'send_to_api: Exception\n\t\t{e}')


def send_user_access(date: str, ctx: str, cmd: str, client: str, user: str, db: str):
    data = {'date': date, 'ctx': ctx, 'cmd': cmd, 'client': client, 'user': user, 'db': db}
    api_url = api_server_url_pre + "/access"
    send_to_api(data=data, api_url=api_url)


def send_user_command(date: str, ctx: str, cmd: str, client: str, table_name: str, db: str):
    data = {'date': date, 'ctx': ctx, 'cmd': cmd, 'client': client, 'table': table_name, 'db': db}
    api_url = api_server_url_pre + "/command"
    send_to_api(data=data, api_url=api_url)
