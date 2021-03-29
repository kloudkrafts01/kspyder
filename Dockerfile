FROM python:3.7

# This Dockerfile is history, as I chose to build on Serverless Azure Functions.
# I cannot guarantee the build will work and if you want to ship this app on Docker-based solutions, it might need work.

COPY requirements.txt /tmp/

# adding custom Microsoft repository
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/ubuntu/18.04/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update -y && ACCEPT_EULA=Y apt-get install -y msodbcsql17 unixodbc-dev
RUN pip install -r /tmp/requirements.txt

RUN useradd --create-home bgspyder
WORKDIR /home/bgspyder
USER bgspyder

COPY --chown=bgspyder . .

ENTRYPOINT [ "python", "main.py" ]
