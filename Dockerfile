# Use the official JupyterLab image as the base image
FROM jupyter/base-notebook:python-3.10

# upgrade pip
RUN pip install --upgrade pip

# Switch back to the notebook user
USER $NB_UID

# Install Python packages
COPY --chown=${NB_UID}:${NB_GID} requirements.txt /tmp/
RUN pip install --quiet --no-cache-dir --requirement /tmp/requirements.txt