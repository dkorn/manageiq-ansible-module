#!/usr/bin/python

import os
from ansible.module_utils.basic import *
from manageiq_client.api import ManageIQClient as MiqApi


DOCUMENTATION = '''
---
module: manageiq_policy
description: The manageiq_policy_assignment module currently supports assigning and unassigning Policies and Policy Profiles on resources in ManageIQ
short_description: assign and unassign policies and policy profiles on resources in ManageIQ
requirements: [ ManageIQ/manageiq-api-client-python ]
author: Daniel Korn (@dkorn)
options:
  miq_url:
    description:
      - the manageiq environment url
    default: MIQ_URL env var if set. otherwise, it is required to pass it
  miq_username:
    description:
      - manageiq username
    default: MIQ_USERNAME env var if set. otherwise, it is required to pass it
  miq_password:
    description:
      - manageiq password
    default: MIQ_PASSWORD env var if set. otherwise, it is required to pass it
  entity:
    description:
      - the entity referred to
    required: true
    choices: ['policy', 'policy profile']
  entity_name:
    description:
      - the entity name in manageiq
    required: true
    default: null
  resource:
    description:
      - the relevant resource type in manageiq
    required: true
    choices: ['provider', 'host', 'vm', 'container node', 'pod', 'replicator', 'container image']
    default: null
  resource_name:
    description:
      - the relevant resource name in manageiq
    required: true
    default: null
  state:
    description:
      - On present, it will assign the entity on the resource, if not already assigned
      - On absent, it will unassign the entity from the resource
    required: false
    choices: ['present', 'absent']
    default: 'present'
  miq_verify_ssl:
    description:
      - whether SSL certificates should be verified for HTTPS requests
    required: false
    default: True
    choices: ['True', 'False']
  ca_bundle_path:
    description:
      - the path to a CA_BUNDLE file or directory with certificates
    required: false
    default: null
'''

EXAMPLES = '''
# Assign policy to a provider in ManageIQ
  manageiq_policy_assignment:
    entity: 'policy'
    entity_name: 'example policy'
    resource_name: 'OpenShift01'
    resource: 'provider'
    state: 'present'
    miq_url: 'http://localhost:3000'
    miq_username: 'admin'
    miq_password: '******'
'''


class ManageIQ(object):
    """ ManageIQ object to execute policy assignments in manageiq

    url            - manageiq environment url
    user           - the username in manageiq
    password       - the user password in manageiq
    miq_verify_ssl - whether SSL certificates should be verified for HTTPS requests
    ca_bundle_path - the path to a CA_BUNDLE file or directory with certificates
    """

    manageiq_entities = {
        'policy': 'policies', 'policy profile': 'policy_profiles',
        'provider': 'providers', 'host': 'hosts', 'vm': 'vms',
        'container node': 'container_nodes', 'pod': 'container_groups',
        'replicator': 'container_replicators',
        'container image': 'container_images'
    }
    policy_actions = {
        'present': 'assign', 'absent': 'unassign'
    }

    def __init__(self, module, url, user, password, miq_verify_ssl, ca_bundle_path):
        self.module        = module
        self.api_url       = url + '/api'
        self.user          = user
        self.password      = password
        self.client        = MiqApi(self.api_url, (self.user, self.password), verify_ssl=miq_verify_ssl, ca_bundle_path=ca_bundle_path)
        self.changed       = False

    def find_entity_by_name(self, entity_type, entity_name):
        """ Searches the entity name in ManageIQ.

        Returns:
            the entity id if it exists in manageiq, None otherwise.
        """
        entities_list = getattr(self.client.collections, entity_type)
        return next((e.id for e in entities_list if e.name == entity_name), None)

    def query_resource_policies_or_profiles(self, entity_type, resource_type, resource_id):
        """ Returns the policies or policy profiles assigned to the resource.
        """
        try:
            url = '{api_url}/{resource_type}/{resource_id}/{entity_type}?expand=resources'.format(api_url=self.api_url, resource_type=resource_type, resource_id=resource_id, entity_type=entity_type)
            result = self.client.get(url)
            return result.get('resources', [])
        except Exception as e:
            self.module.fail_json(msg="Failed to query resource {entity_type}: {error}".format(entity_type=entity_type, error=e))

    def entity_assigned(self, entity_type, entity_id, resource_type, resource_id):
        """Return True if the action is needed on the resource, False otherwise.
        """
        assigned_entities = self.query_resource_policies_or_profiles(entity_type, resource_type, resource_id)
        return any(ae['id'] == entity_id for ae in assigned_entities)

    def execute_action(self, entity_type, entity_id, resource_type, resource_id, action):
        """Executes the action for the relevant entity on the resource.

        Returns:
            Whether or not a change took place and a message describing the
            operation executed.
        """
        try:
            href = '{api_url}/{entity_type}/{entity_id}'.format(api_url=self.api_url, entity_type=entity_type, entity_id=entity_id)
            url = '{api_url}/{resource_type}/{resource_id}/{entity_type}'.format(api_url=self.api_url, resource_type=resource_type, resource_id=resource_id, entity_type=entity_type)
            result = self.client.post(url, action=action, resource={'href': href})
            if result['results'][0]['success']:
                self.changed = True
                return dict(
                    changed=self.changed,
                    msg=result['results'][0]['message']
                )
            else:
                self.module.fail_json(msg="Failed to {action}: {fail_message}".format(action=action, entity=entity, fail_message=result['results'][0]['message']))
        except Exception as e:
            self.module.fail_json(msg="Failed to {action}: {error}".format(action=action, entity=entity, error=e))

    def assign_or_unassign_entity(self, entity, entity_name, resource, resource_name, state):
        """ Assign or unassign the entity on the manageiq resource.

        Returns:
            Whether or not a change took place and a message describing the
            operation executed.
        """
        entity_type = self.manageiq_entities[entity]
        resource_type = self.manageiq_entities[resource]
        entity_id = self.find_entity_by_name(entity_type, entity_name)
        if not entity_id:  # entity doesn't exist
            self.module.fail_json(
                msg="Failed to {action} {entity}: {entity_name} does not exist in manageiq".format(action=ManageIQ.policy_actions[state], entity=entity, entity_name=entity_name))

        resource_id = self.find_entity_by_name(resource_type, resource_name)
        if not resource_id:  # resource doesn't exist
            self.module.fail_json(
                msg="Failed to {action} {entity}: {resource_name} {resource} does not exist in manageiq".format(action=ManageIQ.policy_actions[state], entity=entity, resource_name=resource_name, resource=resource))

        assigned = self.entity_assigned(entity_type, entity_id, resource_type, resource_id)
        if assigned and state == 'absent':
            return self.execute_action(entity_type, entity_id, resource_type, resource_id, 'unassign')
        if (not assigned) and state == 'present':
            return self.execute_action(entity_type, entity_id, resource_type, resource_id, 'assign')

        #  Default case is that there's nothing to change
        return dict(
            changed=self.changed,
            msg="{entity_name} {entity} already {action}ed".format(entity_name=entity_name, entity=entity, action=ManageIQ.policy_actions[state]))


def main():
    module = AnsibleModule(
        argument_spec=dict(
            entity=dict(required=True, type='str',
                        choices=['policy', 'policy profile']),
            entity_name=dict(required=True, type='str'),
            resource_name=dict(required=True, type='str'),
            resource=dict(required=True, type='str',
                          choices=['provider', 'host', 'vm', 'container node',
                                   'pod', 'replicator', 'container image']),
            state=dict(required=True, type='str',
                       choices=['present', 'absent']),
            miq_url=dict(default=os.environ.get('MIQ_URL', None)),
            miq_username=dict(default=os.environ.get('MIQ_USERNAME', None)),
            miq_password=dict(default=os.environ.get('MIQ_PASSWORD', None), no_log=True),
            miq_verify_ssl=dict(require=False, type='bool', default=True),
            ca_bundle_path=dict(required=False, type='str', defualt=None),
        )
    )

    for arg in ['miq_url', 'miq_username', 'miq_password']:
        if module.params[arg] in (None, ''):
            module.fail_json(msg="missing required argument: {}".format(arg))

    miq_url        = module.params['miq_url']
    miq_username   = module.params['miq_username']
    miq_password   = module.params['miq_password']
    entity         = module.params['entity']
    entity_name    = module.params['entity_name']
    resource       = module.params['resource']
    resource_name  = module.params['resource_name']
    state          = module.params['state']
    miq_verify_ssl = module.params['miq_verify_ssl']
    ca_bundle_path = module.params['ca_bundle_path']

    manageiq = ManageIQ(module, miq_url, miq_username, miq_password, miq_verify_ssl, ca_bundle_path)
    res_args = manageiq.assign_or_unassign_entity(entity, entity_name, resource, resource_name, state)

    module.exit_json(**res_args)


if __name__ == "__main__":
    main()
