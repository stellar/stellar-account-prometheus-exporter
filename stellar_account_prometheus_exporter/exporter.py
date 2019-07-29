#!/usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4

import argparse
import requests
import yaml
import threading
import time
from os import environ

# Prometheus client library
from prometheus_client import CollectorRegistry
from prometheus_client.core import Gauge
from prometheus_client.exposition import CONTENT_TYPE_LATEST, generate_latest


try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from SocketServer import ThreadingMixIn
except ImportError:
    # Python 3
    unicode = str
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from socketserver import ThreadingMixIn


parser = argparse.ArgumentParser(description='Exposes staller account balance to prometheus')
parser.add_argument('--port', type=int,
                    help='HTTP bind port. Defaults to PORT environment variable '
                         'or if not set to 9618',
                    default=int(environ.get('PORT', '9618')))
parser.add_argument('--config', nargs='?',
                    help='Configuration file path',
                    default='/etc/prometheus/stellar-account-exporter.yaml',
                    type=argparse.FileType('r'))
args = parser.parse_args()
config = yaml.safe_load(args.config.read())


class _ThreadingSimpleServer(ThreadingMixIn, HTTPServer):
    """Thread per request HTTP server."""
    # Copied from prometheus client_python
    daemon_threads = True


class StellarCoreHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def error(self, code, msg):
        self.send_response(code)
        self.send_header('Content-Type', CONTENT_TYPE_LATEST)
        self.end_headers()
        self.wfile.write('{}\n'.format(msg).encode('utf-8'))

    def do_GET(self):
        self.registry = CollectorRegistry()
        label_names = ["network", "account_id", "account_name", "asset_type"]
        m_balance = Gauge("stellar_account_balance", "Stellar core account balance",
                          label_names, registry=self.registry)
        m_buying_liabilities = Gauge("stellar_account_buying_liabilities", "Stellar core account buying liabilities",
                                     label_names, registry=self.registry)
        m_selling_liabilities = Gauge("stellar_account_selling_liabilities", "Stellar core account selling liabilities",
                                      label_names, registry=self.registry)

        for network in config["networks"]:
            if "accounts" not in network or "name" not in network or "horizon_url" not in network:
                self.error(500, 'Error - invalid network configuration: {}'.format(network))
                return
            for account in network["accounts"]:
                if "account_id" not in account or "account_name" not in account:
                    self.error(500, 'Error - invalid account configuration: {}'.format(account))
                    return
                url = network["horizon_url"] + "/accounts/" + account["account_id"]
                try:
                    r = requests.get(url)
                except requests.ConnectionError:
                    self.error(504, 'Error retrieving data from {}'.format(url))
                    return
                if not r.ok:
                    self.error(504, 'Error retrieving data from {}'.format(url))
                    return
                if "balances" not in r.json():
                    self.error(500, "Error - no balances found for account {}".format(account["account_id"]))
                    return
                for balance in r.json()["balances"]:
                    labels = [network["name"], account["account_id"], account["account_name"], balance["asset_type"]]
                    m_balance.labels(*labels).set(balance["balance"])
                    m_buying_liabilities.labels(*labels).set(balance["buying_liabilities"])
                    m_selling_liabilities.labels(*labels).set(balance["selling_liabilities"])

        output = generate_latest(self.registry)
        self.send_response(200)
        self.send_header('Content-Type', CONTENT_TYPE_LATEST)
        self.end_headers()
        self.wfile.write(output)


def main():
    httpd = _ThreadingSimpleServer(("", args.port), StellarCoreHandler)
    t = threading.Thread(target=httpd.serve_forever)
    t.daemon = True
    t.start()
    while True:
        time.sleep(1)


if __name__ == "__main__":
    main()
