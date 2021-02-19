# This file is part of the Jsonify.
#
# Copyright (C) 2021 Serghei Iakovlev <egrep@protonmail.ch>
#
# For the full copyright and license information, please view
# the LICENSE file that was distributed with this source code.

from airslate.client import Client
from airslate.entities.documents import Document
from asdicts.dict import path

from .client import create_client


def get_documents(flow_id: str, client: Client):
    """Get supported documents for a given flow."""
    return client.flows.documents.collection(flow_id, include='fields')


def document_list(org_id: str, flow_id: str, fields_types=None):
    """Create a list of documents ids and names from a given flow."""
    client = create_client(org_id)
    documents = get_documents(flow_id, client)

    if fields_types is not None:
        documents = _filter_documents(documents, fields_types)

    return [{'id': doc['id'], 'name': doc['name']} for doc in documents]


def field_list(org_id: str, flow_id: str, fields_types=None):
    """Get supported fields for a given flow."""
    client = create_client(org_id)
    documents = get_documents(flow_id, client)
    return _filter_fields(documents, fields_types)


def _filter_fields(documents: [Document], filed_types=None):
    result = []

    def expected_field(inc, f_ids):
        attr_type = path(inc, 'attributes.field_type')
        if filed_types is not None and attr_type not in filed_types:
            return False
        return inc['type'] == 'dictionary' and inc['id'] in f_ids

    for doc in documents:
        ids = [d['id'] for d in path(doc.relationships, 'fields.data', [])]
        fields = [i for i in doc.included if expected_field(i, ids)]

        for field in fields:
            f_type = path(field, 'attributes.field_type')
            f_text = f_type.capitalize()
            f_name = path(field, 'attributes.name')
            response = {
                'id': f_name,
                'name': f'{f_text} Field: {f_name}',
                'icon_type': f_type,
                'group': {
                    'id': doc['id'],  # TODO: doc.id
                    'name': doc['name'],
                }
            }
            result.append(response)

    return result


def _filter_documents(documents: [Document], filed_types):
    """Filter the list of documents with fields from ``filed_types``."""
    result = []

    for document in documents:
        for field in document.fields:
            if field['field_type'] in filed_types:
                result.append(document)
                break

    return result
