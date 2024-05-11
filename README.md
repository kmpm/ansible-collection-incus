# Ansible Collection - kmpm.incus
This repository contains the `kmpm.incus` collection. 
The goal for this collection is to eventually be incorporated
into Ansibles community.general collection.

The module connection module for incus is already included in the `community.general` connection and is not included here.

## Disclaimer
It is very much a Work In Progress and contains bugs, missing features etc.
It might destroy everything on your machine (unlikely) and delete everyting
in incus (somewhat likely). It will eventually be strict about semver versioning but for
not every change could be a breaking one.

## Tested with Ansible
This collection is currently only tested with core-2.16 and python 3.11.
It might be extended to support older versions but currently there are only some python >3.7 
code used.

## External requirements
All modules depend on a locally installed and configured `incus`CLI.
That same incus CLI must have PR https://github.com/lxc/incus/pull/581 included. This probably means `incus > 0.6.0`.

## Using this collection
The collection is not yet published in Ansible Galaxy but can be installed with
`ansible-galaxy collection install git+https://github.com/kmpm/ansible-collection-incus.git

### Modules

```yaml
- hosts: localhost
  connection: local
  - tasks:
    - name: create a network
      incus_network:
        name: make_me_some_network
        type: bridge
        config:
            ipv4.address: "192.168.42.0/24"
            ipv4.dhcp: "false"
            ipv6.address: "none"

    - name: get some info about networks
      incus_network_info:
        name: mynetwork # optional name if you want just one network
        project: default # optional 
        # target: sometarget # defaults to empty
      register: netinfo

    - name: create a instance
      incus_instance:
        name: mycontainer
        source: # No default for source. You will need what you need.
            type: image
            alias: debian/12/cloud
            server: "https://images.linuxcontainers.org"
            protocol: simplestreams
            mode: pull
            allow_inconsistent: false

    - name: delete instance
      incus_instance:
        name: mycontainer
        state: absent

    - name: delete network
      incus_network:
        name: mynetwork
        state: absent
```
### Inventory
There is a incus inventory module but no docs yet.


## License
GPL-3.0-or-later
