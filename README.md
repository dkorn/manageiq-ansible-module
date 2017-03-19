# manageiq-ansible-module

[![travis image][]][travis status]

Ansible modules automating various operations and use cases of ManageIQ.

[travis image]: https://api.travis-ci.org/dkorn/manageiq-ansible-module.svg?branch=master
[travis status]: https://travis-ci.org/dkorn/manageiq-ansible-module/branches

## Prerequisites

ManageIQ Python API Client package [manageiq-client] (https://github.com/ManageIQ/manageiq-api-client-python/).

    $ pip install manageiq-client


## Getting Started

    $ pip install -r requirements.txt
    
To try the modules copy and edit the relevant example playbook and execute:

    $ ansible-playbook examples/EDITED_PLAYBOOK.yml -M library/
   


## The Modules

### manageiq_provider module

The `manageiq_provider` module currently supports adding, updating and deleting OpenShift, Amazon EC2 and Hawkular Datawarehouse providers to manageiq.  
Example playbooks [add_openshift_provider.yml](add_openshift_provider.yml), [add_amazon_provider.yml](add_amazon_provider.yml) and [add_hawkular_datawarehouse_provider.yml](add_hawkular_datawarehouse_provider.yml) are provided.
To update an existing provider pass the changed values together with the required parameters. To delete a provider change `state=absent`.  
SSL verification for HTTPS requests between ManageIQ and the provider is enabled by default. To ignore pass `provider_verify_ssl: false`.
To use a self-signed certificate pass: `provider_ca_path: '/path/to/certfile'`.  
After addition or update, each endpoint authentication is validated, a process which can take up to 50 seconds before timeout.
If all authentications are valid the provider's inventory is refreshed.

### manageiq_user module

The `manageiq_user` module supports adding, updating and deleting users in manageiq.  
Example playbook [create_user.yml](create_user.yml) is provided.  
To update an existing user pass the changed values together with the required parameters. To delete a user change `state=absent`.

### manageiq_policy_assignment module

The `manageiq_policy_assignment` module currently supports assigning and unassigning Policies and Policy Profiles on resources in manageiq.  
An example playbook [assign_policy.yml](assign_policy.yml) is provided.  
To unassign a policy/policy profile on a resource change `state=absent`.

### manageiq_custom_attributes module

The `manageiq_custom_attributes` module supports adding, updating and deleting custom attributes on resources in ManageIQ.
Currently the only resources (entities) that supports custom attributes are vms and providers.  
An example playbook [add_custom_attributes.yml](add_custom_attributes.yml) is provided.  
To delete a custom attributes change `state=absent`.  
It is possible to add a date type custom attributes by specifying `field_type: "Date"` and passing it in the following fromat:
`yyyy-mm-dd`



## Using Environment Variables

It is possible to set the following environment variables, and remove them from playbook options.

    $ export MIQ_URL=http://localhost:3000
    $ export MIQ_USERNAME=admin
    $ export MIQ_PASSWORD=******
    


## SSL Cert Verification

SSL verification for HTTPS requests is enabled by default.

To use a self-signed certificate pass the certificate file or directory path using the ca_bundle_path option: `ca_bundle_path: '/path/to/certfile'`.
To ignore verifying the SSL certificate pass `miq_verify_ssl: False`
