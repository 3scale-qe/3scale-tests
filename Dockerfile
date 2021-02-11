FROM registry.access.redhat.com/ubi7/python-36:latest
LABEL description="Required env variables: \
_3SCALE_TESTS_OPENSHIFT__servers__default__server_url={OPENSHIFT_URL}; \
_3SCALE_TESTS_OPENSHIFT__servers__default__token={OPENSHIFT_TOKEN}; \
_3SCALE_TESTS_OPENSHIFT__projects__threescale__name={OPENSHIFT_PROJECT}"

USER root

ADD https://password.corp.redhat.com/RH-IT-Root-CA.crt /etc/pki/ca-trust/source/anchors
ADD https://gist.githubusercontent.com/mijaros/c9c9ed016ce9985d96c6c5c3b35b4050/raw/66587720883554b03a4c24875fa47442db231a51/ca.pem /etc/pki/ca-trust/source/anchors
RUN update-ca-trust

RUN curl https://mirror.openshift.com/pub/openshift-v4/clients/ocp/stable/openshift-client-linux.tar.gz >/tmp/oc.tgz && \
	tar xzf /tmp/oc.tgz -C /usr/local/bin && \
	rm /tmp/oc.tgz

RUN yum install -y --enablerepo=rhel-7-server-extras-rpms docker-client openssh-clients && \
	yum clean all

RUN pip3 --no-cache-dir install pipenv

RUN mkdir -m 0770 /test-run-results
RUN mkdir -m 0770 -p /opt/workdir/virtualenvs

WORKDIR /opt/workdir/3scale-py-testsuite

COPY . .

RUN chmod -R g+w /opt/workdir/*

USER default

ENV REQUESTS_CA_BUNDLE=/etc/pki/tls/certs/ca-bundle.crt
ENV WORKON_HOME=/opt/workdir/virtualenvs
ENV junit=yes
ENV resultsdir=/test-run-results

RUN make mostlyclean pipenv && \
	rm -Rf $HOME/.cache/*

ENTRYPOINT [ "make" ]
CMD [ "smoke" ]
