# manageiq-ansible-module

This Ansible module provides different ManageIQ operations. 


### prerequisites

ManageIQ Python API Client package [manageiq-api-client-python] (https://github.com/ManageIQ/manageiq-api-client-python/).

    `$ pip install git+https://github.com/ManageIQ/manageiq-api-client-python.git`

### Getting Started

Currently, the module supports adding an OpenShift containers provider to manageiq.
An example playbook `add_provider.yml` is provided and can be run by:

    `$ ansible-playbook add_provider.yml --extra-vars "name=oshift01 url=http://localhost:3000 hostname=oshift01.com port=8443 username=user password=****** token=******"


