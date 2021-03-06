# This file is part of the Jsonify.
#
# Copyright (C) 2021 Serghei Iakovlev <egrep@protonmail.ch>
#
# For the full copyright and license information, please view
# the LICENSE file that was distributed with this source code.

from asdicts.dict import path

from . import models


class SettingsTransformer:

    CHOICE = 'choice'
    RADIO_GROUP_MANUAL = 'radio_group_manual'
    MULTIPLE_CHOICE = 'multiple_choice'
    SEQUENCE = 'sequence'
    FIELDS_MAPPING = 'fields_mapping'
    MATCH = 'match'
    MAPPING = 'mapping'
    GROUP = 'group'

    def transform(self, settings=None) -> dict:
        if settings is None:
            settings = dict()
        elif isinstance(settings, dict):
            return settings

        # TODO: Raise exception on non list data type
        return self.from_list(settings)

    def from_list(self, settings: list) -> dict:
        result = dict()
        for s in settings:
            # TODO: Raise exception on non dict data type
            result[s['name']] = self._transform_setting(s)
        return result

    def _transform_setting(self, setting: dict):
        setting_type = str(setting.get('type', ''))

        # TODO: radio_group_manual, multiple_choice, sequence
        # TODO: fields_mapping, match, mapping, group
        if setting_type in [self.CHOICE, self.RADIO_GROUP_MANUAL]:
            return path(setting, 'data.value')
        else:
            # Otherwise return the data or None
            return path(setting, 'data')


def string_list_to_resource_fields(string_list):
    result = []
    for item in string_list:
        result.append(string_to_resource_field(item))

    return result


def string_to_resource_field(item):
    return models.Field(
        rf_id=item,
        name=item,
    )


def documents_to_resource_fields(documents):
    result = []

    for document in documents:
        field = models.Field(
            rf_id=path(document, 'id'),
            name=path(document, 'name'),
        )
        result.append(field)

    return result


def field_to_resource_fields(fields):
    result = []

    for field in fields:
        rf = models.Document(
            resource_id=path(field, 'id'),
            name=path(field, 'name'),
            resource_type=path(field, 'icon_type'),
            document_id=path(field, 'group.id'),
            document_name=path(field, 'group.name'),
        )
        result.append(rf)

    return result
