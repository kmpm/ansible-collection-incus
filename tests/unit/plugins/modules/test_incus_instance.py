# Copyright (c) Ansible project
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import json

import pytest
# from ansible_collections.community.general.tests.unit.compat import mock
# from ansible_collections.kmpm.general.plugins.modules import incus_instance

# class TestMyModule():
#     @mock.patch('ansible_collections.community.general.plugins.modules.lxca_nodes.execute_module', autospec=True)
#     @mock.patch('ansible_collections.community.general.plugins.modules.lxca_nodes.AnsibleModule', autospec=True)
#     def test_instance(self, ansible_mod_cls):
#         mob_obj = ansible_mod_cls.return_value
#         mob_obj.params = {}
#         incus_instance.main()
