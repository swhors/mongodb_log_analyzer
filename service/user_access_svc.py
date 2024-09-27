from model.user_access import UserAccess, table_name
from service import db_handle
from lib.mysql import select_datas, insert_data


def select_value(cursor=None, value: UserAccess = None):
    value_list = []
    if cursor is None:
        t_cursor = db_handle.cursor()
    else:
        t_cursor = cursor
    values = select_datas(db_handle, cursor=t_cursor, table=table_name, where=value.where_all())
    for val in values:
        value_list.append(val)
    if cursor is None:
        t_cursor.close()
    return value_list


def select_user_by_ctx_db_client(cursor=None, ctx="", db="", client=""):
    where_clause = f"ctx=\"{ctx}\" and db=\"{db}\" and client=\"{client}\""
    order_clause = "order by id desc"
    if cursor is None:
        t_cursor = db_handle.cursor()
    else:
        t_cursor = cursor
    values = select_datas(db_handle,
                          cursor=t_cursor,
                          table=table_name,
                          where=where_clause,
                          order=order_clause)
    if cursor is None:
        t_cursor.close()
    if len(values) > 0 and len(values[0]) == 6:
        return values[0][5]
    return "Unknown"


def insert_value(values, cursor=None, auto_commit=True):
    if len(values) != 5:
        return
    if cursor is None:
        t_cursor = db_handle.cursor()
    else:
        t_cursor = cursor
    user_access = UserAccess.create(*values)
    # ret = select_value(cursor=t_cursor, value=user_access)
    # if len(ret) == 0:
    insert_data(conn=db_handle,
                cursor=t_cursor,
                table=table_name,
                value=user_access,
                auto_commit=auto_commit)
    if cursor is None:
        t_cursor.close()
