# OBSOLETE — Upstreaming into Ansible itself

This repository is **no longer maintained**.
Instead, most of this functionality was upsteamed into <https://github.com/ansible/ansible>.
If you want to contribute, please send PRs to Ansible itself (and we'll help review).

As a result of the upstream reviews, the new modules in Ansible have different interface, so you'll need to rewrite your playbooks.
There is no clear plan for smooth transition or mixed usage; see https://github.com/dkorn/manageiq-ansible-module/issues/85 for the main differences.
Don't hesitate to ask questions - on that issue, on <http://talk.manageiq.org/> and chat <https://gitter.im/ManageIQ/api>.

----


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

To view a module documentation execute:

    $ ansible-doc --module-path=library/ MODULE_NAME.py
   


## The Modules

### manageiq_provider module

**Upstream replacement:** https://docs.ansible.com/ansible/devel/module_docs/manageiq_provider_module.html

The `manageiq_provider` module currently supports adding, updating and deleting OpenShift, Amazon EC2 and Hawkular Datawarehouse providers to manageiq.  
Example playbooks [add_openshift_provider.yml](examples/add_openshift_provider.yml), [add_amazon_provider.yml](examples/add_amazon_provider.yml) and [add_hawkular_datawarehouse_provider.yml](examples/add_hawkular_datawarehouse_provider.yml) are provided.
To update an existing provider pass the changed values together with the required parameters. To delete a provider change `state=absent`.  
SSL verification for HTTPS requests between ManageIQ and the provider is enabled by default. To ignore pass `provider_verify_ssl: false`.
To use a self-signed certificate pass: `provider_ca_path: '/path/to/certfile'`. To remove a previously defined ca pass `""` (empty string). In case the parameter is passed with null or omitted the `certificate_authority` field will be left unmodified (unset on creation). `provider_ca_path` must be omitted with ManageIQ Euwe / CFME 5.7 or earlier releases.
After addition or update, each endpoint authentication is validated, a process which can take up to 50 seconds before timeout.
If all authentications are valid the provider's inventory is refreshed.

### manageiq_user module

**Upstream replacement:** https://docs.ansible.com/ansible/devel/module_docs/manageiq_user_module.html

The `manageiq_user` module supports adding, updating and deleting users in manageiq.  
Example playbook [create_user.yml](examples/create_user.yml) is provided.  
To update an existing user pass the changed values together with the required parameters. To delete a user change `state=absent`.

### manageiq_policy_assignment module

**Upstream replacement:** https://docs.ansible.com/ansible/devel/module_docs/manageiq_policies_module.html

The `manageiq_policy_assignment` module currently supports assigning and unassigning Policies and Policy Profiles on resources in manageiq.  
An example playbook [assign_policy.yml](examples/assign_policy.yml) is provided.  
To unassign a policy/policy profile from a resource change `state=absent`.

### manageiq_custom_attributes module

The `manageiq_custom_attributes` module supports adding, updating and deleting custom attributes on resources in ManageIQ.
Currently the only resources (entities) that supports custom attributes are vms and providers.  
An example playbook [add_custom_attributes.yml](examples/add_custom_attributes.yml) is provided.  
To delete a custom attributes change `state=absent`.  
It is possible to add a date type custom attributes by specifying `field_type: "Date"` and passing it in the following fromat:
`yyyy-mm-dd`

### manageiq_tag_assignment module

**Upstream replacement:** https://docs.ansible.com/ansible/devel/module_docs/manageiq_tags_module.html

The `manageiq_tag_assignment` module currently supports assigning and unassigning tags on resources in manageiq.  
List of supprted entities for tag assignment can be found in the [ManageIQ REST API docs](http://manageiq.org/docs/reference/latest/api/reference/tagging)  
Each assigned tag must be a part of a unique category.  
An example playbook [assign_tag.yml](examples/assign_tag.yml) is provided.  
To unassign a tag from a resource change `state=absent`.

### manageiq_alert module

**Upstream replacements (split into 2 modules):** https://docs.ansible.com/ansible/devel/module_docs/manageiq_alerts_module.html, https://docs.ansible.com/ansible/devel/module_docs/manageiq_alert_profiles_module.html

The `manageiq_alert` module supports adding, updating and deleting alerts in manageiq.  
Example playbook [create_alert.yml](examples/create_alert.yml) is provided.  
To update an existing alert pass the changed values together with the required parameters. To delete an alert change `state=absent`.
Alert expression in ManageIQ can have one of two types: `miq_expression` (`MiqExpression`) or `hash`. By default the expression type is `miq_expression`, to change the type use the `expression_type` field.
The following ManageIQ entities supports alerts: container_node, vm, host, storage, cluster, ems, miq_server and middleware_server.



## Using Environment Variables

It is possible to set the following environment variables, and remove them from playbook options.

    $ export MIQ_URL=http://localhost:3000
    $ export MIQ_USERNAME=admin
    $ export MIQ_PASSWORD=******
    


## SSL Cert Verification

SSL verification for HTTPS requests is enabled by default.

To use a self-signed certificate pass the certificate file or directory path using the ca_bundle_path option: `ca_bundle_path: '/path/to/certfile'`.
To ignore verifying the SSL certificate pass `miq_verify_ssl: False`
    


## Licence
GNU General Public License V3, same as Ansible.
Click on the [Link](COPYING) to see the full text.
