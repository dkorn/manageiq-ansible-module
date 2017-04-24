# -*- coding: utf-8 -*-
import pytest
from mock import Mock

from ansible.module_utils.basic import AnsibleModule

from manageiq_client.api import ManageIQClient
import manageiq_alert


MANAGEIQ_HOSTNAME = "http://miq.example.com"
DESCRIPTION = "Test Alert 01"
ALERT_ID = "17"
EXPRESSION = {
    "eval_method": "dwh_generic",
    "mode": "internal",
    "options": {}
}
MIQ_ENTITY = "container_node"
OPTIONS = {
    "notifications": {
        "delay_next_evaluation": 600,
        "evm_event": {}
    }
}
UPDATED_OPTIONS = {
    "notifications": {
        "delay_next_evaluation": 60,
        "evm_event": {}
    }
}
ENABLED = True

GET_RETURN_VALUES = {
    "alert_definitions_not_exist": {
        "resources": []
    },
    "alert_definitions_exist": {
        'resources': [{
            "id": ALERT_ID,
            "description": DESCRIPTION,
            "created_on": "2017-04-04T07:42:51Z",
            "updated_on": "2017-04-04T07:42:51Z",
            "expression": {
                "exp": {
                    "eval_method": "dwh_generic",
                    "mode": "internal",
                    "options": {}
                },
                "context_type": None
            },
            "options": {
                "notifications": {
                    "delay_next_evaluation": 600,
                    "evm_event": {}
                }
            },
            "db": "ContainerNode",
            "enabled": True
        }]
    }
}

POST_RETURN_VALUES = {
    "created_alert": {
        "results": {
            "id": ALERT_ID,
            "guid": "4ebca44e-190a-11e7-be91-68f728d88921",
            "description": DESCRIPTION,
            "created_on": "2017-04-04T07:42:51Z",
            "updated_on": "2017-04-04T07:42:51Z",
            "options": {
                "notifications": {
                    "delay_next_evaluation": 600,
                    "evm_event": {}
                }
            },
            "db": "ContainerNode",
            "expression": {
                "exp": {
                    "eval_method": "dwh_generic",
                    "mode": "internal",
                    "options": {}
                },
                "context_type": None
            },
            "enabled": True
        }
    },
    'updated_alert': {
        "id": ALERT_ID,
        "guid": "4ebca44e-190a-11e7-be91-68f728d88921",
        "description": DESCRIPTION,
        "created_on": "2017-04-04T07:42:51Z",
        "updated_on": "2017-04-04T07:45:51Z",
        "options": {
          "notifications": {
            "delay_next_evaluation": 60,
            "evm_event": {}
          }
        },
        "db": "ContainerNode",
        "expression": {
          "exp": {
            "eval_method": "dwh_generic",
            "mode": "internal",
            "options": {}
          },
          "context_type": None
        },
        "enabled": True
    },
    'deleted_alert': {
        'success': 'true',
        'message': "alert definitions id: {id} deleting".format(id=ALERT_ID),
    }
}


@pytest.fixture(autouse=True)
def miq_api_class(monkeypatch):
    miq_api_class = Mock(spec=ManageIQClient)
    monkeypatch.setattr("manageiq_alert.MiqApi", miq_api_class)
    yield miq_api_class


@pytest.fixture
def miq_ansible_module():
    miq_ansible_module = Mock(spec=AnsibleModule)
    yield miq_ansible_module


class AnsibleModuleFailed(Exception):
    pass


@pytest.fixture()
def miq(miq_api_class, miq_ansible_module):

    def fail(msg):
        raise AnsibleModuleFailed(msg)

    miq_ansible_module.fail_json = fail
    miq = manageiq_alert.ManageIQAlert(
        miq_ansible_module, MANAGEIQ_HOSTNAME, "The username", "The password",
        False, None)
    yield miq


def test_create_alert_if_not_exist(miq, miq_api_class):
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['alert_definitions_not_exist']
    miq_api_class.return_value.post.return_value = POST_RETURN_VALUES['created_alert']

    result = miq.create_or_update_alert(DESCRIPTION, EXPRESSION, MIQ_ENTITY, OPTIONS, ENABLED)
    assert result == {
        'changed': True,
        'msg': "Successfully created alert {description}: {alert_details}".format(description=DESCRIPTION, alert_details=POST_RETURN_VALUES['created_alert']['results'])
    }
    miq.client.post.assert_called_once_with(
        '{hostname}/api/alert_definitions/'.format(hostname=MANAGEIQ_HOSTNAME),
        action='create',
        resource={'description': DESCRIPTION, 'expression': EXPRESSION, 'db': 'ContainerNode', 'options': OPTIONS, 'enabled': ENABLED}
    )


def test_update_alert_options(miq, miq_api_class):
    miq_api_class.return_value.get.side_effect = [
        GET_RETURN_VALUES['alert_definitions_exist'],
        GET_RETURN_VALUES['alert_definitions_exist']['resources'][0]
    ]
    miq_api_class.return_value.post.return_value = POST_RETURN_VALUES['updated_alert']

    result = miq.create_or_update_alert(DESCRIPTION, EXPRESSION, MIQ_ENTITY, UPDATED_OPTIONS, ENABLED)
    assert result == {
        'changed': True,
        'msg': "Successfully updated alert {description}: {alert_details}".format(description=DESCRIPTION, alert_details=POST_RETURN_VALUES['updated_alert'])
    }


def test_delete_existing_alert(miq, miq_api_class):
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['alert_definitions_exist']
    miq_api_class.return_value.post.return_value = POST_RETURN_VALUES['deleted_alert']

    result = miq.delete_alert(DESCRIPTION)
    assert result == {
        'changed': True,
        'msg': "alert definitions id: {id} deleting".format(id=ALERT_ID)
    }
    miq.client.post.assert_called_once_with(
        '{hostname}/api/alert_definitions/{id}'.format(hostname=MANAGEIQ_HOSTNAME, id=ALERT_ID),
        action='delete')


def test_delete_alert_not_exist(miq, miq_api_class):
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['alert_definitions_not_exist']

    result = miq.delete_alert(DESCRIPTION)
    assert result == {
        'changed': False,
        'msg': 'Alert {description} does not exist in manageiq'.format(description=DESCRIPTION)
    }


def test_create_alert_with_same_attributes(miq, miq_api_class):
    miq_api_class.return_value.get.side_effect = [
        GET_RETURN_VALUES['alert_definitions_exist'],
        GET_RETURN_VALUES['alert_definitions_exist']['resources'][0]
    ]

    result = miq.create_or_update_alert(DESCRIPTION, EXPRESSION, MIQ_ENTITY, OPTIONS, ENABLED)
    assert result == {
        'changed': False,
        'msg': 'Alert {description} already exist, no need for updates'.format(description=DESCRIPTION)
    }
