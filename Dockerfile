FROM python:3.7-alpine
COPY setup.py tqdm/
COPY requirements-dev.txt tqdm/
COPY README.rst tqdm/
COPY tqdm tqdm/tqdm
RUN pip install -U ./tqdm
ENTRYPOINT ["tqdm"]
