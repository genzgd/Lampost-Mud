from lampost.util.lputil import ClientError


class DataError(ClientError):
    http_status = 409


class ObjectExistsError(DataError):
    def __init__(self, key):
        super().__init__("ObjectExists: {}".format(key))


class NonUniqueError(DataError):
    def __init__(self, index_name, value):
        super().__init__("NonUnique:  {} already exists in index {}.".format(value, index_name))

