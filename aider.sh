#!/bin/bash
## env vars for keys and projects
export DEEPSEEK_API_KEY="$(cat /mnt/e/Dev/DS.txt)"
export ANTHROPIC_API_KEY="$(cat /mnt/e/Dev/AP.txt)"
export GOOGLE_APPLICATION_CREDENTIALS="/mnt/e/Dev/VThrkm.json"
export VERTEXAI_PROJECT="sharp-terminal-429710-k4"
export VERTEXAI_LOCATION="europe-west1"

## Variables
IMAGE_NAME="paulgauthier/aider"
CONTAINER_NAME="aider-container"

## Model to use
#INITIAL_MODEL=deepseek/deepseek-coder
INITIAL_MODEL="vertex_ai/claude-3-5-sonnet@20240620"

# download latest image
docker pull ${IMAGE_NAME}

# Start the Docker container with aider vars, docker socket and pwd (repo) mounted
# note aider in docker will exit immediately
echo "Stopping, removing and starting Docker container..."
docker stop ${CONTAINER_NAME}
sleep 2
docker rm ${CONTAINER_NAME}
docker run --rm -d --name ${CONTAINER_NAME} \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v $(pwd):/app \
  -v /mnt/e/Dev/:/mnt/e/Dev/ \
  -e GOOGLE_APPLICATION_CREDENTIALS="$GOOGLE_APPLICATION_CREDENTIALS" -e VERTEXAI_PROJECT=$VERTEXAI_PROJECT -e VERTEXAI_LOCATION=$VERTEXAI_LOCATION \
  --entrypoint sleep ${IMAGE_NAME} infinity

# Wait a few seconds to ensure the container is up
sleep 5

# Install Docker CLI and other requirements inside the container
echo "Installing Docker CLI..."
docker exec ${CONTAINER_NAME} bash -c "
  apt-get update &&
  apt-get install -y docker.io &&
  pip install -U google-cloud-aiplatform "anthropic[vertex]" &&
  pip install -U -r requirements.txt &&
  apt-get clean &&
  rm -rf /var/lib/apt/lists/*
"
echo "...Done installing."

# Optional: Print the Docker version inside the container to verify installation
echo "Verifying Docker installation..."
docker exec ${CONTAINER_NAME} docker --version

# Start aider with args
docker exec -it ${CONTAINER_NAME} aider \
  --openai-api-key $DEEPSEEK_API_KEY --anthropic-api-key $ANTHROPIC_API_KEY \
  --model ${INITIAL_MODEL}

# Clean-up container after exiting aider
docker stop ${CONTAINER_NAME}
sleep 2
docker rm ${CONTAINER_NAME}