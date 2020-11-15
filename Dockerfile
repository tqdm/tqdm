FROM python:3.7-alpine
COPY setup.py tqdm/
COPY dist/*.whl .
RUN pip install -U $(ls *.whl) && rm *.whl
ENTRYPOINT ["tqdm"]
