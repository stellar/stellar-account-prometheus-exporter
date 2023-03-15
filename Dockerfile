FROM ubuntu:22.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg2 curl apt-utils apt-transport-https ca-certificates
RUN curl -sSL https://apt.stellar.org/SDF.asc|gpg --dearmor >/etc/apt/trusted.gpg.d/SDF.gpg && \
    echo "deb https://apt.stellar.org jammy stable" | tee -a /etc/apt/sources.list.d/SDF.list
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends stellar-account-prometheus-exporter

EXPOSE 9618
ENTRYPOINT ["/usr/bin/stellar-account-prometheus-exporter"]
