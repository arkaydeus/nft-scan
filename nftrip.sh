#!/bin/sh
docker run -it --rm --env-file ./env --mount type=bind,source="$(pwd)",target=/nft-rip/output arkaydeus/nft-rip pipenv run python3 ripnft.py