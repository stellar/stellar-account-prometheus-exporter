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
 * *stellar_account_buying_liabilities*
 * *stellar_account_selling_liabilities*

Each metric has the following labels:
 * *network* - network name from the configuration file
 * *account_id* - account ID from the configuration file
 * *account_name* - account name, as per configuration file
 * *asset_type* - asset type
