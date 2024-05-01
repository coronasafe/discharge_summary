# Discharge Summary

[![Release Status](https://img.shields.io/pypi/v/discharge_summary.svg)](https://pypi.python.org/pypi/discharge_summary)
[![Build Status](https://github.com/coronasafe/discharge_summary/actions/workflows/build.yaml/badge.svg)](https://github.com/coronasafe/discharge_summary/actions/workflows/build.yaml)

Discharge Summary is a plugin for care to add AI generated summary for patient discharge.


## Features

- Generate summary for patient discharge using AI

## Installation

https://care-be-docs.coronasafe.network/pluggable-apps/configuration.html

https://github.com/coronasafe/care/blob/develop/plug_config.py


To install Discharge Summary, you can add the plugin config in [care/plug_config.py](https://github.com/coronasafe/care/blob/develop/plug_config.py) as follows:

```python
...

discharge_summary_plug = Plug(
    name="discharge_summary",
    package_name="git+https://github.com/coronasafe/discharge_summary.git",
    version="@master",
    configs={
        "SERVICE_PROVIDER_API_KEY": "secret",
    },
)
plugs = [discharge_summary_plug]
...
```

## Configuration

The following configurations variables are available for Discharge Summary:

- `SERVICE_PROVIDER_API_KEY`: API key for the summary service provider (OpenAI key)

The plugin will try to find the API key from the config first and then from the environment variable.

## License

This project is licensed under the terms of the [MIT license](LICENSE).


---
This plugin was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) using the [coronasafe/care-plugin-cookiecutter](https://github.com/coronasafe/care-plugin-cookiecutter).