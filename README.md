# Overview

The Stellar Account Prometheus Exporter retrieves account(s)
balance and exposes it in prometheus format.

# Configuration

Configuration file path must be provided using the --config option.

The config file is yaml formatted file:
```
networks:
- name: pubnet                              # Human readable name
  horizon_url: https://horizon.example.com  # Horizon URL
  accounts:
  - account_id: ABC123XYZ     # Account ID
    account_name: Account one # Human readable description
  - account_id: DEF456ABC
    account_name: Account two
- name: testnet
  horizon_url: https://horizon-testnet.example.com
  accounts:
  - account_id: QWE789DEF
    account_name: Testnet test account
```

By default the exporter listens on port 9618. This can be changes using
--port switch or "PORT" environment variable.

# Exported data

For each account the following metrics are exported:
 * *stellar_account_balance*
 * *stellar_account_available_balance*
 * *stellar_account_buying_liabilities*
 * *stellar_account_selling_liabilities*
 * *stellar_account_num_sponsored*
 * *stellar_account_num_sponsoring*

Each metric has the following labels:
 * *network* - network name from the configuration file
 * *account_id* - account ID from the configuration file
 * *account_name* - account name, as per configuration file
 * *asset_type* - asset type

# Installing from pypi

To download/test package in pypi you can use venv:
```
python3 -m venv venv
. venv/bin/activate
```

Install:
```
python3 -m pip install stellar_account_prometheus_exporter
```

Run:
```
./venv/bin/stellar-account-prometheus-exporter --config /path/to/config.yaml
```

# Releasing new version

* ensure you bumped version number in setup.py. PyPi does not allow version reuse
* build new package:
```
python3 setup.py sdist bdist_wheel
```
* push to testpypi:
```
python3 -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*
```
* test by installing the package (see above). If all good release:
```
python3 -m twine upload dist/*
```
