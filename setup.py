from setuptools import setup, find_packages

exec(open('yaseeker/_version.py').read())

with open('requirements.txt') as rf:
    requires = rf.read().splitlines()

with open('README.md') as fh:
    long_description = fh.read()

setup(
    name="yaseeker",
    version=__version__,
    description="Yandex profile seeker took",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/soxoj/YaSeekerUltra",
    author="Soxoj",
    author_email="soxoj@protonmail.com",
    entry_points={'console_scripts': ['yaseeker = yaseeker.__init__:run']},
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
)
