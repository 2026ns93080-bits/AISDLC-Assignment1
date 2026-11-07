class ServiceError(Exception):
    def __init__(self) -> None:
        super().__init__("Model service unavailable.")


class InvalidModelOutput(Exception):
    def __init__(self, raw_reply: str) -> None:
        self.raw_reply = raw_reply
        super().__init__("Model returned an invalid response.")
