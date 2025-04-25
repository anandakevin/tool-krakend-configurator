# Use the official KrakenD image
FROM devopsfaith/krakend:2.7

# Define the environment variable for selecting the config
ARG ENV=DEV

# Copy the krakend.json corresponding to the environment
COPY result/$ENV/krakend.json /etc/krakend/krakend.json

# You can add any other necessary configuration or commands here
