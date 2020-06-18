FROM google/cloud-sdk:alpine@sha256:831392d2de636422829112ef2439719d46b3c60e837f56228dbd58c4e6f31718
RUN apk --update --no-cache add py3-pip && pip3 install --upgrade pip
RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.18.4/bin/linux/amd64/kubectl &&\
    chmod +x ./kubectl && mv ./kubectl /usr/local/bin/kubectl
RUN apk --update --no-cache add jq
COPY setup.py requirements.txt /opt/rsp/
COPY resourcesaverproxy /opt/rsp/resourcesaverproxy
WORKDIR /opt/rsp
RUN pip3 install -r requirements.txt && pip3 install -e .
ENV FLASK_APP=resourcesaverproxy.web
ENTRYPOINT ["rsp"]
