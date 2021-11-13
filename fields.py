import validators


class Field(object):

    _base_type = str

    def __init__(self, required=True, default=None):
        self.required = required
        self.default = default
        self.validators = []

    def validate(self, value, raise_exception=False):
        validations = (not x.is_valid(value) for x in self.validators)
        if not isinstance(value, self._base_type) or any(validations):
            if raise_exception:
                raise ValueError('invalid value: {}'.format(value))
            return False
        return True


class StringField(Field):

    _base_type = str

    def __init__(self, length_min=None, length_max=None, **kwargs):
        super().__init__(**kwargs)
        if length_min is not None:
            self.validators.append(validators.LengthMin(length_min))
        if length_max is not None:
            self.validators.append(validators.LengthMax(length_max))


class IntegerField(Field):

    _base_type = int

    def __init__(self, value_min=None, value_max=None, **kwargs):
        super().__init__(**kwargs)
        if value_min is not None:
            self.validators.append(validators.ValueMin(value_min))
        if value_max is not None:
            self.validators.append(validators.ValueMax(value_max))


class ListField(Field):
    pass


class DictField(Field):
    pass
