from enum import Enum

class Model(object):

    _INITIALIZED = "_initialized"
    FIELD_TYPES = None


    def __init__(self, **content):

        if not self._hasSetFieldTypes():
            self._setFieldTypes(content.keys())

        if not all(key == key.lower() for key in content):
            raise AttributeError("Model fields may only be lower case to work with serializers {0}".format(content.keys()))

        for key, val in content.items():
            self.__dict__[key] = val

        self._setInitialized()

    def __iter__(self):

        for attr, value in self.__dict__.iteritems():

            if not attr.startswith("_"):

                yield attr, value

    def __setattr__(self, attr, value):

        if (attr == Model._INITIALIZED):

            raise AttributeError(
                "Can't directly set model to initialized state")

        elif (self._isInitialzed() and not hasattr(self, attr)):

            raise AttributeError(
                "Can't add new attributes after initialization")

        else:

            self.__dict__[attr] = value

    @classmethod
    def _hasSetFieldTypes(cls):

        return ("FIELD_TYPES" in cls.__dict__ and 
                cls.__dict__["FIELD_TYPES"] is not None)

    @classmethod
    def _setFieldTypes(cls, types):

        if cls._hasSetFieldTypes():
            raise AttributeError("Can't change field types")
        else:
            cls.FIELD_TYPES = Enum(cls.__name__, {t: hash(t) for t in types})

    def _setInitialized(self):

        self.__dict__[Model._INITIALIZED] = True

    def _isInitialzed(self):

        if (Model._INITIALIZED not in self.__dict__):
            self.__dict__[Model._INITIALIZED] = False

        return self.__dict__[Model._INITIALIZED]

