FROM python:3.10.12

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./connection /code/connection
COPY ./Database /code/Database
COPY ./Game /code/Game
COPY ./app.py /code/app.py
COPY ./pydantic_models.py /code/pydantic_models.py

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]

# Pre instalar docker

# Tutorial
# https://www.youtube.com/watch?v=HyCO6nMdxC0

# docker build -t lacosa-back .
# docker run -d --name mycontainer -p 80:80 lacosa-back
# docker stop mycontainer
# docker rm mycontainer
# Usando credenciales de azure
# docker login lacosafastapi.azurecr.io -u lacosaFastapi -p /O6T8tNAdKcJAKCpcV5denh3HQEXhIGXHVK707sln++ACRCksI15
# docker build -t lacosafastapi.azurecr.io/lcfastapi:latest .
# docker push lacosafastapi.azurecr.io/lcfastapi:latest

# Actualizar
# docker build -t lacosafastapi.azurecr.io/lcfastapi:latest .
# docker push lacosafastapi.azurecr.io/lcfastapi:latest
# Reinicio

