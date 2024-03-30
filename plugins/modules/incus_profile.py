#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2024, Peter Magnusson <me@kmpm.se>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: incus_profile
author: "Peter Magnusson (@kmpm)"
short_description: Manage Incus Profile resources
description:
  - Management of Incus Profile resources
options:
    name:
        description:
            - Name of the profile
        type: str
        required: true
    project:
        description:
            - Project to manage the profile in
        type: str
        default: default
    description:
        description:
            - Description of the profile
        type: str
        required: false
    config:
        description:
            - The config for the profile
        type: dict
        required: false
        default: {}
    devices:
        description:
            - The devices for the profile
        type: dict
        required: false
        default: {}
    state:
        description:
            - State of the profile
        type: str
        choices: [present, updated, absent]
        default: present
'''

EXAMPLES = '''
- host: localhost
  connection: local
  tasks:
    - name: Create a profile
      kmpm.incus.incus_profile:
        name: my-profile
        description: My profile
'''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kmpm.incus.plugins.module_utils.incuscli import IncusClient, IncusClientException

RESOURCE_PARAMS = ['name', 'description', 'config', 'devices', 'state']


def clean_resource(resource, **defaults):
    out = {}
    if 'config' not in defaults or not bool(defaults['config']):
        defaults['config'] = {}
    if 'devices' not in defaults or not bool(defaults['devices']):
        defaults['devices'] = {}

    for key in list(resource.keys()):
        if key in RESOURCE_PARAMS:
            out[key] = resource[key]
    for key, value in defaults.items():
        if key not in out:
            out[key] = value
    return out


class IncusProfileManagement(object):
    def __init__(self, module):
        self.module = module
        self.client = IncusClient(module.params['project'])

        self.name = self.module.params['name']
        self.description = self.module.params['description']
        self.config = self.module.params['config']
        self.devices = self.module.params['devices']
        self.state = self.module.params['state']
        self.actions = []

    def _get_current(self):
        return self.client.get_profile(self.name)

    def _get_desired(self):
        return clean_resource(self.module.params, state=self.state)

    def _update(self):
        # is there any difference between the current and the desired state?
        got = json.dumps(clean_resource(self.current, state=self.current_state), sort_keys=True)
        want = json.dumps(clean_resource(self._get_desired()), sort_keys=True)

        if got != want:
            if not self.module.check_mode:
                self.client.update_profile(
                    self.name,
                    self.description,
                    self.config,
                    self.devices
                )
            self.diff['after'] = clean_resource(self._get_current(), state=self.state)
            self.actions.append('update')
        else:
            self.diff['after'] = clean_resource(self.current, state=self.current_state)

    def _create(self):
        if bool(self.current):
            self._update()
            return

        if not self.module.check_mode:
            self.client.create_profile(
                self.name,
                self.description,
                self.config,
                self.devices
            )
            self.diff['after'] = clean_resource(self._get_current(), state=self.state)
        self.actions.append('create')

    def _delete(self):
        if not self.client.profile_exists(self.name):
            return
        if not self.module.check_mode:
            self.client.delete_profile(self.name)
        self.actions.append("delete")

    def run(self):
        self.current = self._get_current()
        self.current_state = 'present' if bool(self.current) else 'absent'
        self.diff = {
            'before': clean_resource(self.current, state=self.current_state),
            'after': clean_resource({}, state=self.state)}
        result = dict(
            changed=False,
            message='',
            state=self.state,
        )

        try:
            if self.state == 'present':
                self._create()
            elif self.state == 'absent':
                self._delete()
        except IncusClientException as e:
            self.module.fail_json(msg=str(e))

        result['diff'] = self.diff
        result['actions'] = self.actions
        result['changed'] = len(self.actions) > 0
        result['profile'] = self.diff['after']
        if not self.module.check_mode:
            result['changed'] = bool(self.actions)

        self.module.exit_json(**result)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            project=dict(type='str', default='default'),
            description=dict(type='str', required=False),
            config=dict(type='dict', required=False, default={}),
            devices=dict(type='dict', required=False, default={}),
            state=dict(type='str', choices=['present', 'updated', 'absent'], default='present'),
        ),
        supports_check_mode=True

    )
    incus = IncusProfileManagement(module)
    incus.run()


if __name__ == '__main__':
    main()
