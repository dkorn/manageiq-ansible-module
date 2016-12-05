# manageiq-ansible-module

[![travis image][]][travis status]

Ansible modules which provide different ManageIQ operations.

[travis image]: https://api.travis-ci.org/dkorn/manageiq-ansible-module.svg?branch=master
[travis status]: https://travis-ci.org/dkorn/manageiq-ansible-module/branches

## Prerequisites

ManageIQ Python API Client package [manageiq-client] (https://github.com/ManageIQ/manageiq-api-client-python/).

    $ pip install manageiq-client



## Getting Started

    $ pip install -r requirements.txt
    
To try the modules copy and edit the relevant example playbook and execute:

    $ ansible-playbook EDITED_PLAYBOOK.yml
   

## The Modules

### manageiq_provider module

The `manageiq_provider` module currently supports adding, updating and deleting an OpenShift and Amazon EC2 providers to manageiq.
Example playbooks `add_openshift_provider.yml` and `add_amazon_provider` are provided.
To update an existing provider pass the changed values together with the required parameters.
To delete a provider change `state=absent`.
After addition or update, the authentication validation is not verified for the provider at the moment.

### manageiq_user module

The `manageiq_user` module supports adding, updating and deleting users in manageiq.
Example playbook `create_user.yml` is provided.
To update an existing user pass the changed values together with the required parameters.
To delete a user change `state=absent`.

### manageiq_policy_assignment module

The `manageiq_policy_assignment` module currently supports assigning and unassigning Policies and Policy Profiles on resources in manageiq.
An example playbook `assign_policy.yml` is provided.
To unassign a policy/policy profile on a resource change `state=absent`.

### manageiq_custom_attributes module

The `manageiq_custom_attributes` module supports adding, updating and deleting custom attributes on resources in ManageIQ.
Currently the only resources (entities) that supports custom attributes are vms and providers.
An example playbook `add_custom_attributes.yml` is provided.
To delete a custom attributes change `state=absent`.


## Using Environment Variables

It is possible to add the following environment variables, and remove them from playbook options.

    $ export MIQ_URL=http://localhost:3000
    $ export MIQ_USERNAME=admin
    $ export MIQ_PASSWORD=******
    

## SSL Cert Verification

SSL verification for HTTPS requests is enabled by default.

To use a self-signed certificate pass the certificate file or directory path using the ca_bundle_path option: `ca_bundle_path: '/path/to/certfile'`.
To ignore verifying the SSL certificate pass `verify_ssl: False`



