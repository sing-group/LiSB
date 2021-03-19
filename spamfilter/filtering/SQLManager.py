import sqlite3 as sql


class SQLManager:
    db_name = None

    def __init__(self, db_name):
        self.db_name = db_name

    def update_info_in_db(self, table_scheme: dict, data: dict):
        """
        When called, this method updates the info in info in the table described in table_scheme.
        If the table or DB aren't created yet, then they are created.

        :param table_scheme: the table scheme as a dictionary. Example: { "table_name" : "new_table", "attribute_info" : [ {'name' : 'at1', 'type' : 'text', 'nullness' : 'not_null'} ] }
        :param data: the data that will be updated in the DB. Example: { "key1" : { "attr1" : "value1" }, "key2": { "attr1": "value1" } }
        """

        try:
            # Crate connection object to DB and cursor to operate on it
            conn = sql.connect(self.db_name)
            cursor = conn.cursor()

            # Parse data to tuple format:
            parsed_data = []
            for (pk_value, attributes) in data.items():
                row = (pk_value,)
                for attribute in attributes.values():
                    row += (attribute,)
                parsed_data.append(row)

            # Create table if not created
            parsed_create_query = SQLManager.__parse_create_table_query(table_scheme)
            cursor.execute(parsed_create_query)

            # Update data in table
            parsed_replace_query = SQLManager.__parse_replace_query(table_scheme)
            cursor.executemany(parsed_replace_query, parsed_data)

        except sql.Error as e:
            print(f"An error occurred when trying to update the info to the DB ({e})")

        finally:
            # Close the cursor, commit the changes and close the connection to the DB
            if cursor:
                cursor.close()
            if conn:
                conn.commit()
                conn.close()

    def get_info_from_db(self, table_scheme):
        """
        This method gets all data from a given table.

        :param table_scheme: the scheme of the table where the data will be obtained from
        :return: The data in this format: { "key1" : { "attr1" : "value1" }, "key2": { "attr1": "value1" } }
        """
        data = {}
        try:
            # Crate connection object to DB and cursor to operate on it
            conn = sql.connect(self.db_name)
            cursor = conn.cursor()

            # Check if table exists and get data if so
            cursor.execute(f"""SELECT name FROM sqlite_master WHERE type='table' AND name='{table_scheme['table_name']}';""")
            if cursor.rowcount == 1:
                # Get all rows from table and parse them to return format
                for row in cursor.execute(f"""SELECT * FROM {table_scheme['table_name']}"""):
                    pk_value = row[0]
                    data[pk_value] = {}
                    for attr_index in range(1, len(row)):
                        attr_name = table_scheme['attribute_info'][attr_index - 1]['name']
                        data[pk_value][attr_name] = row[attr_index]

        except sql.Error as e:
            print(f"An error occurred when trying to update the info to the DB ({e})")
        finally:
            # Close the cursor, commit the changes and close the connection to the DB
            if cursor:
                cursor.close()
            if conn:
                conn.close()
        return data

    @staticmethod
    def __parse_create_table_query(table_scheme: dict):
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
    def __parse_replace_query(table_scheme: dict):
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
