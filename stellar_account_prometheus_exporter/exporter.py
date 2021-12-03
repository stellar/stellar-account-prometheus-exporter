#!/usr/bin/env python
# vim: tabstop=4 expandtab shiftwidth=4

import argparse
import logging
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
# Initialize logger
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("stellar-account-exporter")

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

        account_label_names = ["network", "account_id", "account_name"]
        m_num_sponsored = Gauge("stellar_account_num_sponsored", "Stellar core account number of sponsored entries",
                                account_label_names, registry=self.registry)
        m_num_sponsoring = Gauge("stellar_account_num_sponsoring", "Stellar core account number of sponsoring entries",
                                 account_label_names, registry=self.registry)

        m_account_exists = Gauge("stellar_account_scrape_success", "Indicates whether data was gathered successfully",
                                    account_label_names, registry=self.registry)

        balance_label_names = account_label_names + ["asset_type"]
        m_balance = Gauge("stellar_account_balance", "Stellar core account balance",
                          balance_label_names, registry=self.registry)
        m_buying_liabilities = Gauge("stellar_account_buying_liabilities", "Stellar core account buying liabilities",
                                     balance_label_names, registry=self.registry)
        m_selling_liabilities = Gauge("stellar_account_selling_liabilities", "Stellar core account selling liabilities",
                                      balance_label_names, registry=self.registry)
        m_available_balance = Gauge("stellar_account_available_balance", "Stellar core account available balance, i.e. the account balance exceding the minimum required balance of `(2 + subentry_count + num_sponsoring - num_sponsored) * 0.5 + liabilities.selling`",
                                    balance_label_names, registry=self.registry)

        for network in config["networks"]:
            if "accounts" not in network or "name" not in network or "horizon_url" not in network:
                self.error(500, 'Error - invalid network configuration: {}'.format(network))
                return
            for account in network["accounts"]:
                account_labels = [network["name"], account["account_id"], account["account_name"]]

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
                    m_account_exists.labels(*account_labels).set(0)
                    logger.error("Error retrieving data from {}".format(url))
                    continue
                if "balances" not in r.json() or "subentry_count" not in r.json():
                    m_account_exists.labels(*account_labels).set(0)
                    logger.error("Error - no balances or subentry_count found for account {}".format(account["account_id"]))
                    continue

                m_num_sponsored.labels(*account_labels).set(r.json().get("num_sponsored", 0))
                m_num_sponsoring.labels(*account_labels).set(r.json().get("num_sponsoring", 0))

                m_account_exists.labels(*account_labels).set(1)

                for balance in r.json()["balances"]:
                    labels = [network["name"], account["account_id"], account["account_name"], balance["asset_type"]]

                    m_balance.labels(*labels).set(balance["balance"])
                    m_buying_liabilities.labels(*labels).set(balance["buying_liabilities"])
                    m_selling_liabilities.labels(*labels).set(balance["selling_liabilities"])

                    # ref: https://github.com/stellar/stellar-protocol/blob/a664806db12635ab4d49b3f006c8f1b578fba8d4/core/cap-0033.md#reserve-requirement
                    minimum_required_balance = float(balance["selling_liabilities"])
                    if balance["asset_type"] == "native":
                        minimum_required_balance += 0.5 * (2 + r.json()["subentry_count"] + r.json().get("num_sponsoring", 0) - r.json().get("num_sponsored", 0))
                    m_available_balance.labels(*labels).set(float(balance["balance"]) - minimum_required_balance)

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
