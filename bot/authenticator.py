# This file is part of the Jsonify.
#
# Copyright (C) 2021 Serghei Iakovlev <egrep@protonmail.ch>
#
# For the full copyright and license information, please view
# the LICENSE file that was distributed with this source code.

from dataclasses import dataclass
from datetime import datetime, timedelta

from airslate.client import Client
from asdicts.dict import path
from flask import current_app

from . import logger
from .exceptions import BadRequest


@dataclass
class AddonIdentity:
    """Class for storing addon identity."""
    token: str
    domain: str
    expires: datetime


def authenticate(org_uid: str, client_id: str, client_secret: str) -> AddonIdentity:
    client = Client(base_url=current_app.config.get('API_BASE_URI'))

    logger.info(
        'Trying to authenticate bot %s for organization %s' %
        (client_id, org_uid)
    )

    # We're expect a response in the following format:
    #    {
    #        'meta': {
    #            'token_type': 'Bearer',
    #            'expires': 1209000,
    #            'access_token': '...',
    #            'refresh_token': '...',
    #            'domain': '',
    #        }
    #    }
    #
    identity = client.addons.auth(org_uid, client_id, client_secret)

    logger.info(
        'Received identity response for organization %s: %s' %
        (org_uid, identity)
    )

    if 'meta' not in identity:
        raise BadRequest(message='The `meta` field is required.')

    token = path(identity, 'meta.access_token')
    domain = path(identity, 'meta.domain')
    expires = path(identity, 'meta.expires')

    if expires and token and domain:
        expires = datetime.utcnow() + timedelta(seconds=int(expires))
        return AddonIdentity(token, domain, expires)

    fields = {'expires': expires, 'access_token': token, 'domain': domain}
    missed = [k for k in fields.keys() if not fields[k]]
    message = map(lambda f: f'The `meta.{f}` field is required.', missed)

    raise BadRequest(message=list(message))
