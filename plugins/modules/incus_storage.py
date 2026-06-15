#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2026, Simon Bernier St-Pierre <git.sbstp.ca@gmail.com>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
from ansible_collections.kmpm.incus.plugins.module_utils.incuscli import Patch
__metaclass__ = type

DOCUMENTATION = r'''
---
module: incus_storage
author: "Simon Bernier St-Pierre (@sbstp)"
short_description: Manage Incus Storage resources
description:
  - Management of Incus Storage resources
options:
    name:
        description:
            - Name of the storage pool
        type: str
        required: true
    remote:
        description: The remote to use for the Incus CLI.
        type: str
        default: local
    project:
        description:
            - Project to manage the profile in
        type: str
        default: default
    description:
        description:
            - Description of the storage pool
        type: str
        required: false
    config:
        description:
            - The config for the storage pool
        type: dict
        required: false
        default: {}
    driver:
        description:
            - The driver for the storage pool
        type: str
        required: false
    state:
        description:
            - State of the storage pool
        type: str
        choices: [present, absent]
        default: present
'''

EXAMPLES = '''
- host: localhost
  connection: local
  tasks:
    - name: Create a storage pool
      kmpm.incus.incus_storage:
        name: tank
        description: tank
        driver: btrfs
        config:
            size: 100GiB
            btrfs.mount_options: compress=zstd,noatime
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kmpm.incus.plugins.module_utils.incuscli import IncusClient

SUPPORTED_FIELDS = {'name', 'description', 'driver', 'config'}


class IncusStorageManagement(object):
    def __init__(self, module):
        self.module = module
        self.name = self.module.params['name']
        remote = self.module.params['remote']
        project = module.params['project']
        driver = self.module.params['driver']
        description = self.module.params['description']
        config = self.module.params['config']
        next_state = self.module.params['state']

        self.client = IncusClient(project=project, remote=remote)
        self.actions = []

        current = self.client.get_storage(self.name)
        self.patch = Patch(
            current=current,
            supported_fields=SUPPORTED_FIELDS,
            patch=dict(
                name=self.name,
                description=description,
                driver=driver,
                config=config,
            ),
            next_state=next_state,
        )


    def run(self):
        patch = self.patch
        if patch.is_created():
            if patch.payload.get("driver") is None:
                raise Exception('cannot create storage without driver')
            if not self.module.check_mode:
                self.client.query_raw_checked('POST', '/1.0/storage-pools', patch.payload)
            self.actions.append('create')
        elif patch.is_updated():
            if patch.before['driver'] != patch.after['driver']:
                raise Exception("cannot update driver on existing storage")
            if not self.module.check_mode:
                self.client.query_raw_checked('PATCH', '/1.0/storage-pools/{0}'.format(self.name), patch.payload)
            self.actions.append('update')
        elif patch.is_deleted():
            if not self.module.check_mode:
                self.client.query_raw_checked('DELETE', '/1.0/storage-pools/{0}'.format(self.name))
            self.actions.append('delete')

        return self.state()

    def state(self):
        return self.patch.result(actions=self.actions)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            remote=dict(type='str', default='local'),
            project=dict(type='str', default='default'),
            driver=dict(type='str', required=False),
            description=dict(type='str', required=False),
            config=dict(type='dict', required=False, default={}),
            state=dict(type='str', choices=['present', 'absent'], default='present'),
        ),
        supports_check_mode=True
    )
    incus = IncusStorageManagement(module)
    try:
        module.exit_json(**incus.run())
    except Exception as e:
        module.fail_json({
            "error": str(e),
            **incus.state(),
        })


if __name__ == '__main__':
    main()
