from scanomatic.generics.abstract_model_factory import AbstractModelFactory 
from scanomatic.models.scanning_model import ScanningModel 
import scanomatic.io.fixtures as fixtures
import scanomatic.io.app_config as app_config

import os
import re
import string

class ScanningModelFactory(AbstractModelFactory):

    _MODEL = ScanningModel
    _GET_MIN_MODEL = app_config.Config().getMinModel
    _GET_MAX_MODEL = app_config.Config().getMaxModel
    STORE_SECTION_HEAD = ("scanner",)
    STORE_SECTION_SERLIALIZERS = dict(
        numberOfScans=int,
        timeBetweenScans=float,
        projectName=str,
        directoryContainingProject=str,
        projectTag=str,
        scannerTag=str,
        description=str,
        email=str,
        pinningFormats=tuple,
        fixture=str,
        scanner=int,
        mode=str
    )

    @classmethod
    def clamp(cls, model):

        return cls._clamp(model, cls._GET_MIN_MODEL(model, factory=cls),
                          cls._GET_MAX_MODEL(model, factory=cls))

    # noinspection PyMethodOverriding
    @classmethod
    def _correct_type_and_in_bounds(cls, model, attr, dtype):

        return super(ScanningModelFactory, cls)._correct_type_and_in_bounds(
            model, attr, dtype, cls._GET_MIN_MODEL, cls._GET_MAX_MODEL)

    @classmethod
    def _validate_numberOfScans(cls, model):

        return cls._correct_type_and_in_bounds(model, "numberOfScans", int)

    @classmethod
    def _validate_timeBetweenScans(cls, model):

        try:
            model.timeBetweenScans = float(model.timeBetweenScans)
        except:
            return model.FIELD_TYPES.timeBetweenScans

        return cls._correct_type_and_in_bounds(model, "timeBetweenScans", float)

    @classmethod
    def _validate_projectName(cls, model):
        
        try:
            if os.path.isdir(os.path.join(model.directoryContainingProject,
                                          model.projectName)):

                return model.FIELD_TYPES.projectName

        except:

            return model.FIELD_TYPES.projectName

        if len(model.projectName) != len(tuple(c for c in model.projectName 
                             if c in string.letters + string.digits + "_")):

            return model.FIELD_TYPES.projectName

        return True

    @classmethod
    def _validate_directoryContainingProject(cls, model):

        try:

            if os.path.isdir(os.path.abspath(model.directoryContainingProject)):

                return True

        except:

            pass

        return model.FIELD_TYPES.directoryContainingProject

    @classmethod
    def _validate_description(cls, model):

        if (isinstance(model.description, str)):

            return True

        return model.FIELD_TYPES.description

    @classmethod
    def _validate_email(cls, model):


        if (isinstance(model.email, str) and
                (model.email == '' or
                 re.match(r'[^@]+@[^@]+\.[^@]+', model.email))):

            return True

        return model.FIELD_TYPES.email


    @classmethod
    def _validate_pinningFormats(cls, model):
        if AbstractModelFactory._is_pinning_formats(model.pinningFormats):
            return True

        return model.FIELD_TYPES.pinningFormarts

    @classmethod
    def _validate_fixture(cls, model):

        if model.fixture in fixtures.Fixtures():

            return True

        return model.FIELD_TYPES.fixture

    @classmethod
    def _validate_scanner(cls, model):

        if app_config.Config().get_scanner_name(model.scanner) is not None:

            return True

        return model.FIELD_TYPES.scanner
