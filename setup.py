import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="stellar-account-prometheus-exporter",
    version="0.0.5",
    author="Stellar Development Foundation",
    author_email="ops@stellar.org",
    description="Export stellar account balance in prometheus format",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/stellar/stellar-account-prometheus-exporter",
    include_package_data=True,
    keywords=["prometheus", "exporter", "stellar"],
    license="Apache Software License 2.0",
    entry_points={
        'console_scripts': [
            'stellar-account-prometheus-exporter=stellar_account_prometheus_exporter:run',
        ],
    },
    packages=setuptools.find_packages(),
    install_requires=["prometheus_client", "requests", "pyyaml"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Information Technology",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: Apache Software License",
    ],
)
