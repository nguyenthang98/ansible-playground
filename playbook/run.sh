#!/bin/bash

docker run --rm -it --network=host -v $(pwd):/ansible ansible:latest ansible-playbook site.yml $@
