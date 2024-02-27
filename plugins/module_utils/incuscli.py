# -*- coding: utf-8 -*-
# Based on lxd.py (c) 2016, Matt Clay <matt@mystile.com>
# (c) 2023, Stephane Graber <stgraber@stgraber.org>
# Copyright (c) 2023 Ansible Project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
import json
__metaclass__ = type

DOCUMENTATION = """
    author: Stéphane Graber (@stgraber)
    name: incus
    short_description: Run tasks in Incus instances via the Incus CLI.
    description:
        - Run commands or put/fetch files to an existing Incus instance using Incus CLI.
    version_added: "8.2.0"
    options:
      remote_addr:
        description:
            - The instance identifier.
        default: inventory_hostname
        vars:
            - name: inventory_hostname
            - name: ansible_host
            - name: ansible_incus_host
      executable:
        description:
            - The shell to use for execution inside the instance.
        default: /bin/sh
        vars:
            - name: ansible_executable
            - name: ansible_incus_executable
      remote:
        description:
            - The name of the Incus remote to use (per C(incus remote list)).
            - Remotes are used to access multiple servers from a single client.
        default: local
        vars:
            - name: ansible_incus_remote
      project:
        description:
            - The name of the Incus project to use (per C(incus project list)).
            - Projects are used to divide the instances running on a server.
        default: default
        vars:
            - name: ansible_incus_project
"""

# import os
from subprocess import Popen, PIPE

# from ansible.module_utils.urls import generic_urlparse
# from ansible.module_utils.six.moves.urllib.parse import urlparse
# from ansible.errors import AnsibleError, AnsibleConnectionFailure, AnsibleFileNotFound
from ansible.module_utils.common.process import get_bin_path
from ansible.module_utils._text import to_bytes, to_text

try:
    import q
except ImportError:
    def q(*args):
        return args


class IncusClientException(Exception):
    def __init__(self, msg, **kwargs):
        self.msg = msg
        self.kwargs = kwargs

    def __str__(self):
        return '{0} {1}'.format(self.msg, self.kwargs)

class IncusNotFoundException(IncusClientException):
    def __init__(self, **kwargs):
        super(IncusNotFoundException, self).__init__('Not found', **kwargs)


class IncusClient(object):
    def __init__(self, remote='local', project='default', debug=False, *args, **kwargs):
        self.debug = debug
        self.remote = remote
        self.project = project
        self.logs = []

        self._incus_cmd = get_bin_path("incus")

        if not self._incus_cmd:
            raise IncusClientException("incus command not found in PATH")

    def do(self, method, url, body_json=None):
        resp_json = self._send_query(method, url, body_json=body_json)
        return resp_json

    def _send_query(self, method, url, body_json=None):
        local_cmd = [
            self._incus_cmd,
            "query",
            "--raw",
            "--wait",
        ]
        if not method == 'GET':
            local_cmd += ['-X', method]

        if not body_json is None:
            body = json.dumps(body_json)
            local_cmd += ['--data', body]

        local_cmd.append(url)
        if self.debug:
            q(local_cmd)

        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        process = Popen(local_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        stdout = to_text(stdout)
        stderr = to_text(stderr)

        resp_json = {}
        if stdout:
            resp_json = json.loads(stdout)

        if self.debug:
            q({'request': {'method': method, 'url': url, 'data': body_json},
            'process':{'stderr': stderr, 'returncode': process.returncode},
            'response': {'json': resp_json}})

        self.logs.append({
            'type': 'query',
            'request': {'method': method, 'url': url, 'data': body_json},
            'process':{'stderr': stderr, 'returncode': process.returncode},
            'response': {'json': resp_json},
        })

        if stderr != '':
            # possibly simulate 404
            if "not found\n" in stderr:
                raise IncusNotFoundException( error_code = 404, error = stderr, returncode=process.returncode)
            raise IncusClientException(stderr, returncode=process.returncode)
        elif process.returncode != 0:
            raise IncusClientException('Error Exit {0}'.format(process.returncode))

        return resp_json
