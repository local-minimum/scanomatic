from scanomatic.generics.model import Model
import scanomatic.generics.decorators as decorators
from scanomatic.io.logger import Logger

import copy
import os
from enum import Enum
from ConfigParser import ConfigParser
import cPickle


class AbstractModelFactory(object):
    MODEL = Model
    _SUB_FACTORIES = dict()
    STORE_SECTION_HEAD = tuple()
    STORE_SECTION_SERIALIZERS = dict()

    def __new__(cls, *args):

        raise Exception("This class is static, can't be instantiated")

    # noinspection PyMethodParameters
    @decorators.class_property
    def serializer(cls):

        """

        :rtype : Serializer
        """
        return Serializer(cls)

    @classmethod
    def get_sub_factory(cls, model):

        model_type = type(model)
        if model_type not in cls._SUB_FACTORIES:
            return AbstractModelFactory
        return cls._SUB_FACTORIES[model_type]

    @classmethod
    def _verify_correct_model(cls, model):

        if not isinstance(model, cls.MODEL):
            raise TypeError("Wrong model for factory {1} is not a {0}".format(
                cls.MODEL, model))

        return True

    @classmethod
    def create(cls, **settings):

        """

        :rtype : scanomatic.genercs.model.Model
        """
        for key in settings:
            tuple_key = (key,)
            if (settings[key] is not None and
                    tuple_key in cls.STORE_SECTION_SERIALIZERS and
                    isinstance(cls.STORE_SECTION_SERIALIZERS[tuple_key], AbstractModelFactory) and
                    not isinstance(settings[key], AbstractModelFactory)):

                settings[key] = cls.STORE_SECTION_SERIALIZERS[tuple_key].create(**settings[key])

        return cls.MODEL(**settings)

    @classmethod
    def enforce_serializer_type(cls, settings, keys):
        """Especially good for enums

        :param settings:
        :param keys:
        :return:
        """
        for key in keys:
            if key in settings and not isinstance(settings[key], cls.STORE_SECTION_SERIALIZERS[(key,)]):
                try:
                    settings[key] = cls.STORE_SECTION_SERIALIZERS[(key,)](settings[key])
                except (AttributeError, ValueError):
                    try:
                        settings[key] = cls.STORE_SECTION_SERIALIZERS[(key,)][settings[key]]
                    except (AttributeError, KeyError, IndexError):
                        pass

    @classmethod
    def update(cls, model, **settings):

        for parameter, value in settings.items():

            if parameter in model:

                setattr(model, parameter, value)

    @classmethod
    def copy(cls, model):

        if cls._verify_correct_model(model):
            return cls.serializer.load_serialized_object(
                copy.deepcopy(
                    cls.serializer.serialize(model)))

    @classmethod
    def validate(cls, model):

        if cls._verify_correct_model(model):
            return all(v is True for v in cls._get_validation_results(model))

        return False

    @classmethod
    def get_invalid(cls, model):

        return (v for v in set(cls._get_validation_results(model))
                if v is not True)

    @classmethod
    def get_invalid_names(cls, model):

        return (v.name for v in cls.get_invalid(model))

    @classmethod
    def _get_validation_results(cls, model):

        return (getattr(cls, attr)(model) for attr in dir(cls) if attr.startswith("_validate"))

    @classmethod
    def set_invalid_to_default(cls, model):

        if cls._verify_correct_model(model):
            cls.set_default(model, fields=tuple(cls.get_invalid(model)))

    @classmethod
    def set_default(cls, model, fields=None):

        if cls._verify_correct_model(model):

            default_model = cls.MODEL()

            for attr, val in default_model:
                if fields is None or getattr(default_model.FIELD_TYPES, attr) in fields:
                    setattr(model, attr, val)

    @classmethod
    def clamp(cls, model):

        pass

    @classmethod
    def _clamp(cls, model, min_model, max_model):

        if (cls._verify_correct_model(model) and
                cls._verify_correct_model(min_model) and
                cls._verify_correct_model(max_model)):

            for attr, val in model:
                min_val = getattr(min_model, attr)
                max_val = getattr(max_model, attr)

                if min_val is not None and val < min_val:
                    setattr(model, attr, min_val)
                elif max_val is not None and val > max_val:
                    setattr(model, attr, max_val)

    @classmethod
    def _correct_type_and_in_bounds(cls, model, attr, dtype, min_model_caller,
                                    max_model_caller):

        if not isinstance(getattr(model, attr), dtype):

            return getattr(model.FIELD_TYPES, attr)

        elif not AbstractModelFactory._in_bounds(
                model,
                min_model_caller(model, factory=cls),
                max_model_caller(model, factory=cls),
                attr):

            return getattr(model.FIELD_TYPES, attr)

        else:

            return True

    @classmethod
    def _is_valid_submodel(cls, model, key):

        sub_model = getattr(model, key)
        sub_model_type = type(sub_model)
        if isinstance(sub_model, Model) and sub_model_type in cls._SUB_FACTORIES:
            return cls._SUB_FACTORIES[sub_model_type].validate(sub_model)
        return False

    @staticmethod
    def _in_bounds(model, lower_bounds, upper_bounds, attr):

        val = getattr(model, attr)
        min_val = getattr(lower_bounds, attr)
        max_val = getattr(upper_bounds, attr)

        if min_val is not None and val < min_val:
            return False
        elif max_val is not None and val > max_val:
            return False
        else:
            return True

    @staticmethod
    def _is_pinning_formats(pinning_formats):

        # noinspection PyBroadException
        try:

            return all(pinning_format is None or _is_pinning_format(pinning_format) for
                       pinning_format in pinning_formats)

        except:

            pass

        return False

    @staticmethod
    def _is_file(path):

        return isinstance(path, str) and os.path.isfile(path)

    @staticmethod
    def _is_tuple_or_list(obj):

        return isinstance(obj, tuple) or isinstance(obj, list)


def _is_pinning_format(pinning_format):
    # noinspection PyBroadException
    try:

        return all(isinstance(val, int) and val > 0
                   for val in pinning_format) and len(pinning_format) == 2

    except:

        pass

    return False


@decorators.memoize
class Serializer(object):
    def __init__(self, factory):

        """

        :type factory: AbstractModelFactory
        """
        self._factory = factory
        self._logger = Logger(factory.__name__)

    def dump(self, model, path):

        if self._can_dump_to_file(model):

            conf = SerializationHelper.get_config(path)
            serialized_model = self.serialize(model)
            section = self.get_section_name(model)

            if conf and serialized_model and section:
                SerializationHelper.update_config(conf, section, serialized_model)
                return SerializationHelper.save_config(conf, path)

        return False

    def dump_to_filehandle(self, model, filehandle):

        if self._can_dump_to_file(model):

            serialized_model = self.serialize(model)
            section = self.get_section_name(model)
            conf = ConfigParser(allow_no_value=True)
            SerializationHelper.update_config(conf, section, serialized_model)
            conf.write(filehandle)
            return True

    def _can_dump_to_file(self, model):

        factory = self._factory
        valid = factory.validate(model)

        if factory.STORE_SECTION_HEAD and valid:
            return True

        if not factory.STORE_SECTION_HEAD:
            self._logger.warning("Factory does not know head for sections")

        if not valid:
            self._logger.warning("Model {0} does not have valid data".format(model))
            for invalid in factory.get_invalid_names(model):
                self._logger.error("Faulty value in model {0} for {1} as {2}".format(
                    model, invalid, model[invalid]))

        return False

    def purge(self, model, path):

        conf = SerializationHelper.get_config(path)

        if conf:

            for section in conf.sections():

                if self.get_section_name(model) == section:

                    conf.remove_section(section)
                    return SerializationHelper.save_config(conf, path)
        return False

    def purge_all(self, path):

        conf = SerializationHelper.get_config(None)
        return SerializationHelper.save_config(conf, path)

    def load(self, path):

        conf = SerializationHelper.get_config(path)

        if conf:
            for section in conf.sections():
                yield self._unserialize_section(conf, section)

    def _unserialize_section(self, conf, section):

        keys, vals = zip(*conf.items(section))
        return self._parse_serialization(keys, vals)

    def load_serialized_object(self, serialized_object):

        return self._parse_serialization(*zip(*serialized_object.items()))

    def _parse_serialization(self, keys, vals):

        factory = self._factory
        key_paths = map(SerializationHelper.get_path_from_str, keys)
        dtypes = tuple(self._get_data_type(key_path) for key_path in key_paths)

        model_dict = {key: SerializationHelper.unserialize(val, dtype)
                      for key, key_path, val, dtype in zip(keys, key_paths, vals, dtypes)
                      if not self._get_is_sub_model(dtype, key_path) and not self._get_belongs_to_sub_model(key_path)}

        model = factory.create(**model_dict)

        for key, key_path, val, dtype in zip(keys, key_paths, vals, dtypes):

            if self._get_is_sub_model(dtype, key_path):

                filtered_members = zip(*SerializationHelper.filter_member_model(
                    key_path, key_paths, keys, vals))
                filter_keypaths, filter_keys, filter_vals = filtered_members
                if filtered_members:
                    filter_keys = tuple(self._get_trimmed_keys(filter_keys, key))
                    submodel_factory = self._get_submodel_factory(val, dtype)
                    setattr(model, key, submodel_factory.serializer._parse_serialization(filter_keys, filter_vals))

        return model

    @staticmethod
    def _get_trimmed_keys(keys, prefix_to_trim_away):

        trim_pos = len(prefix_to_trim_away) + 1
        for key in keys:
            yield key[trim_pos:]

    @staticmethod
    def _get_submodel_factory(serialized_value, dtype):

        return SerializationHelper.unserialize(serialized_value, dtype)

    def _get_is_sub_model(self, dtype, key_path):

        return dtype is not None and len(key_path) == 1 and issubclass(dtype, AbstractModelFactory)

    @staticmethod
    def _get_belongs_to_sub_model(key_path):

        return len(key_path) > 1

    def _get_data_type(self, key):

        factory = self._factory
        if key in factory.STORE_SECTION_SERIALIZERS:
            return factory.STORE_SECTION_SERIALIZERS[key]
        return None

    def serialize(self, model):

        serialized_model = dict()

        for keyPath, dtype in self._deep_serialize_keys_and_types(model):
            serializable_val = SerializationHelper.get_value_by_path(model, keyPath)
            serialized_model[SerializationHelper.get_str_from_path(keyPath)] = \
                SerializationHelper.serialize(serializable_val, dtype)

        return serialized_model

    def _deep_serialize_keys_and_types(self, model):

        factory = self._factory
        for key_path, dtype in factory.STORE_SECTION_SERIALIZERS.items():

            if issubclass(dtype, AbstractModelFactory):

                sub_model = getattr(model, SerializationHelper.get_str_from_path(key_path))
                if dtype is AbstractModelFactory:
                    dtype = factory.get_sub_factory(sub_model)

                yield key_path, dtype

                for sub_key_path, sub_dtype in dtype.serializer._deep_serialize_keys_and_types(sub_model):
                    yield key_path + sub_key_path, sub_dtype
            else:
                yield key_path, dtype

    def get_section_name(self, model):

        if isinstance(self._factory.STORE_SECTION_HEAD, list):
            return ", ".join(
                [str(SerializationHelper.get_value_by_path(model, head)) for head in self._factory.STORE_SECTION_HEAD])
        else:
            return str(SerializationHelper.get_value_by_path(model, self._factory.STORE_SECTION_HEAD))


class SerializationHelper(object):
    def __new__(cls, *args):

        raise Exception("This class is static, can't be instantiated")

    @staticmethod
    def filter_member_model(key_filter, keys, *args):

        filter_length = len(key_filter)
        for filteree in zip(keys, *args):

            key = filteree[0]
            if all(filt == k for filt, k in zip(key_filter, key)) and len(key) > filter_length:
                yield (key[filter_length:],) + filteree[1:]

    @staticmethod
    def get_str_from_path(keyPath):

        return ".".join(keyPath)

    @staticmethod
    def get_path_from_str(key):

        return tuple(key.split("."))

    @staticmethod
    def serialize(obj, dtype):

        if issubclass(dtype, Enum):

            return obj.name

        elif dtype in (int, float, str, bool):

            return str(obj)

        elif issubclass(dtype, AbstractModelFactory):
            return cPickle.dumps(dtype)
        else:

            return cPickle.dumps(obj)

    @staticmethod
    def unserialize(obj, dtype):

        if dtype is not None and issubclass(dtype, Enum):
            try:
                return dtype[obj]
            except:
                return None
        elif dtype is bool:
            try:
                return eval(obj)
            except:
                return None
        elif dtype in (int, float, str):
            try:
                return dtype(obj)
            except:
                try:
                    return eval(obj)
                except:
                    return None
        else:
            try:
                return cPickle.loads(obj)
            except:
                return None

    @staticmethod
    def get_value_by_path(model, valuePath):

        ret = None
        for attr in valuePath:
            ret = getattr(model, attr)
            model = ret

        return ret

    @staticmethod
    def get_config(path):

        conf = ConfigParser(
            allow_no_value=True)
        try:
            with open(path, 'r') as fh:
                conf.readfp(fh)
        except IOError:
            pass

        return conf

    @staticmethod
    def update_config(conf, section, serializedModel):

        conf.remove_section(section)
        conf.add_section(section)
        for key, val in serializedModel.items():
            conf.set(section, key, val)

    @staticmethod
    def save_config(conf, path):

        try:
            with open(path, 'w') as fh:
                conf.write(fh)
        except IOError:
            return False
        return True


def rename_setting(settings, old_name, new_name):

    if old_name in settings:
        if new_name not in settings:
            settings[new_name] = settings[old_name]
        del settings[old_name]


def split_and_replace(settings, key, new_key_pattern, new_key_index_names):
    if key in settings:

        for index, new_key_index_name in enumerate(new_key_index_names):
            try:
                settings[new_key_pattern.format(new_key_index_name)] = settings[key][index]
            except (IndexError, TypeError):
                pass

        del settings[key]