
class Validator(object):

    def __init__(self, limit):
        self.limit = limit


class LengthMin(Validator):

    def is_valid(self, value):
        return self.limit <= len(value)


class LengthMax(Validator):

    def is_valid(self, value):
        return len(value) <= self.limit


class ValueMin(Validator):

    def is_valid(self, value):
        return self.limit <= value


class ValueMax(Validator):

    def is_valid(self, value):
        return value <= self.limit
