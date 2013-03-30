class DataError(Exception):
    pass


class ObjectExistsError(DataError):
    def __init(self, key):
        super(ObjectExistsError, self).__init__("ObjectExists: {}".format(key))


class NonUniqueError(DataError):
    def __init__(self, index_name, value):
        super(NonUniqueError, self).__init__("NonUnique:  {} already exists in index {}.".format(value, index_name))

