# -*- coding: utf-8 -*-
import pytest
from mock import Mock

from ansible.module_utils.basic import AnsibleModule

from manageiq_client.api import ManageIQClient
import manageiq_provider


PROVIDER_NAME = "Provider name 1 with some unicode characters «ταБЬℓσ»"
AMAZON_PROVIDER_NAME = "amazon provider"
PROVIDER_HOSTNAME = "some-provider-hostname.tld"
PROVIDER_TOKEN = "THE_PROVIDER_TOKEN"
PROVIDER_PORT = 8443
AMAZON_USERID = "THE_PROVIDER_USERID"
AMAZON_PASSWORD = "THE_PROVIDER_PASSWORD"
AMAZON_PROVIDER_REGION = "THE_PROVIDER-REGION"
PROVIDER_ID = 134
HAWKULAR_HOSTNAME = "some-hawkular-hostname.tld"
HAWKULAR_PORT = 443
MANAGEIQ_HOSTNAME = "http://themanageiq.tld"


POST_RETURN_VALUES = {
    'openshift': {
        'results': [{
            'api_version': u'v1',
            'created_on': u'2016-09-08T15:11:29Z',
            'guid': u'84a4084a-75d6-11e6-92bc-0242ee817803',
            'id': PROVIDER_ID,
            'name': u'Openshift01',
            'tenant_id': 1,
            'type': u'ManageIQ::Providers::Openshift::ContainerManager',
            'updated_on': u'2016-09-08T15:11:29Z',
            'zone_id': 1
        }]
    },
    'amazon': {
        'results': [{
            'api_version': u'v1',
            'created_on': u'2016-09-08T15:11:29Z',
            'guid': u'84a4084a-75d6-11e6-92bc-0242ee817803',
            'id': PROVIDER_ID,
            'name': u'amazon provider',
            'tenant_id': 1,
            'type': u'ManageIQ::Providers::Openshift::ContainerManager',
            'updated_on': u'2016-09-08T15:11:29Z',
            'zone_id': 1,
            'provider_region': AMAZON_PROVIDER_REGION
        }]
    },
    'updated_amazon': {
        'results': [{
            'api_version': u'v1',
            'created_on': u'2016-09-08T15:11:29Z',
            'guid': u'84a4084a-75d6-11e6-92bc-0242ee817803',
            'id': PROVIDER_ID,
            'name': u'amazon provider',
            'tenant_id': 1,
            'type': u'ManageIQ::Providers::Openshift::ContainerManager',
            'updated_on': u'2016-09-08T16:11:29Z',
            'zone_id': 1,
            'provider_region': 'other region'
        }]
    }
}

GET_RETURN_VALUES = {
    'openshift_without_hawkular': {
        'zone_id': 1,
        'endpoints': [{
            'port': PROVIDER_PORT,
            'role': 'default',
            'hostname': PROVIDER_HOSTNAME
        }],
        'authentications': [
            {'authtype': 'bearer',
             'updated_on': '2020-09-22T11:58:30Z',
             'status': 'Valid',
             'status_details': 'Ok',
             'last_valid_on': '2020-09-22T11:00:30Z'}]
    },
    'openshift_with_hawkular': {
        'zone_id': 1,
        'endpoints': [
            {'port': PROVIDER_PORT,
             'role': 'default',
             'hostname': PROVIDER_HOSTNAME},
            {'port': HAWKULAR_PORT,
             'role': 'hawkular',
             'hostname': HAWKULAR_HOSTNAME}
        ],
        'authentications': [
            {'authtype': 'hawkular',
             'updated_on': '2020-09-22T12:58:30Z',
             'status': 'Valid',
             'status_details': 'Ok',
             'last_valid_on': '2020-09-22T12:59:30Z'},
            {'authtype': 'bearer',
             'updated_on': '2020-09-22T11:58:30Z',
             'status': 'Valid',
             'status_details': 'Ok',
             'last_valid_on': '2020-09-22T11:00:30Z'}]
    },
    'amazon': {
        'zone_id': 1,
        'endpoints': [{'role': 'default'}],
        'authentications': [
            {'authtype': 'default',
             'updated_on': '2020-09-22T11:58:30Z',
             'status': 'Valid',
             'status_details': 'Ok',
             'last_valid_on': '2020-09-22T11:00:30Z'}
        ]
    }
}


@pytest.fixture(autouse=True)
def miq_api_class(monkeypatch):
    miq_api_class = Mock(spec=ManageIQClient)
    monkeypatch.setattr("manageiq_provider.MiqApi", miq_api_class)
    yield miq_api_class


@pytest.fixture
def the_provider():
    the_provider = Mock()
    the_provider.name = PROVIDER_NAME
    the_provider.id = PROVIDER_ID
    yield the_provider


@pytest.fixture
def the_amazon_provider():
    the_amazon_provider = Mock()
    the_amazon_provider.name = AMAZON_PROVIDER_NAME
    the_amazon_provider.id = PROVIDER_ID
    yield the_amazon_provider


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
def openshift_endpoint(miq):
    yield [
        miq.generate_openshift_endpoint("default", "bearer", PROVIDER_HOSTNAME,
                                        PROVIDER_PORT, PROVIDER_TOKEN)]


@pytest.fixture
def hawkular_endpoint(miq):
    yield [
        miq.generate_openshift_endpoint("hawkular", "hawkular", HAWKULAR_HOSTNAME,
                                        HAWKULAR_PORT, PROVIDER_TOKEN)]


@pytest.fixture
def amazon_endpoint(miq):
    yield [
        miq.generate_amazon_endpoint("default", "default", userid=AMAZON_USERID,
                                     password=AMAZON_PASSWORD)]



class AnsibleModuleFailed(Exception):
    pass


@pytest.fixture()
def miq(miq_api_class, miq_ansible_module, the_provider, the_amazon_provider, the_zone):
    miq_ansible_module.params = {'metrics': True}

    def fail(msg):
        raise AnsibleModuleFailed(msg)

    miq_ansible_module.fail_json = fail
    miq = manageiq_provider.ManageIQ(miq_ansible_module, MANAGEIQ_HOSTNAME,
                                     "The username", "The password",
                                     verify_ssl=False, ca_bundle_path=None)

    miq_api_class.return_value.collections.zones = [the_zone]

    yield miq


def test_generate_openshift_endpoint(miq):
    endpoint = miq.generate_openshift_endpoint("default", "bearer",
                                               PROVIDER_HOSTNAME,
                                               PROVIDER_PORT,
                                               PROVIDER_TOKEN)
    assert endpoint == {'authentication': {'auth_key': PROVIDER_TOKEN,
                                           'authtype': 'bearer'},
                        'endpoint': {'hostname': PROVIDER_HOSTNAME,
                                     'port': PROVIDER_PORT,
                                     'role': 'default'}}


def test_will_add_openshift_provider_if_none_present(miq, miq_api_class, openshift_endpoint):
    miq_api_class.return_value.collections.providers = []
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['openshift_without_hawkular']
    miq_api_class.return_value.post.return_value = POST_RETURN_VALUES['openshift']

    res_args = miq.add_or_update_provider(
        PROVIDER_NAME, "openshift-origin", openshift_endpoint,
        "default", None)
    assert res_args == {
        'changed': True,
        'msg': 'Successful addition of {} provider. Authentication: All Valid'.format(PROVIDER_NAME),
        'provider_id': PROVIDER_ID,
        'updates': None}
    miq.client.post.assert_called_once_with(
        '{}/api/providers'.format(MANAGEIQ_HOSTNAME),
        connection_configurations=[
            {'endpoint': {'port': PROVIDER_PORT,
                          'role': 'default',
                          'hostname': PROVIDER_HOSTNAME},
             'authentication': {'auth_key': PROVIDER_TOKEN,
                                'authtype': 'bearer'}}],
        name=PROVIDER_NAME,
        type='ManageIQ::Providers::Openshift::ContainerManager',
        zone={'id': 1},
        provider_region=None)


def test_will_add_amazon_provider_if_none_present(miq, miq_api_class, amazon_endpoint):
    miq_api_class.return_value.collections.providers = []
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['amazon']
    miq_api_class.return_value.post.return_value = POST_RETURN_VALUES['amazon']

    res_args = miq.add_or_update_provider(
        AMAZON_PROVIDER_NAME, "amazon", amazon_endpoint,
        "default", AMAZON_PROVIDER_REGION)
    assert res_args == {
        "changed": True,
        "msg": "Successful addition of {} provider. Authentication: All Valid".format(AMAZON_PROVIDER_NAME),
        "provider_id": PROVIDER_ID,
        'updates': None
        }
    miq.client.post.assert_called_once_with(
        '{}/api/providers'.format(MANAGEIQ_HOSTNAME),
        connection_configurations=[
            {'endpoint': {'role': 'default'},
             'authentication': {'userid': AMAZON_USERID,
                                'password': AMAZON_PASSWORD,
                                'authtype': 'default'}}],
        name=AMAZON_PROVIDER_NAME,
        type='ManageIQ::Providers::Amazon::CloudManager',
        zone={'id': 1},
        provider_region=AMAZON_PROVIDER_REGION)


def test_will_update_openshift_provider_if_present(miq, miq_api_class, openshift_endpoint, hawkular_endpoint, the_provider):
    miq_api_class.return_value.collections.providers = [the_provider]
    miq_api_class.return_value.get.side_effect = [
        GET_RETURN_VALUES['openshift_without_hawkular'],
        GET_RETURN_VALUES['openshift_without_hawkular'],
        GET_RETURN_VALUES['openshift_with_hawkular']
    ]
    miq_api_class.return_value.post.return_value = POST_RETURN_VALUES['openshift']

    openshift_endpoint.extend(hawkular_endpoint)
    res_args = miq.add_or_update_provider(
        PROVIDER_NAME, "openshift-origin", openshift_endpoint,
        "default", None)
    assert res_args == {
        'changed': True,
        'msg': 'Successful update of {} provider. Authentication: All Valid'.format(PROVIDER_NAME),
        'provider_id': PROVIDER_ID,
        'updates': {
            'Added': {
                'hawkular': {'hostname': 'some-hawkular-hostname.tld', 'port': 443}
            },
            'Removed': {},
            'Updated': {}
        }
    }


def test_will_update_amazon_provider_if_present(miq, miq_api_class, amazon_endpoint, the_amazon_provider):
    miq_api_class.return_value.collections.providers = [the_amazon_provider]
    miq_api_class.return_value.get.return_value = GET_RETURN_VALUES['amazon']
    miq_api_class.return_value.post.return_value = POST_RETURN_VALUES['updated_amazon']

    res_args = miq.add_or_update_provider(
        AMAZON_PROVIDER_NAME, "amazon", amazon_endpoint, "default",
        "other region")
    assert res_args == {
        'changed': True,
        'msg': 'Successful update of {} provider. Authentication: All Valid'.format(AMAZON_PROVIDER_NAME),
        'provider_id': the_amazon_provider.id,
        'updates': {
            'Added': {},
            'Removed': {},
            'Updated': {
                'provider_region': 'other region'
            }
        }
    }


def test_reports_error(miq, openshift_endpoint, the_provider, miq_api_class):
    miq_api_class.return_value.collections.providers = [the_provider]
    miq_api_class().get.side_effect = Exception("foo")
    with pytest.raises(AnsibleModuleFailed) as excinfo:
        miq.add_or_update_provider(
            PROVIDER_NAME, "openshift-origin", openshift_endpoint, "default", None)
    assert str(excinfo.value) == "Failed to get provider data. Error: Exception('foo',)"
