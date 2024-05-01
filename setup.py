#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "jsonschema",
    "django",
    "djangorestframework",
    "openai",
    "botocore",
    "celery",
    "django-hardcopy",
    "drf_spectacular",
    "dry_rest_permissions",
    "django-environ",
]

test_requirements = []

setup(
    author="Vignesh Hari",
    author_email="hey@vigneshhari.dev",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    description="Nothing Much",
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="discharge_summary",
    name="discharge_summary",
    packages=find_packages(include=["discharge_summary", "discharge_summary.*"]),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/coronasafe/discharge_summary",
    version="0.1.0",
    zip_safe=False,
)
