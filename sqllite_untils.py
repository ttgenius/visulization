"""sqllite database utils: create connection, create tables, insert data etc"""

import sqlite3
from sqlite3 import Error
import argparse


def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by db_file
    :param db_file: abs path to database file
    :return: Connection object or None
    """
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Error as e:
        print(e)

    return None


def close_connection(conn):
    """close database connection
     :param conn: Connection object
    """
    try:
        if conn is not None:
            conn.close()
            print('Database connection closed.')
    except Error as e:
        print(e)


def create_table(conn, create_table_sql):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :param create_table_sql: a CREATE TABLE statement
    :return:
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Error as e:
        print(e)


def create_schema(conn, schema_dump_file):
    """create a schema with tables
    :param conn: Connection object
    :param schema_dump_file: txt file consisting of sql statements to create tables
    """
    try:
        with open(schema_dump_file, 'r') as schema_file:
            lines = schema_file.readlines()
            sql_statement = ''

            for line in lines:
                line = line.strip()
                if line.startswith('create') or line.startswith('CREATE'):
                    sql_statement += line
                    if line.endswith(';'):
                        create_table(conn, sql_statement)
                        print(sql_statement)
                        sql_statement = ''
                elif line.endswith(';'):
                    sql_statement += line
                    print(sql_statement)
                    create_table(conn, sql_statement)
                    sql_statement = ''
                else:
                    sql_statement += line
    except Exception as (e):
        print (e)


def insert_imdb(conn,imdb):
    pass


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-c', '--create', nargs=2, help='db_file_path_to_create existing_schema_dump_file_path Eg.sqllite_schema_test.db sqllite_schema_dump.txt',
                        metavar=('db_file_path_to_create', 'existing_schema_dump_file_path'))

    parser.add_argument('-i', '--insert', help='abs path to data folder that is to be used to insert into the database. Eg.home/tt/cybershake17p9_csv')

    args = parser.parse_args()
    # print("ereer",len(vars(args).values()))
    if args.create and args.insert:
        parser.error("-c option must be used individually")

    if not any(vars(args).values()):
        parser.error('No arguments provided.')

    if args.create:
        conn = create_connection(args.create[0])
        create_schema(conn, args.create[1])
        close_connection(conn)

    elif args.insert:
        print("insert not implemented yet")


if __name__ == '__main__':
    main()