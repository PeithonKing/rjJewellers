FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_DEBUG=False

WORKDIR /app

COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD bash -c "python manage.py collectstatic --noinput && \
            python manage.py makemigrations && \
            python manage.py migrate && \
            python populate.py --customers 0 --invoices 0 --superuser --username $SUPERUSER_USERNAME --password $SUPERUSER_PASSWORD && \
            gunicorn core.wsgi:application --bind 0.0.0.0:8000"
