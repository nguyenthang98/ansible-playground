FROM ubuntu:18.04

MAINTAINER nguyenthang98

RUN apt update && apt install -y software-properties-common \
    && apt-add-repository --yes --update ppa:ansible/ansible \
    && apt install -y ansible

COPY ./playbook /ansible

WORKDIR /ansible

CMD ["ansible", "--version"]
