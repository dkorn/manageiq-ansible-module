# manageiq-ansible-module

[![travis image][]][travis status]

Ansible modules which provide different ManageIQ operations.

[travis image]: https://api.travis-ci.org/dkorn/manageiq-ansible-module.svg?branch=master
[travis status]: https://travis-ci.org/dkorn/manageiq-ansible-module/branches

## Prerequisites

ManageIQ Python API Client package [manageiq-api-client-python] (https://github.com/ManageIQ/manageiq-api-client-python/).

    `$ pip install git+https://github.com/ManageIQ/manageiq-api-client-python.git`


## Getting Started

### manageiq_provider module

The `manageiq_provider` module currently supports adding, updating and deleting an OpenShift and Amazon EC2 providers to manageiq.
Example playbooks `add_openshift_provider.yml` and `add_amazon_provider` are provided.

Usage:

    `$ ansible-playbook add_openshift_provider.yml --extra-vars "name=oshift01 provider_type=openshift-origin state=present zone=default miq_url=http://localhost:3000 miq_username=user miq_password=****** provider_api_hostname=oshift01.com provider_api_port=8443 provider_api_auth_token=****** metrics=True hawkular_hostname=hawkular01.com hawkular_port=443"


To update an existing provider pass the changed values together with the required parameters.

To delete a provider change `state=absent`.

After addition or update, the authentication validation is verified for the provider.


### manageiq_policy_assignment module

The `manageiq_policy_assignment` module currently supports assigning and unassigning Policies and Policy Profiles on resources in manageiq.
An example playbook `assign_policy.yml` is provided.

Usage:

    `$ ansible-playbook assign_policy.yml --extra-vars "entity=policy entity_name=openscap resource=provider resource_name=openshift01 state=present miq_url=http://localhost:3000 miq_username=user miq_password=******"


To unassign a policy/policy profile on a resource change `state=absent`.


## SSL Cert Verification

SSL verification for HTTPS requests is enabled by default.

To use a self-signed certificate pass the certificate file or directory path using the ca_bundle_path option: `ca_bundle_path: '/path/to/certfile'`.
To ignore verifying the SSL certificate pass `verify_ssl: False`


## Using Environment Variables

It is possible to add the following environment variables, and remove them from playbook options.

    `$ export MIQ_URL=http://localhost:3000`
    `$ export MIQ_USERNAME=admin`
    `$ export MIQ_PASSWORD=******`
