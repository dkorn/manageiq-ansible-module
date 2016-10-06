# -*- coding: utf-8 -*-
import pytest
from mock import Mock

from ansible.module_utils.basic import AnsibleModule

from miqclient.api import API
import manageiq_provider


PROVIDER_NAME = "Provider name 1 with some unicode characters «ταБЬℓσ»"
PROVIDER_HOSTNAME = "some-provider-hostname.tld"
PROVIDER_TOKEN = "THE_PROVIDER_TOKEN"
PROVIDER_PORT = 8443
PROVIDER_ID = 134
HAWKULAR_HOSTNAME = "some-hawkular-hostname.tld"
HAWKULAR_PORT = 443
MANAGEIQ_HOSTNAME = "http://themanageiq.tld"


@pytest.fixture(autouse=True)
def miq_api_class(monkeypatch):
    miq_api_class = Mock(spec=API)
    monkeypatch.setattr("manageiq_provider.MiqApi", miq_api_class)
    yield miq_api_class


@pytest.fixture
def the_provider():
    the_provider = Mock()
    the_provider.name = PROVIDER_NAME
    yield the_provider


@pytest.fixture
def the_zone():
    the_zone = Mock()
    the_zone.name = "default"
    the_zone.id = 1
    yield the_zone


@pytest.fixture
def miq_ansible_module():
    miq_ansible_module = Mock(spec=AnsibleModule)
    yield miq_ansible_module


@pytest.fixture
def endpoints(miq):
    endpoints = [
        miq.generate_endpoint("default", PROVIDER_HOSTNAME, PROVIDER_PORT,
                              "bearer", PROVIDER_TOKEN),
        miq.generate_endpoint("hawkular", HAWKULAR_HOSTNAME, HAWKULAR_PORT,
                              "hawkular", PROVIDER_TOKEN)]
    yield endpoints


class AnsibleModuleFailed(Exception):
    pass


@pytest.fixture()
def miq(miq_api_class, miq_ansible_module, the_provider, the_zone):
    miq_ansible_module.params = {'metrics': True}

    def fail(msg):
        raise AnsibleModuleFailed(msg)

    miq_ansible_module.fail_json = fail
    miq = manageiq_provider.ManageIQ(miq_ansible_module, MANAGEIQ_HOSTNAME,
                                     "The username", "The password",
                                     verify_ssl=False, ca_bundle_path=None)

    miq_api_class.return_value.post.return_value = dict(results=[
        {'api_version': u'v1',
         'created_on': u'2016-09-08T15:11:29Z',
         'guid': u'84a4084a-75d6-11e6-92bc-0242ee817803',
         'id': PROVIDER_ID,
         'name': u'Openshift01',
         'tenant_id': 1,
         'type': u'ManageIQ::Providers::Openshift::ContainerManager',
         'updated_on': u'2016-09-08T15:11:29Z',
         'zone_id': 1}])
    miq_api_class.return_value.get.return_value = dict(endpoints=[
        {'port': PROVIDER_PORT, 'role': 'default',
         'hostname': PROVIDER_HOSTNAME}], zone_id=1)
    miq_api_class.return_value.collections.providers = [the_provider]
    miq_api_class.return_value.collections.zones = [the_zone]

    yield miq


def test_generate_endpoint(miq):
    endpoint = miq.generate_endpoint("default", PROVIDER_HOSTNAME,
                                     PROVIDER_PORT, "bearer", PROVIDER_TOKEN)
    assert endpoint == {'authentication': {'auth_key': PROVIDER_TOKEN,
                                           'role': 'bearer'},
                        'endpoint': {'hostname': PROVIDER_HOSTNAME,
                                     'port': PROVIDER_PORT,
                                     'role': 'default'}}


def test_will_add_provider_if_none_present(miq, endpoints):
    miq.client.collections.providers = []
    res_args = miq.add_or_update_provider(
        PROVIDER_NAME, "openshift-origin", endpoints, "default")
    assert res_args == {
        'changed': True,
        'msg': 'Successfuly added {} provider'.format(PROVIDER_NAME),
        'provider_id': PROVIDER_ID}
    miq.client.post.assert_called_once_with(
        '{}/api/providers'.format(MANAGEIQ_HOSTNAME),
        connection_configurations=[
            {'endpoint': {'port': PROVIDER_PORT,
                          'role': 'default',
                          'hostname': PROVIDER_HOSTNAME},
             'authentication': {'auth_key': PROVIDER_TOKEN,
                                'role': 'bearer'}},
            {'endpoint': {'port': HAWKULAR_PORT, 'role': 'hawkular',
                          'hostname': HAWKULAR_HOSTNAME},
             'authentication': {'auth_key': PROVIDER_TOKEN,
                                'role': 'hawkular'}}],
        name=PROVIDER_NAME,
        type='ManageIQ::Providers::Openshift::ContainerManager',
        zone={'id': 1})


def test_will_update_provider_if_present(miq, endpoints, the_provider):
    res_args = miq.add_or_update_provider(
        PROVIDER_NAME, "openshift-origin", endpoints, "default")
    assert res_args == {
        'changed': True,
        'msg': 'Successfuly updated {} provider'.format(PROVIDER_NAME),
        'provider_id': the_provider.id,
        'updates': {
            'Added':
            {'hawkular': {
                'hostname': HAWKULAR_HOSTNAME,
                'port': HAWKULAR_PORT}},
            'Removed': {},
            'Updated': {}
        }}


def test_reports_error(miq, endpoints, the_provider, miq_api_class):
    miq_api_class().get.side_effect = Exception("foo")
    with pytest.raises(AnsibleModuleFailed) as excinfo:
        miq.add_or_update_provider(
            PROVIDER_NAME, "openshift-origin", endpoints, "default")
    assert str(excinfo.value) == "Failed to get provider data. Error: foo"
