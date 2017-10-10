FROM python

RUN pip install requests datadog yaml
RUN mkdir /app

COPY init.py /app/init.py

ENTRYPOINT ["/app/init.py"]
