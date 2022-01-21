FROM python:3.10
WORKDIR /nft-rip
COPY . .
RUN pip3 install --no-cache-dir pipenv
RUN pipenv install
RUN pipenv --clear
CMD ["python3","ripnft.py"]