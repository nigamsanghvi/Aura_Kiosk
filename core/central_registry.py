class CentralRegistry:
    _instance = None

    def __init__(self):
        self.config = {}
        self.status = {}

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = CentralRegistry()
        return cls._instance

    def set_config(self, key, value):
        self.config[key] = value

    def get_config(self, key):
        return self.config.get(key)

    def set_status(self, key, value):
        self.status[key] = value

    def get_status(self, key):
        return self.status.get(key)