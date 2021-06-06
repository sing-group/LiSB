from setuptools import setup, find_packages

setup(
    name='SpamFilterWeb',
    version='1.0',
    long_description="This Flask Wep App acts a UI for the SpamFilterServer",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['Flask']
)