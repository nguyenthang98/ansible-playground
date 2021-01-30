#!/bin/bash

docker run --rm -it --network=ansible-net -v $(pwd):/ansible ansible:latest ansible-playbook site.yml $@
