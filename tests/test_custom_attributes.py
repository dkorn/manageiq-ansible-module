# -*- coding: utf-8 -*-
import pytest
from mock import Mock

from ansible.module_utils.basic import AnsibleModule

from miqclient.api import API
import manageiq_custom_attributes


MANAGEIQ_HOSTNAME = "http://miq.example.com"
PROVIDER_NAME = "openshift01"
PROVIDER_HOSTNAME = "os01.example.com"
PROVIDER_ID = 266
EXISTING_CA = {"id": 1, "name": "ca1", "value": "value 1"}
NEW_CA = {"id": 2, "name": "ca2", "value": "value 2"}
UPDATED_CA_VALUE = "new value"


GET_RETURN_VALUES = {
    'no_cas': {},
    'ca_exist': {
        "custom_attributes": [{
            "href": "{miq_hostname}/api/providers/{provider_id}/custom_attributes/{ca_id}".format(miq_hostname=MANAGEIQ_HOSTNAME, provider_id=PROVIDER_ID, ca_id=EXISTING_CA['id']),
            "id": EXISTING_CA['id'],
            "section": "metadata",
            "name": EXISTING_CA['name'],
            "value": EXISTING_CA['value'],
            "resource_type": "ExtManagementSystem",
            "resource_id": PROVIDER_ID,
            "source": "EVM",
            "serialized_value": EXISTING_CA['value']
        }]
    }
}
POST_RETURN_VALUES = {
    'added_ca': {
        'results': [{
            "resource_id": PROVIDER_ID,
            "section": "metadata",
            "name": NEW_CA['name'],
            "id": NEW_CA['id'],
            "serialized_value": NEW_CA['value'],
            "value": NEW_CA['value'],
            "resource_type": "ExtManagementSystem",
            "source": "EVM"
        }]
    },
    'updated_ca': {
        'results': [{
            "resource_id": PROVIDER_ID,
            "section": "metadata",
            "name": EXISTING_CA['name'],
            "id": EXISTING_CA['id'],
            "serialized_value": UPDATED_CA_VALUE,
            "value": UPDATED_CA_VALUE,
            "resource_type": "ExtManagementSystem",
            "source": "EVM"
        }]
    }
}


class MiqAPIMock(Mock):
    def __init__(self, *args, **kwargs):
        super(MiqAPIMock, self).__init__(*args, **kwargs)
        self.next_id = 1

    def get_new_id(self, action):
        if action != 'edit':
            self.next_id = self.next_id + 1
        return self.next_id

    def post(self, url, action, resources):
        """
        Mock the post function to mirror the given resources
        """
        posted_cas = []
        for ca in resources:
            posted_cas.append({
                "resource_id": PROVIDER_ID,
                "section": ca['section'] if 'section' in ca else "metadata",
                "name": ca['name'],
                "id": self.get_new_id(action),
                "serialized_value": ca['value'],
                "value": ca['value'],
                "resource_type": "ExtManagementSystem",
                "source": "EVM"
                })
        return {'results': posted_cas}


@pytest.fixture(autouse=True)
def miq_api_class(monkeypatch):
    miq_api_class = MiqAPIMock(spec=API)
    monkeypatch.setattr("manageiq_custom_attributes.MiqApi", miq_api_class)
    yield miq_api_class


@pytest.fixture
def the_provider():
    the_provider = Mock()
    the_provider.name = PROVIDER_NAME
    yield the_provider


@pytest.fixture
def miq_ansible_module():
    miq_ansible_module = Mock(spec=AnsibleModule)
    yield miq_ansible_module


class AnsibleModuleFailed(Exception):
    pass


@pytest.fixture()
def miq(miq_api_class, miq_ansible_module, the_provider):

    def fail(msg):
        raise AnsibleModuleFailed(msg)

    miq_ansible_module.fail_json = fail
    miq = manageiq_custom_attributes.ManageIQCustomAttributes(
        miq_ansible_module, MANAGEIQ_HOSTNAME, "The username", "The password",
        verify_ssl=False, ca_bundle_path=None)

    miq_api_class.return_value.collections.providers = [the_provider]

    yield miq


def test_get_entity_custom_attributes(miq, miq_api_class):
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['ca_exist']
    provider_cas = miq.get_entity_custom_attributes('provider', PROVIDER_ID)
    assert provider_cas == GET_RETURN_VALUES['ca_exist']['custom_attributes']


def test_add_custom_attributes_if_none_exist(miq, miq_api_class):
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['no_cas']

    new_ca = [{'name': NEW_CA['name'], 'value': NEW_CA['value']}]
    result = miq.add_or_update_custom_attributes('provider', PROVIDER_NAME, new_ca)
    assert result == {
        'changed': True,
        'msg': "Successfully set the custom attributes to {entity_name} {entity_type}".format(entity_name=PROVIDER_NAME, entity_type='provider'),
        'updates': {
            'Added': POST_RETURN_VALUES['added_ca']['results'],
            'Updated': []
        }
    }


def test_update_existing_custom_attribute(miq, miq_api_class):
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['ca_exist']

    updated_ca = [{'name': EXISTING_CA['name'], 'value': UPDATED_CA_VALUE}]
    result = miq.add_or_update_custom_attributes('provider', PROVIDER_NAME, updated_ca)
    assert result == {
        'changed': True,
        'msg': "Successfully set the custom attributes to {entity_name} {entity_type}".format(entity_name=PROVIDER_NAME, entity_type='provider'),
        'updates': {
            'Added': [],
            'Updated': POST_RETURN_VALUES['updated_ca']['results']
        }
    }


def delete_existing_custom_attribute(miq, miq_api_class):
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['ca_exist']

    deleted_ca = [{'name': EXISTING_CA['name'], 'value': EXISTING_CA['value']}]
    result = miq.delete_custom_attributes('provider', PROVIDER_NAME, deleted_ca)
    assert result == {
        'changed': True,
        'msg': "Successfully deleted the following custom attributes from {provider_name} provider: {deleted}".format(
            provider_name=PROVIDER_NAME, deleted=POST_RETURN_VALUES['added_ca']['results'])
    }
