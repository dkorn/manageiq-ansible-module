from setuptools import setup

setup(
    name='manageiq-ansible-module',
    description='ManageIQ Ansible module',
    author='Daniel Korn',
    author_email='dkorn@redhat.com',
    url='https://github.com/dkorn/manageiq-ansible-module',
    package_dir={'': 'library'},
    py_modules=["manageiq_provider", "manageiq_policy_assignment"],
    install_requires='ansible manageiq-api-client-python'.split(),
)
