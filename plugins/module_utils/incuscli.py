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

        self._incus_cmd = get_bin_path("incus")

        if not self._incus_cmd:
            raise IncusClientException("incus command not found in PATH")

    def do(self, method, url, *args, **kwargs):
        local_cmd = [
            self._incus_cmd,
            "query",
            "--raw",
            "--wait",
        ]
        if not method == 'GET':
            local_cmd += ['-X', method]
        local_cmd.append(url)
        # print(local_cmd)
        local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

        process = Popen(local_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()

        stdout = to_text(stdout)
        stderr = to_text(stderr)
        # print("url", url, kwargs)
        if stderr:
            raise IncusClientException(stderr, **kwargs)
        if process.returncode != 0:
            raise IncusClientException('Error Exit {0}'.format(process.returncode))
        data = json.loads(stdout)
        # print("url", url, "data", stdout[:30])
        return data

    # def exec_command(self, cmd, in_data=None, sudoable=True):
    #     """ execute a command on the Incus host """
    #     super(Connection, self).exec_command(cmd, in_data=in_data, sudoable=sudoable)

    #     self._display.vvv(u"EXEC {0}".format(cmd),
    #                       host=self._instance())

    #     local_cmd = [
    #         self._incus_cmd,
    #         "--project", self.get_option("project"),
    #         "exec",
    #         "%s:%s" % (self.get_option("remote"), self._instance()),
    #         "--",
    #         self._play_context.executable, "-c", cmd]

    #     local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]
    #     in_data = to_bytes(in_data, errors='surrogate_or_strict', nonstring='passthru')

    #     process = Popen(local_cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE)
    #     stdout, stderr = process.communicate(in_data)

    #     stdout = to_text(stdout)
    #     stderr = to_text(stderr)

    #     if stderr == "Error: Instance is not running.\n":
    #         raise AnsibleConnectionFailure("instance not running: %s" %
    #                                        self._instance())

    #     if stderr == "Error: Instance not found\n":
    #         raise AnsibleConnectionFailure("instance not found: %s" %
    #                                        self._instance())

    #     return process.returncode, stdout, stderr

    # def put_file(self, in_path, out_path):
    #     """ put a file from local to Incus """
    #     super(Connection, self).put_file(in_path, out_path)

    #     self._display.vvv(u"PUT {0} TO {1}".format(in_path, out_path),
    #                       host=self._instance())

    #     if not os.path.isfile(to_bytes(in_path, errors='surrogate_or_strict')):
    #         raise AnsibleFileNotFound("input path is not a file: %s" % in_path)

    #     local_cmd = [
    #         self._incus_cmd,
    #         "--project", self.get_option("project"),
    #         "file", "push", "--quiet",
    #         in_path,
    #         "%s:%s/%s" % (self.get_option("remote"),
    #                       self._instance(),
    #                       out_path)]

    #     local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

    #     call(local_cmd)

    # def fetch_file(self, in_path, out_path):
    #     """ fetch a file from Incus to local """
    #     super(Connection, self).fetch_file(in_path, out_path)

    #     self._display.vvv(u"FETCH {0} TO {1}".format(in_path, out_path),
    #                       host=self._instance())

    #     local_cmd = [
    #         self._incus_cmd,
    #         "--project", self.get_option("project"),
    #         "file", "pull", "--quiet",
    #         "%s:%s/%s" % (self.get_option("remote"),
    #                       self._instance(),
    #                       in_path),
    #         out_path]

    #     local_cmd = [to_bytes(i, errors='surrogate_or_strict') for i in local_cmd]

    #     call(local_cmd)
