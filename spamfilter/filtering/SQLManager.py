import sqlite3 as sql


class SQLManager:
    db_name = None

    def __init__(self, db_name):
        self.db_name = db_name

    def update_info_in_db(self, table_scheme, data):
        """
        When called, this method updates the info in info in the table described in table_scheme.
        If the table or DB aren't created yet, then they are created.

        :param table_scheme: the table scheme as a dictionary. Example: { "table_name" : "new_table", "attribute_info" : [ {'name' : 'at1', 'type' : 'text', 'nullness' : 'not_null'} ] }
        :param data: the data that will be updated in the DB
        """

        try:
            # Crate connection object to DB and cursor to operate on it
            conn = sql.connect(self.db_name)
            cursor = conn.cursor()

            # Create table if not created
            parsed_create_query = self._parse_create_table_query(table_scheme)
            cursor.execute(parsed_create_query)

            # Update data in table
            parsed_replace_query = self._parse_replace_query(table_scheme)
            cursor.executemany(parsed_replace_query, data)

        except sql.Error as e:
            print(f"An error occurred when trying to update the info to the DB ({e})")

        finally:
            # Close the cursor, commit the changes and close the connection to the DB
            if cursor:
                cursor.close()
            if conn:
                conn.commit()
                conn.close()

    @staticmethod
    def _parse_create_table_query(table_scheme: dict):
        """
        This method parses the info in table_scheme into a CREATE TABLE statement.

        :param table_scheme: the table data as a dictionary. Example: { "table_name" : "new_table", "attribute_info" : [ {'name' : 'at1', 'type' : 'text', 'nullness' : 'not_null'} ] }
        :return: The parsed CREATE TABLE query
        """
        pk_str = f"{table_scheme['primary_key']['name']} {table_scheme['primary_key']['type']} PRIMARY KEY"
        attributes_str = ", ".join([
            f"{attribute_info['name']} {attribute_info['type']} {attribute_info['nullness']} {attribute_info['uniqueness']}"
            for attribute_info in table_scheme['attribute_info']
        ])
        query = f"""CREATE TABLE IF NOT EXISTS {table_scheme['table_name']} (""" \
                f"""{pk_str}, {attributes_str} );"""
        return query

    @staticmethod
    def _parse_replace_query(table_scheme: dict):
        """
        This method parses the info in table_scheme into a REPLACE INTO statement.

        :param table_scheme: the table data as a dictionary. Example: { "table_name" : "new_table", "attribute_info" : [ {'name' : 'at1', 'type' : 'text', 'nullness' : 'not_null'} ] }
        :return: The parsed REPLACE INTO  query
        """
        pk = table_scheme['primary_key']['name']
        attributes_str = ", ".join([attribute_info['name'] for attribute_info in table_scheme['attribute_info']])
        params_str = ", ".join(["?" for i in range(len(table_scheme['attribute_info']))])
        query = f"""REPLACE INTO {table_scheme['table_name']} ({pk}, {attributes_str}) VALUES (?, {params_str});"""
        return query
