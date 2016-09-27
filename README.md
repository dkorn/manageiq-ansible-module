# manageiq-ansible-module

[![travis image][]][travis status]

Ansible modules which provide different ManageIQ operations.

[travis image]: https://api.travis-ci.org/dkorn/manageiq-ansible-module.svg?branch=master
[travis status]: https://travis-ci.org/dkorn/manageiq-ansible-module/branches

### Prerequisites

ManageIQ Python API Client package [manageiq-api-client-python] (https://github.com/ManageIQ/manageiq-api-client-python/).

    `$ pip install git+https://github.com/ManageIQ/manageiq-api-client-python.git`

### Getting Started

###### manageiq_provider module

The `manageiq_provider` module currently supports adding, updating and deleting an OpenShift provider to manageiq.
An example playbook `add_provider.yml` is provided and can be run by:

    `$ ansible-playbook add_provider.yml --extra-vars "name=oshift01 type=openshift-origin state=present zone=default miq_url=http://localhost:3000 miq_username=user miq_password=****** hostname=oshift01.com port=8443 token=****** metrics=True hawkular_hostname=hawkular01.com hawkular_port=443"

Alternatively, it is possible to add the following environment variables, and remove them from the extra-vars string:

    `$ export MIQ_URL=http://localhost:3000`
    `$ export MIQ_USERNAME=admin`
    `$ export MIQ_PASSWORD=******`

    `$ ansible-playbook add_provider.yml --extra-vars "name=oshift01 type=openshift-origin state=present add_zone_option hostname=oshift01.com port=8443 token=****** metrics=True hawkular_hostname=hawkular01.com hawkular_port=443"

To update an existing provider pass the changed values together with the required parameters.

To delete an OpenShift provider change `state=absent`.

After addition or update, the authentication validation is verified for the provider.

###### manageiq_policy_assignment module

The `manageiq_policy_assignment` module currently supports assigning and unassigning Policies and Policy Profiles on resources in manageiq.
An example playbook `assign_policy.yml` is provided and can be run by:

    `$ ansible-playbook assign_policy.yml --extra-vars "entity=policy entity_name=openscap resource=provider resource_name=openshift01 state=present miq_url=http://localhost:3000 miq_username=user miq_password=******"

Alternatively, it is possible to add the following environment variables, and remove them from the extra-vars string:

    `$ export MIQ_URL=http://localhost:3000`
    `$ export MIQ_USERNAME=admin`
    `$ export MIQ_PASSWORD=******`

    `$ ansible-playbook assign_policy.yml --extra-vars "entity=policy entity_name=openscap resource=provider resource_name=openshift01 state=present"

To unassign a policy/policy profile on a resource change `state=absent`.
