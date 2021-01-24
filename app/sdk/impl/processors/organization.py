# This file is part of the Jsonify.
#
# Copyright (c) 2021 airSlate, Inc.
#
# For the full copyright and license information, please view
# the LICENSE file that was distributed with this source code.

from airslate.exceptions import Error as ApiError
from flask import current_app
from requests.exceptions import RequestException
from sqlalchemy import exc

from app import db
from app import logger
from app.models import Organization
from app.sdk import exceptions
from app.sdk.impl.authenticator import authenticate


def connect(organization: Organization) -> Organization:
    try:
        client_id = current_app.config.get('BOT_CLIENT_ID')
        client_secret = current_app.config.get('BOT_CLIENT_SECRET')

        identity = authenticate(
            organization.organization_uid,
            client_id,
            client_secret
        )

        organization.token = identity.token
        organization.domain = identity.domain
        organization.token_expires_at = identity.expires

        db.session.add(organization)
        db.session.flush()
    except ApiError as api_error:
        logger.error(
            'Received error response from API: %s' %
            api_error.message
        )

        # Any 4xx errors at this stage means our error
        if 400 <= api_error.status < 500:
            message = ('Unable to connect organization due to internal '
                       ' error. Please contact bot developer.')
            raise exceptions.InternalServerError(
                payload={'detail': message}
            ) from api_error
        else:
            raise exceptions.BadRequest(
                message='API Error',
                payload={'detail': api_error.message}
            ) from api_error
    except exc.IntegrityError as integrity_error:
        logger.error(integrity_error)

        db.session.rollback()
        raise exceptions.OrganizationConnect(
            message='Already connected',
            payload={'detail': 'Requested organization already connected.'}
        )
    except (exc.SQLAlchemyError, RequestException) as internal_error:
        logger.error(internal_error)

        db.session.rollback()
        raise exceptions.InternalServerError(
            payload={'detail': 'Unable to connect organization.'}
        )
    else:
        db.session.commit()
        logger.info(
            'Organization %s successfully connected' %
            organization.organization_uid
        )

        return organization


def disconnect(org_uid: str):
    rows = db.session.query(Organization).filter_by(organization_uid=org_uid).delete()
    db.session.commit()

    status = bool(rows)
    if not status:
        raise exceptions.OrganizationDisconnect(
            status_code=404,
            message='Not Found',
            payload={'detail': 'Requested organization does not exist.'}
        )

    logger.info(
        'Organization %s successfully disconnected' %
        org_uid
    )
