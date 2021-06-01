from core.EmailEnvelope import EmailEnvelope


class EmailWithFile:
    file_name: str
    msg: EmailEnvelope

    def __init__(self, file_name: str, msg: EmailEnvelope):
        self.file_name = file_name
        self.msg = msg
