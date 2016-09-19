# manageiq-ansible-module

[![travis image][]][travis status]

This Ansible module provides different ManageIQ operations.

[travis image]: https://api.travis-ci.org/dkorn/manageiq-ansible-module.svg?branch=master
[travis status]: https://travis-ci.org/dkorn/manageiq-ansible-module/branches

### Prerequisites

ManageIQ Python API Client package [manageiq-api-client-python] (https://github.com/ManageIQ/manageiq-api-client-python/).

    `$ pip install git+https://github.com/ManageIQ/manageiq-api-client-python.git`

### Getting Started

Currently, the module supports adding an OpenShift containers provider to manageiq.
An example playbook `add_provider.yml` is provided and can be run by:

    `$ ansible-playbook add_provider.yml --extra-vars "name=oshift01 type=openshift-origin state=present miq_url=http://localhost:3000 miq_username=user miq_password=****** hostname=oshift01.com port=8443 token=****** metrics=True hawkular_hostname=hawkular01.com hawkular_port=443"

Alternatively, it is possible to add the following environment variables, and remove them from the extra-vars string:

    `$ export MIQ_URL=http://localhost:3000`
    `$ export MIQ_USERNAME=admin`
    `$ export MIQ_PASSWORD=******`

    `$ ansible-playbook add_provider.yml --extra-vars "name=oshift01 type=openshift-origin state=present hostname=oshift01.com port=8443 token=****** metrics=True hawkular_hostname=hawkular01.com hawkular_port=443"
