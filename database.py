from contextlib import contextmanager

import json
import psycopg2
import psycopg2.extras


class DatabasePort:
    """
    Class for creating database port to specified database.
    Database specifications are loaded from psql_connection.json.

    Attributes
    ----------
    :database : name of database
    :u : name of user
    :p : password if any
    :host : host
    """

    def __init__(self):
        with open('./config/psql_connection.json') as psql_conn:
            conn_data = json.load(psql_conn)
            self.database = conn_data['name']
            self.u = conn_data['user']
            self.p = conn_data['pass']
            self.host = conn_data['host']

    @contextmanager
    def connection_handler(self, commit=None, cursor_factory=None):
        """
        Context manager, creates and yields connection to database.
        Connection is always closed in the end.

        :param commit: boolean value
        :param cursor_factory: eg. psycopg2.extras.DictCursor
        :return: yields cursor
        """
        connection = psycopg2.connect(database=self.database, host=self.host,
                                      user=self.u, password=self.p)
        cursor = connection.cursor(cursor_factory=cursor_factory)
        try:
            yield cursor
        except psycopg2.DatabaseError as e:
            if hasattr(e, 'message'):
                print(e.message)
            else:
                print(e)
            connection.rollback()
            raise e
        else:
            if commit:
                connection.commit()
            else:
                connection.rollback()
        finally:
            connection.close()
