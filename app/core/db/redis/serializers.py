import pickle


class RedisSerializer:
    def __init__(self):
        self.protocol = pickle.HIGHEST_PROTOCOL

    def dumps(self, obj):
        if type(obj) is int:
            return obj
        return pickle.dumps(obj, self.protocol)

    def loads(self, data):  # noqa
        try:
            return int(data)
        except ValueError:
            return pickle.loads(data)
