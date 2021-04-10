# from spamfilter.configuration_schemas import filtering_schema, email_alerts_schema, server_params_schema

from configuration import communications_schema

# filtering_conf = {
#     "disabled-filters": ["SPFFilter"],
#     "exceptions": {
#         "ip_addresses": ["192.168.1.1"],
#         "email_addresses": ["cmrodriguez17@esei.es"],
#         "email_domains": ["esei.es"]
#     }
# }
# print(filtering_schema.validate(filtering_conf))
#
# alerts = {
#     "status": "enabled",
#     "level": "WARNING",
#     "msg-template": "A new alert has been generated at %(asctime)s by %(module)s : %(message)s"
#   }
#
# print(email_alerts_schema.validate(alerts))
#
# server_params = {
#   "n-filtering-threads": 0,
#   "n-forwarder-threads": 1,
#   "storing-frequency": 10
# }
#
# print(server_params_schema.validate(server_params))

# with open("conf/logging.json") as file:
#     loaded = json.load(file)
#
# print(logging_schema.validate(loaded))

to_test = {
  "admin-emails": [
    "cmrodriguez17@esei.uvigo.es"
  ],
  "server-email": "no-reply@spamfilter.com"
}

print(communications_schema.validate(to_test))