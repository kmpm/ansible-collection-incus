# -*- coding: utf-8 -*-
# Copyright (c) 2021, Frank Dornheim <dornheim@posteo.de>
# Copyright (c) 2024, Peter Magnusson <me@kmpm.se>
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import pytest
from ansible.inventory.data import InventoryData
from ansible_collections.kmpm.incus.plugins.inventory.incus import InventoryModule

HOST_COMPARATIVE_DATA = {
    'ansible_connection': 'community.general.incus', 'ansible_host': 'vlantest', 'ansible_incus_os': 'Debian',
    'ansible_incus_release': 'bookworm', 'ansible_incus_profiles': ['default'],
    'ansible_incus_project': 'default',
    'ansible_incus_status': 'running', 'ansible_incus_location': 'Berlin',
    'inventory_hostname': 'vlantest', 'inventory_hostname_short': 'vlantest'
    # FIXME: 'ansible_incus_vlan_ids': {'my-macvlan': 666},
}
GROUP_COMPARATIVE_DATA = {
    'all': [], 'ungrouped': [], 'testpattern': ['vlantest'],
    # FIXME: 'vlan666': ['vlantest'],
    'locationBerlin': ['vlantest'],
    'osDebian': ['vlantest'], 'releaseBookworm': ['vlantest'], 'releaseBionic': [], 'profileDefault': ['vlantest'],
    'profileX11': [], 'netRangeIPv4': ['vlantest'], 'netRangeIPv6': ['vlantest']}
GROUP_Config = {
    'testpattern': {'type': 'pattern', 'attribute': 'test'},
    # FIXME: 'vlan666': {'type': 'vlanid', 'attribute': 666},
    'locationBerlin': {'type': 'location', 'attribute': 'Berlin'},
    'osDebian': {'type': 'os', 'attribute': 'debian'},
    'releaseBookworm': {'type': 'release', 'attribute': 'bookworm'},
    'releaseBionic': {'type': 'release', 'attribute': 'bionic'},
    'profileDefault': {'type': 'profile', 'attribute': 'default'},
    'profileX11': {'type': 'profile', 'attribute': 'x11'},
    'netRangeIPv4': {'type': 'network_range', 'attribute': '10.201.82.0/24'},
    'netRangeIPv6': {'type': 'network_range', 'attribute': 'fd42:9ad6:a276:908a:216:3eff::/96'}}


@pytest.fixture
def inventory():
    inv = InventoryModule()
    inv.inventory = InventoryData()
    # Test Values
    inv.data = inv.load_yaml_data('tests/unit/plugins/inventory/fixtures/incus_inventory.atd')  # Load Test Data
    inv.groupby = GROUP_Config
    inv.prefered_instance_network_interface = 'eth'
    inv.prefered_instance_network_family = 'inet'
    inv.status_filter = 'running'
    inv.type_filter = 'all'
    inv.project_filter = 'all'
    inv.dump_data = False

    return inv


def test_verify_file(tmp_path, inventory):
    file = tmp_path / "foobar.incus.yml"
    file.touch()
    assert inventory.verify_file(str(file)) is True


def test_verify_file_bad_config(inventory):
    assert inventory.verify_file('foobar.incus.yml') is False


def test_build_inventory_hosts(inventory):
    """Load example data and start the inventoryto test the host generation.

    After the inventory plugin has run with the test data, the result of the host is checked."""
    inventory._populate()
    generated_data = inventory.inventory.get_host('vlantest').get_vars()

    eq = True
    failures = []
    for key, value in HOST_COMPARATIVE_DATA.items():
        if generated_data[key] != value:
            failures.append(f"{key}: != {value}")
            eq = False
    assert eq, failures


def test_build_inventory_groups(inventory):
    """Load example data and start the inventory to test the group generation.

    After the inventory plugin has run with the test data, the result of the host is checked."""
    inventory._populate()
    generated_data = inventory.inventory.get_groups_dict()

    eq = True
    failures = []
    for key, value in GROUP_COMPARATIVE_DATA.items():
        if generated_data[key] != value:
            failures.append(f"{key}: != {value}")
            eq = False
    assert eq, failures


def test_build_inventory_groups_with_no_groupselection(inventory):
    """Load example data and start the inventory to test the group generation with groupby is none.

    After the inventory plugin has run with the test data, the result of the host is checked."""
    inventory.groupby = None
    inventory._populate()
    generated_data = inventory.inventory.get_groups_dict()
    group_comparative_data = {'all': [], 'ungrouped': []}

    eq = True
    print("data: {0}".format(generated_data))
    for key, value in group_comparative_data.items():
        if generated_data[key] != value:
            eq = False
    assert eq
