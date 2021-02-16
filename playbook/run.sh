#!/bin/bash

docker run --rm -it -v $(pwd):/ansible ansible:latest ansible-playbook site.yml $@
