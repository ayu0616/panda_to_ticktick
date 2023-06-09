FROM python:alpine

WORKDIR /app

# ARG TICKTICK_TOKEN_OAUTH

# RUN echo ${TICKTICK_TOKEN_OAUTH} > .token-oauth

COPY requirements.txt .

RUN apk add --no-cache gcc musl-dev &&\
    pip install -r requirements.txt

COPY . /app

EXPOSE 3000

CMD ["python", "app.py"]