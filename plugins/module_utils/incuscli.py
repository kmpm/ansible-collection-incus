# -*- coding: utf-8 -*-
# Based on connection/incus.py (c) 2023, Stephane Graber <stgraber@stgraber.org>
# (c) 2023, Peter Magnusson <me@kmpm.se>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from typing import List, Dict, Any
from subprocess import Popen, PIPE
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils.common.yaml import yaml_load
from ansible.module_utils._text import to_bytes, to_text


class IncusClientException(Exception):
    def __init__(self, msg, **kwargs):
        self.msg = msg
        self.kwargs = kwargs

    def __str__(self):
        return '{0} {1}'.format(self.msg, self.kwargs)


class IncusClient(object):
    def __init__(self, remote='local', project='default', debug=False, *args, **kwargs):
        self.debug = debug
        self.remote = remote
        self.project = project
        self.logs = []

        self._incus_cmd = get_bin_path("incus")
        if not self._incus_cmd:
            raise IncusClientException("incus command not found in PATH")

    def list(self, filter: str='') -> List[Dict[str, Any]]:
        """List instances from Incus.
        Returns a list of instances.
        """
        data = self._execute('list', '--format', 'yaml', filter)
        # yaml_data = yaml.safe_load(data)
        return yaml_load(data)

    def _execute(self, *args):
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

    def _parseErr(self, returncode, stderr):
        if stderr != '':
            raise IncusClientException(stderr, returncode=returncode)
        elif returncode != 0:
            raise IncusClientException('Error Exit {0}'.format(returncode))
