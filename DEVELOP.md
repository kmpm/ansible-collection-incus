# Developing the collection

## Recommended reading
- https://www.redhat.com/sysadmin/ansible-dynamic-inventory-python
- https://www.redhat.com/sysadmin/ansible-plugin-inventory-files
- https://github.com/zestyping/q

### If you are using vscode
- [Medium - Guide to writing and debugging ansible modules in vscode](https://medium.com/@tushe_33516/guide-to-writing-and-debugging-ansible-modules-in-vscode-a-nearly-perfect-setup-ad54024a466a)
- [GH - Sample Project for debugging with vscode](https://github.com/troshlyak/vscode_ansible)


## Testing
### Using ansible-doc
```shell
# Does ansible recognize the inventory plugin
$ ansible-doc -t inventory -l | grep incus
kmpm.incus.incus                                        Incus inventory sou...

# Does it recognize the instance module
$ ansible-doc -t module -l | grep incus
kmpm.incus.incus_instance 

```

### Simple execution
```shell
ansible hostname -i inventory_source -m ansible.builtin.ping

```

### Sanity
First fix any format or similar errors

```shell
# to run it in docker
ansible-test sanity --docker default -v

# to run it locally with only single python version
ansible-test sanity --python 3.11 -v
```


### Unit and integration

```shell

# test with local venv
ansible-test units --venv --python 3.11

ansible-test integration --venv --python 3.11 unsupported/incus_instance
```


### Links
- https://docs.ansible.com/ansible/latest/dev_guide/developing_collections_testing.html
- https://docs.ansible.com/ansible/latest/dev_guide/testing_units.html
- https://docs.ansible.com/ansible/latest/dev_guide/testing_integration.html
