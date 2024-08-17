class cached_property: # noqa
    """
    Decorator that converts a method with a single self argument into a
    property cached on the instance.
    """

    name = None

    @staticmethod
    def decorated_method(instance):
        raise TypeError(
            "Cannot use cached_property instance without calling "
            "__set_name__() on it."
        )

    def __init__(self, method):
        self.method_to_decorate = method
        self.__doc__ = getattr(method, "__doc__")

    def __set_name__(self, owner, name):
        if self.name is None:
            self.name = name
            self.decorated_method = self.method_to_decorate
        elif name != self.name:
            raise TypeError(
                "Cannot assign the same cached_property to two different names "
                "(%r and %r)." % (self.name, name)
            )

    def __get__(self, instance, cls=None):
        """
        Call the function and put the return value in instance.__dict__ so that
        subsequent attribute access on the instance returns the cached value
        instead of calling cached_property.__get__().
        """
        if instance is None:
            return self

        result = instance.__dict__[self.name] = self.decorated_method(instance)

        return result
