# This file is part of the Jsonify.
#
# Copyright (C) 2021 Serghei Iakovlev <egrep@protonmail.ch>
#
# For the full copyright and license information, please view
# the LICENSE file that was distributed with this source code.

import json
import os
from functools import reduce
from urllib.error import HTTPError
from urllib.request import urlopen, Request

from asdicts.dict import path

from .client import create_client
from .exceptions import ValidationError, BadRequest


def create_storage(settings, org_id):
    if 'json_url' in settings:
        return JsonUrlStorage(
            url=settings['json_url'],
            user_agent=os.environ.get('CRAWLER_USER_AGENT'),
            timeout=int(os.environ.get('CRAWLER_TIMEOUT', 5)),
        )

    if 'attachment' in settings:
        return JsonFileStorage(path(settings, 'attachment.file_id'), org_id)

    raise ValidationError('Invalid storage settings')


class JsonUrlStorage:
    def __init__(self, url, user_agent=None, timeout=5):
        self.url = url
        self.user_agent = user_agent
        self.timeout = timeout

    @property
    def contents(self):
        try:
            if not self.user_agent:
                headers = {}
            else:
                headers = {'User-Agent': self.user_agent}

            request = Request(self.url, headers=headers)
            with urlopen(request, timeout=self.timeout) as response:
                contents = response.read().decode('utf-8')

            return contents
        except HTTPError as exc_info:
            msg = str(exc_info)
            raise BadRequest(
                message='Unable to fetch JSON contents from the remote server',
                payload={
                    'detail': f'Response from the remote server: {msg}: {self.url}'
                }
            )


class JsonFileStorage:
    def __init__(self, file_id, org_id):
        self.file_id = file_id
        self.org_id = org_id

    @property
    def contents(self):
        client = create_client(self.org_id)
        stream = client.addons.files.download(self.file_id)

        file_contents = ''

        # With the following streaming code, the Python memory usage is
        # restricted regardless of the size of the downloaded file:
        with stream as r:
            for chunk in r.iter_content(chunk_size=512, decode_unicode=True):
                file_contents += chunk

        return file_contents


class JsonDecoder:

    def __init__(self, contents):
        self.contents = json.loads(contents)

    def list_paths(self):
        """Create paths of all nested dictionary values."""
        paths = self._find_list_fields(self.contents)
        return reduce(lambda x, y: x + ['.'.join(y)], paths, [])

    def fields(self, root):
        """Get all keys pointing to lists using `the_path` as a start point."""
        result = []
        first_object = path(self.contents, root)
        if isinstance(first_object, list) and len(first_object):
            first_object = first_object[0]
        if isinstance(first_object, dict):
            result = first_object.keys()
        return result

    def _find_list_fields(self, obj, container=None):
        """Create paths of all nested dictionary values."""
        if not isinstance(obj, dict):
            return []
        if container is None:
            container = []

        for k, v in obj.items():
            new_container = container + [k]
            if isinstance(v, dict):
                for u in self._find_list_fields(v, new_container):
                    yield u
            elif isinstance(v, list):
                yield new_container
