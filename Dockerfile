FROM ubuntu:20.04
RUN apt-get update && apt-get install -y --no-install-recommends \
    gnupg2 wget apt-utils apt-transport-https ca-certificates
RUN wget -qO - https://apt.stellar.org/SDF.asc | apt-key add - 
RUN echo -n 'deb https://apt.stellar.org focal stable\n\n' | tee /etc/apt/sources.list.d/SDF.list
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends stellar-account-prometheus-exporter

EXPOSE 9618
ENTRYPOINT ["/usr/bin/stellar-account-prometheus-exporter"]
