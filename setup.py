from setuptools import setup

setup(
    name='manageiq-ansible-module',
    description='ManageIQ Ansible module',
    author='Daniel Korn',
    author_email='dkorn@redhat.com',
    url='https://github.com/dkorn/manageiq-ansible-module',
    package_dir={'': 'library'},
    py_modules=["manageiq_provider", "manageiq_policy_assignment",
                "manageiq_custom_attributes", "manageiq_user"],
    install_requires='ansible manageiq-client'.split(),
)
