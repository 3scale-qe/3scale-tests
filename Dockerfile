FROM quay.io/centos/centos:stream
LABEL description="Run 3scale integration tests \
Default ENTRYPOINT: 'make' and CMD: 'smoke' \
Bind dynaconf settings to /opt/secrets.yaml \
Bind kubeconfig to /opt/kubeconfig \
Bind a dir to /test-run-results to get reports \
Set NAMESPACE env variable"

ARG cacert=https://password.corp.redhat.com/RH-IT-Root-CA.crt

USER root

ADD $cacert /etc/pki/ca-trust/source/anchors
ADD https://gist.githubusercontent.com/mdujava/c87f687cbb9bbed0144ddc136758292c/raw/7dbb42e02e2b0fe75074efccd7350e3082cc6655/ca.pem /etc/pki/ca-trust/source/anchors
RUN update-ca-trust

RUN useradd --no-log-init -u 1001 -g root -m default
RUN curl https://mirror.openshift.com/pub/openshift-v4/clients/ocp/4.10.29/openshift-client-linux.tar.gz | tar xz -C /usr/local/bin

RUN curl -L https://github.com/cloudflare/cfssl/releases/download/v1.6.1/cfssl_1.6.1_linux_amd64 >/usr/local/bin/cfssl && \
    chmod +x /usr/local/bin/cfssl

RUN yum install -y python3.9 git make gettext && \
	yum clean all

RUN pip3 --no-cache-dir install pipenv

WORKDIR /opt/workdir/3scale-py-testsuite

COPY . .

RUN mkdir -m 0770 /test-run-results && \
	mkdir -m 0770 -p /opt/workdir/virtualenvs && \
	chmod -R g+w /opt/workdir/* && \
	chmod g+w /opt

USER default

ENV KUBECONFIG=/opt/kubeconfig
ENV SECRETS_FOR_DYNACONF=/opt/secrets.yaml
ENV PIPENV_IGNORE_VIRTUALENVS=1
ENV REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt
ENV SSL_CERT_FILE=/etc/pki/tls/certs/ca-bundle.crt
ENV WORKON_HOME=/opt/workdir/virtualenvs
ENV junit=yes
ENV html=yes
ENV resultsdir=/test-run-results
ENV BASH_ENV=~/.profile

RUN echo umask 002 | tee -a $HOME/.profile >>$HOME/.bashrc \
	&& make mostlyclean pipenv \
	&& rm -Rf $HOME/.cache/*

ENTRYPOINT [ "make" ]
CMD [ "smoke" ]
