from spamfilter.filtering.SQLManager import SQLManager

# SQL TESTS
sql_mgr = SQLManager('test.db')

table_scheme = {
    'table_name': 'email_table',
    'primary_key': {'name': 'email_addr', 'type': 'text'},
    'attribute_info': [
        {'name': 'ehlo', 'type': 'text', 'nullness': 'NOT_NULL', 'uniqueness': ''}
    ]
}

data = [
    ('cmrodriguez17@esei.uvigo.es', 'ehlo1'),
    ('eacappello17@esei.uvigo.es', 'ehlo2'),
    ('imalvarez17@esei.uvigo.es', 'ehlo2')
]

sql_mgr.update_info_in_db(table_scheme, data)
