# This file is part of the Jsonify.
#
# Copyright (c) 2021 airSlate, Inc.
#
# For the full copyright and license information, please view
# the LICENSE file that was distributed with this source code

from dataclasses import dataclass

from asdicts.dict import path

from jsonify import flow
from jsonify.addon_settings import supported_mapping
from .transformers import (
    field_to_resource_fields,
    documents_to_resource_fields,
    SettingsTransformer,
)


@dataclass
class Request:
    org_id: str
    addon_id: str
    flow_id: str
    setting_name: str
    settings: dict


class Response(dict):
    def __init__(self, fields):
        super().__init__(
            data=[field.to_dict() for field in fields]
        )


def create_request(data: dict):
    transformer = SettingsTransformer()

    return Request(
        path(data, 'meta.organization.data.id'),
        path(data, 'data.relationships.organization_addon.data.id'),
        path(data, 'data.relationships.slate.data.id'),
        path(data, 'data.attributes.setting_name'),
        transformer.transform(path(data, 'data.attributes.settings')),
    )


def parse_request(request: Request):
    setting_name = str(request.setting_name)

    if setting_name == 'lists':
        return lists_paths(
            settings=request.settings,
            org_id=request.org_id,
        )
    elif setting_name == 'listed_objects_fields':
        return fields_except_lists(
            settings=request.settings,
            org_id=request.org_id,
        )
    elif setting_name == 'documents':
        # Create a list of supported documents for a given flow.
        return supported_documents(
            settings=request.settings,
            org_id=request.org_id,
            flow_id=request.flow_id
        )
    elif setting_name == 'documents_fields':
        # Create a list of supported document fields for a given flow.
        return supported_document_fields(
            settings=request.settings,
            org_id=request.org_id,
            flow_id=request.flow_id
        )
    else:
        return []


def fields_except_lists(settings: dict, org_id: str):
    pass


def lists_paths(settings: dict, org_id: str):
    pass


def supported_document_fields(settings: dict, org_id: str, flow_id: str):
    """Create a list of supported document fields for a given flow."""
    data_type = settings.get('data_type')
    field_types = supported_mapping(data_type)
    field_list = flow.field_list(org_id, flow_id, field_types)
    return field_to_resource_fields(field_list)


def supported_documents(settings: dict, org_id: str, flow_id: str):
    """Create a list of supported documents for a given flow."""
    data_type = settings.get('data_type')
    field_types = supported_mapping(data_type)
    doc_list = flow.document_list(org_id, flow_id, field_types)
    return documents_to_resource_fields(doc_list)
