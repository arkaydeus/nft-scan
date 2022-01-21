#!/bin/sh
docker run -it --rm --mount type=bind,source="$(pwd)",target=/nft-rip/output arkaydeus/nft-rip pipenv run python3 ripnft.py