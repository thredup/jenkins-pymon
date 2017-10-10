FROM python

RUN pip install requests datadog PyYAML
RUN mkdir -p /app/cfg

COPY init.py /app/init.py
COPY config.yaml /app/cfg

ENTRYPOINT ["/app/init.py"]
