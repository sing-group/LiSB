import email

file = open("datasets/spam/20030229_spam/msg7.eml", "r")
msg_data = email.message_from_file(file)

for (header, value) in msg_data.items():
    if "X-" in header:
        print(header)
