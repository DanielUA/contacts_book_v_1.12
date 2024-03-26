FROM python:3.10

WORKDIR /contacts_book

COPY . .

ENTRYPOINT ["python", "main.py"]
