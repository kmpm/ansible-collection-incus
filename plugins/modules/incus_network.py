#!/usr/bin/python
# -*- coding: utf-8 -*-
# (c) 2024, Peter Magnusson <me@kmpm.se>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = '''
---
module: incus_network
author: "Peter Magnusson (@kmpm)"
short_description: Manage Incus Network resources
description:
  - Management of Incus Network resources
options:
    name:
        description:
            - Name of the network
        type: str
        required: true
    remote:
        description: The remote to use for the Incus CLI.
        type: str
        default: local
    project:
        description:
            - Project to manage the network in
        type: str
        default: default
    description:
        description:
            - Description of the network
        type: str
        required: false
    config:
        description:
            - The config for the network
        type: dict
        required: false
    target:
        description:
          - For cluster deployments. Will attempt to create an instance on a target node.
            If the instance exists elsewhere in a cluster, then it will not be replaced or moved.
            The name should respond to same name of the node you see in C(incus cluster list).
        type: str
        required: false
    type:
        description:
            - Type of network
        type: str
        choices: [bridge, ovn, macvlan, sriov, physical]
        default: bridge
    state:
        description:
            - State of the network
        type: str
        choices: [present, absent]
        default: present
'''

EXAMPLES = '''
- host: localhost
  connection: local
  tasks:
    - name: Get all networks
      kmpm.incus.incus_network:
        name: testnet0
        config:
            ipv4.address: "192.168.171.1/24"
            ipv4.dhcp": "false"
            "ipv6.address": "none"
        type: "bridge"
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.kmpm.incus.plugins.module_utils.incuscli import IncusClient, IncusClientException


INCUS_ANSIBLE_STATES = {
    'present': '_created',
    'unmanaged': '_unmanaged',
    'absent': '_deleted'
}


ANSIBLE_INCUS_STATES = {
    '': 'absent',
    'Unmanaged': 'unmanaged',
    'Created': 'present',
}


CONFIG_PARAMS = ['name', 'project', 'config', 'description', 'state', 'target', 'type']


class IncusNetworkManagement(object):
    def __init__(self, module, **kwargs):
        self.module = module

        self.api_endpoint = '/1.0/networks'

        self.name = self.module.params['name']
        self.project = self.module.params['project']
        self.config = self._build_config()
        self.state = self.module.params['state']
        self.type = self.module.params['type']
        self.target = self.module.params['target']
        self.description = self.module.params.get('description', None)

        self.debug = self.module._verbosity >= 3

        self.current_network = {}

        try:
            self.client = IncusClient(
                project=self.project,
                target=self.target,
                debug=self.debug
            )
        except IncusClientException as e:
            self.module.fail_json(msg=e.msg)

        self.actions = []
        self.diff = {'before': {}, 'after': {}}

    def _build_config(self):
        config = {}
        for attr in CONFIG_PARAMS:
            param_val = self.module.params.get(attr, None)
            if param_val is not None:
                config[attr] = param_val
        return config

    def _get_network(self):
        url = '{0}/{1}'.format(self.api_endpoint, self.name)
        try:
            return self.client.query_raw('GET', url, ok_errors=[404])
        except IncusClientException as e:
            return {'type': 'error'}

    def _get_network_state(self):
        url = '{0}/{1}/state'.format(self.api_endpoint, self.name)
        try:
            return self.client.query_raw('GET', url)
        except IncusClientException as e:
            return {'type': 'error'}

    @staticmethod
    def _incus_to_module_state(resp_json):
        if resp_json['type'] == 'error':
            return 'absent'
        data = resp_json.get('metadata', {})
        managed = data.get('managed', True)
        if not managed:
            return ANSIBLE_INCUS_STATES['Unmanaged']
        state = data.get('status', '')
        return ANSIBLE_INCUS_STATES[state]

    def _is_managed(self):
        return (self.current_network.get('type', '') == 'sync'
                and bool(self.current_network.get('metadata', {}).get('managed', False)))

    def _is_used(self):
        usage = self.current_network.get('metadata', {}).get('used_by', [])
        return len(usage) > 0

    def _delete_network(self):
        if not self._is_managed():
            self.module.fail_json(msg='Failed to remove network. It is not managed by incus')
            return

        if self._is_used():
            self.module.fail_json(msg='Failed to remove network. It is in use')
            return

        url = '{0}/{1}'.format(self.api_endpoint, self.name)
        if not self.module.check_mode:
            self.client.query_raw('DELETE', url)

        # update diff
        self.diff['after']['network'] = dict(name=self.name, project=self.project, state="absent")

        self.actions.append('delete')

    def _create_network(self):
        url = self.api_endpoint
        payload = self.config.copy()
        {
            'config': self.config.copy(),
            'name': self.name,
        }
        if self.description:
            payload['description'] = self.description

        if not self.module.check_mode:
            self.client.query_raw('POST', url, payload=payload)
        self.actions.append('create')

    def _created(self):
        if self.current_state == 'unmanaged':
            self.module.fail_json(msg='Failed to (re)create network. It exists but is not managed by incus')
            return

        if self.current_state == 'absent':
            self._create_network()

    def _deleted(self):
        if self.current_state == 'absent':
            return
        if self.current_state == 'unmanaged':
            self.module.fail_json(msg='Failed to delete network. It exists but is not managed by incus')
            return
        self._delete_network()

    def _unmanaged(self):
        # FIXME: Fail, warn or skipp
        self.module.fail_json(msg='Unmanaged state not implemented')

    def run(self):
        try:
            self.current_network = self._get_network()
            self.diff['before']['network'] = self.current_network['metadata']
            self.diff['after']['network'] = self.config
            self.current_state = self._incus_to_module_state(self.current_network)

            self.diff['before']['state'] = self.current_state
            self.diff['after']['state'] = self.state

            action = getattr(self, INCUS_ANSIBLE_STATES[self.state])
            action()

            state_changed = len(self.actions) > 0
            result_json = {
                'log_verbosity': self.module._verbosity,
                'changed': state_changed,
                'old_state': self.current_state,
                'actions': self.actions,
                'diff': self.diff,
                'network': self.diff['after']['network'],
            }
            if self.debug:
                result_json['logs'] = self.client.logs

            self.module.exit_json(**result_json)
        except IncusClientException as e:
            state_changed = len(self.actions) > 0
            fail_params = {
                'msg': e.msg,
                'actions': self.actions,
                'changed': state_changed,
                'diff': self.diff
            }
            if self.client.debug:
                fail_params['logs'] = self.client.logs
            self.module.fail_json(**fail_params)


def main():
    '''Ansible Main module.'''

    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            remote=dict(type='str', default='local'),
            project=dict(type='str', default='default'),
            description=dict(type='str', required=False),
            config=dict(type='dict', required=False),
            state=dict(type='str', default='present', choices=['present', 'absent']),
            target=dict(type='str', required=False),
            type=dict(type='str', default='bridge', choices=['bridge', 'ovn', 'macvlan', 'sriov', 'physical'])
        ),
        supports_check_mode=True
    )

    resource_manager = IncusNetworkManagement(module=module)
    resource_manager.run()


if __name__ == '__main__':
    main()
