class staticproperty(property):
    def __get__(self, obj, cls=None):
        return self.fget()
