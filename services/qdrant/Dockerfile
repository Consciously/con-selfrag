FROM qdrant/qdrant:latest
USER root
# Try multiple approaches to install curl
RUN apt-get update --fix-missing && apt-get install -y curl || \
    (echo "Network issues, trying alternative..." && \
     apt-get clean && apt-get update --fix-missing && apt-get install -y curl)
USER qdrant
