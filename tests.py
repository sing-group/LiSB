import email

file = open("datasets/test_email_msg.eml")
msg_data = email.message_from_file(file)

dkim = {}
for to_parse in msg_data.get('DKIM-Signature').split(';'):
    parsed = to_parse.replace("\n", "").strip().split('=')
    dkim[parsed[0]] = parsed[1].strip()
print(f"d:{dkim['d']}")
print(f"s:{dkim['s']}")
