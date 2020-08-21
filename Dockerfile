# For more information, please refer to https://aka.ms/vscode-docker-python
FROM python:3.8-slim-buster

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE 1

# Exposing Streamlit Default Port for Streamlit
EXPOSE 8501

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED 1

# Install pip requirements
ADD requirements.txt .
RUN python -m pip install -r requirements.txt

# Defining the working directory
WORKDIR /app
ADD app.py /app/

# Creating Streamlit Configuration Directory
RUN mkdir -p /root/.streamlit

# Saving Streamlit Specific Configuration to /root/.streamlit.config.toml file
RUN bash -c 'echo -e "\
[general]\n\
email = \"\"\n\
" > /root/.streamlit/credentials.toml'
RUN bash -c 'echo -e "\
[server]\n\
enableCORS = false\n\
" > /root/.streamlit/config.toml'

# Switching to a non-root user, please refer to https://aka.ms/vscode-docker-python-user-rights
RUN useradd appuser && chown -R appuser /app
USER appuser

# Running the Streamlit Application
CMD streamlit run /app/app.py

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8