# -*- coding: utf-8 -*-
# Based on connection/incus.py (c) 2023, Stephane Graber <stgraber@stgraber.org>
# (c) 2023, Peter Magnusson <me@kmpm.se>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from typing import List, Dict, Any, Union
import json
from subprocess import Popen, PIPE
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils.common.yaml import yaml_load
from ansible.module_utils._text import to_bytes, to_text
from ansible.module_utils.six.moves.urllib.parse import urlencode
from ansible.module_utils.common.dict_transformations import dict_merge
import q

class IncusClientException(Exception):
    def __init__(self, msg, **kwargs):
        self.msg = msg
        self.kwargs = kwargs

    def __str__(self):
        return '{0} {1}'.format(self.msg, self.kwargs)


class IncusClient(object):
    def __init__(self, remote='local', project='default', target=None, debug=False, *args, **kwargs):
        self.debug = debug
        self.remote = remote
        self.project = project
        self.target = target
        self.logs = []

        self._incus_cmd = get_bin_path("incus")
        if not self._incus_cmd:
            raise IncusClientException("incus command not found in PATH")

    def _parseErr(self, returncode, stderr):
        err_params = {"rc": returncode}
        if self.debug:
            err_params['logs'] = self.logs
        if stderr != '':
            err_params['error'] = stderr
            raise IncusClientException(stderr, **err_params)
        elif returncode != 0:
            raise IncusClientException('Error Exit {0}'.format(returncode), **err_params)

    def _parsErrFromJson(self, json_data: Dict[str, Any], ok_errors: List[int]) -> Union[IncusClientException, None]:
        if json_data.get('type') == 'error':
            if json_data['error_code'] in ok_errors:
                return None
            else:
                err_params = {'error_code': json_data['error_code']}
                if self.debug:
                    err_params['logs'] = self.logs
                raise IncusClientException(json_data['error'], **err_params)
        return None

    def list(self, filter: str = '') -> List[Dict[str, Any]]:
        """List instances from Incus.
        Returns a list of instances.
        """
        data = self._execute('list', '--format', 'json', filter)
        return json.loads(data)

    def query_raw(self,
              method: str, url: str,
              payload: Dict[str, Any] = {},
              url_params: Dict[str, Any] = {},
              ok_errors: List[int] = []
              ) -> Union[Dict[str, Any],None]:
        """Query Incus API.
        Returns the response as a dict.
        """
        if not 'project' in url_params:
            url_params['project'] = self.project
        if not 'target' in url_params and self.target:
            url_params['target'] = self.target

        if '?' in url:
            url = url + '&' + urlencode(url_params)
        else:
            url = url + '?' + urlencode(url_params)

        args = ['query', '-X', method, url, '--wait', '--raw']
        if self.debug:
            self.logs.append(args)

        if len(payload) > 0:
            args.extend(["--data", json.dumps(payload)])
        q(args)

        response = self._execute(*args)
        json_data = json.loads(response)

        self._parsErrFromJson(json_data, ok_errors)

        return json_data

    def _execute(self, *args):
        """Execute incus command."""
        if self.debug:
            self.logs.append(args)
        local_cmd = [self._incus_cmd]
        if len(args) > 0:
            local_cmd.extend(args)

        try:
            local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

            process = Popen(local_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
            stdout, stderr = process.communicate()

            stdout = to_text(stdout)
            stderr = to_text(stderr)
        except Exception as e:
            err_params = {}
            err_params['error'] = e
            if self.debug:
                err_params['logs'] = self.logs
            raise IncusClientException(str(e), **err_params)

        self._parseErr(process.returncode, stderr)
        return stdout


