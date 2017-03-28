#!/usr/bin/python


DOCUMENTATION = '''
---
module: manageiq_alert
description: The manageiq_alert module supports adding, updating and deleting alert definitions in ManageIQ.
short_description: management of alerts in ManageIQ
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
  description:
    description:
      - the alert definition description in manageiq
    required: false
    default: null
  db:
    description:
      - the db entry of the entity to base the alert on in manageiq
    required: false
    default: null
  expression:
    description:
      - the expression to evaluate
    required: false
    default: null
  options:
    description:
      - Additional alert options, including the notification type and frequency
    required: false
    default: null
  enabled:
    description:
      - whether the alert is active or not
    required: false
    default: true
  state:
    description:
      - the state of the alert definition
      - On present, it will create the alert if it does not exist, or update it
        if the associated data is different
      - On absent, it will delete the alert if it exists
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
# Create a new alert in ManageIQ
  manageiq_alert:
    description: Test Alert 01
    options:
      notifications:
        delay_next_evaluation: 60
        evm_event: {}
    db: ContainerNode
    expression:
      eval_method: dwh_generic
      mode: internal
    enabled: true
    state: present
    miq_url: 'http://localhost:3000'
    miq_username: 'admin'
    miq_password: '******'
    miq_verify_ssl: False
'''

import os
from manageiq_client.api import ManageIQClient as MiqApi


class ManageIQAlert(object):
    """ ManageIQ object to execute alert definitions management operations in manageiq

    url            - manageiq environment url
    user           - the username in manageiq
    password       - the user password in manageiq
    miq_verify_ssl - whether SSL certificates should be verified for HTTPS requests
    ca_bundle_path - the path to a CA_BUNDLE file or directory with certificates
    """

    def __init__(self, module, url, user, password, miq_verify_ssl, ca_bundle_path):
        self.module        = module
        self.api_url       = url + '/api'
        self.user          = user
        self.password      = password
        self.client        = MiqApi(self.api_url, (self.user, self.password), verify_ssl=miq_verify_ssl, ca_bundle_path=ca_bundle_path)
        self.changed       = False

    def find_alert_by_description(self, description):
        """ Searches the alert description in ManageIQ.

        Returns:
            the alert id if it exists in manageiq, None otherwise.
        """
        try:
            response = self.client.get('{api_url}/alert_definitions?expand=resources'.format(api_url=self.api_url))
        except Exception as e:
            self.module.fail_json(msg="Failed to query alerts: {error}".format(error=e))
        alerts = response.get('resources', [])
        return next((alert['id'] for alert in alerts if alert['description'] == description), None)

    def delete_alert(self, description):
        """Deletes the alert from manageiq.

        Returns:
            a short message describing the operation executed.
        """
        alert_id = self.find_alert_by_description(description)
        if not alert_id:  # alert doesn't exist
            return dict(
                changed=self.changed,
                msg="Alert {description} does not exist in manageiq".format(description=description))
        try:
            url = '{api_url}/alert_definitions/{alert_id}'.format(api_url=self.api_url, alert_id=alert_id)
            result = self.client.post(url, action='delete')
        except Exception as e:
            self.module.fail_json(msg="Failed to delete alert {description}: {error}".format(description=description, error=e))
        self.changed = True
        return dict(changed=self.changed, msg=result['message'])

    def alert_update_required(self, alert_id, description, expression, db, options, enabled):
        """ Returns true if the expression, db, options, or enabled passed for
            the alert differ from the alert's existing ones, False otherwise.
        """
        url = "{api_url}/alert_definitions/{alert_id}".format(api_url=self.api_url, alert_id=alert_id)
        try:
            result = self.client.get(url)
        except Exception as e:
            self.module.fail_json(msg="Failed to get alert {description} details. Error: {error}".format(description=description, error=e))

        # remove None values from expression and options dicts
        current_expression = dict((k, v) for k, v in result['expression']['exp'].items() if v is not None)
        current_options = dict((k, v) for k, v in result['options'].items() if v is not None)

        attributes_tuples = [(current_expression, expression), (result['db'], db), (current_options, options), (result['enabled'], enabled)]
        for tup in attributes_tuples:
            if tup[1] is not None and tup[0] != tup[1]:
                return True
        return False

    def update_alert_if_required(self, alert_id, description, expression, db, options, enabled):
        """Updates the alert in manageiq.

        Returns:
            Whether or not a change took place and a message describing the
            operation executed.
        """
        if not self.alert_update_required(alert_id, description, expression, db, options, enabled):
            return dict(
                changed=self.changed,
                msg="Alert {description} already exist, no need for updates".format(description=description))

        url = '{api_url}/alert_definitions/{alert_id}'.format(api_url=self.api_url, alert_id=alert_id)
        resource = {'description': description, 'expression': expression, 'db': db,
                    'options': options, 'enabled': enabled}
        try:
            result = self.client.post(url, action='edit', resource=resource)
        except Exception as e:
            self.module.fail_json(msg="Failed to update alert {description}: {error}".format(description=description, error=e))
        self.changed = True
        return dict(
            changed=self.changed,
            msg="Successfully updated alert {description}: {alert_details}".format(description=description, alert_details=result))

    def create_alert(self, description, expression, db, options, enabled):
        """Creates the alert in manageiq.

        Returns:
            Whether or not a change took place and a message describing the
            operation executed.
        """
        url = '{api_url}/alert_definitions/'.format(api_url=self.api_url)
        resource = {'description': description, 'expression': expression,
                    'db': db, 'options': options, 'enabled': enabled}
        try:
            result = self.client.post(url, action='create', resource=resource)
            self.changed = True
            return dict(
                changed=self.changed,
                msg="Successfully created alert {description}: {alert_details}".format(description=description, alert_details=result['results']))
        except Exception as e:
            self.module.fail_json(msg="Failed to create alert {description}: {error}".format(description=description, error=e))

    def create_or_update_alert(self, description, expression, db, options, enabled):
        """ Create or update an alert in manageiq.

        Returns:
            Whether or not a change took place and a message describing the
            operation executed.
        """
        alert_id = self.find_alert_by_description(description)
        if alert_id:  # alert already exist
            return self.update_alert_if_required(alert_id, description, expression, db, options, enabled)
        else:
            return self.create_alert(description, expression, db, options, enabled)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            description=dict(required=False, type='str'),
            db=dict(required=False, type='str'),
            options=dict(required=False, type='dict'),
            expression=dict(required=False, type='dict'),
            enabled=dict(require=False, type='bool', default=True),
            state=dict(required=True, type='str',
                       choices=['present', 'absent']),
            miq_url=dict(default=os.environ.get('MIQ_URL', None)),
            miq_username=dict(default=os.environ.get('MIQ_USERNAME', None)),
            miq_password=dict(default=os.environ.get('MIQ_PASSWORD', None), no_log=True),
            miq_verify_ssl=dict(require=False, type='bool', default=True),
            ca_bundle_path=dict(required=False, type='str', defualt=None)
        ),
        required_if=[
            ('state', 'present', ['description', 'expression', 'db', 'options'])
        ],
    )

    for arg in ['miq_url', 'miq_username', 'miq_password']:
        if module.params[arg] in (None, ''):
            module.fail_json(msg="missing required argument: {}".format(arg))

    miq_url        = module.params['miq_url']
    miq_username   = module.params['miq_username']
    miq_password   = module.params['miq_password']
    miq_verify_ssl = module.params['miq_verify_ssl']
    ca_bundle_path = module.params['ca_bundle_path']
    description    = module.params['description']
    db             = module.params['db']
    options        = module.params['options']
    expression     = module.params['expression']
    enabled        = module.params['enabled']
    state          = module.params['state']

    manageiq = ManageIQAlert(module, miq_url, miq_username, miq_password, miq_verify_ssl, ca_bundle_path)
    if state == "present":
        res_args = manageiq.create_or_update_alert(description, expression, db,
                                                   options, enabled)
    if state == "absent":
        res_args = manageiq.delete_alert(description)

    module.exit_json(**res_args)


# Import module bits
from ansible.module_utils.basic import *
if __name__ == "__main__":
    main()
