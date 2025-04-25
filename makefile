# Variables
REGISTRY ?=  # Allow overriding in GitHub Actions or via command line
REPOSITORY ?= api-gateway-krakend
ENV ?= LOCAL  # Allow ENV to be overridden (defaults to LOCAL)

# Detect the architecture (local vs CI)
LOCAL_ARCH := $(shell uname -m)

# Set PLATFORM and IMAGE_TAG based on environment (local or CI)
ifeq ($(ENV),)
    ENV := DEV  # Default to DEV if ENV is not set
endif

# Set platform based on environment and architecture
ifeq ($(ENV), LOCAL)
    PLATFORM =      # No platform defined for local (will be handled by Docker default)
    IMAGE_TAG := latest-$(LOCAL_ARCH)  # Tag based on local architecture
else
    PLATFORM = linux/amd64  # For DEV/PROD, use amd64 platform
    IMAGE_TAG := $(IMAGE_TAG)  # Tag based on amd64 architecture for CI
endif

# Build, tag, and push the Docker image
docker-build-push:
	DOCKER_BUILDKIT=0 docker build \
		$(if $(PLATFORM),--platform $(PLATFORM)) \
		--build-arg ENV=$(ENV) \
		$(if $(REGISTRY),--tag $(REGISTRY)/$(REPOSITORY):$(IMAGE_TAG)) \
		--tag $(REPOSITORY):$(IMAGE_TAG) .  # Tag without REGISTRY for local
	$(if $(REGISTRY),docker push $(REGISTRY)/$(REPOSITORY):$(IMAGE_TAG),)  # Push only if REGISTRY is set

# Local build target (for ARM64 architecture or default local configuration)
docker-build-local:
	$(MAKE) docker-build-push ENV=LOCAL

# Local environment build (with push)
docker-build-push-local:
	$(MAKE) docker-build-push ENV=LOCAL REGISTRY=thechief28

# DEV environment build (with push)
docker-build-push-dev:
	$(MAKE) docker-build-push ENV=DEV REGISTRY=$(REGISTRY)

# PROD environment build (with push)
docker-build-push-prod:
	$(MAKE) docker-build-push ENV=PROD REGISTRY=$(REGISTRY)

# Run JWK fingerprint preparation and convert Excel to JSON based on ENV
generate-krakend-json:
	python scripts/krakend_json_generator.py

# Helper command to prepare and convert for Local environment
generate-krakend-json-local:
	$(MAKE) generate-krakend-json ENV=LOCAL

# Helper command to prepare and convert for Development environment
generate-krakend-json-dev:
	$(MAKE) generate-krakend-json ENV=DEV

# Helper command to prepare and convert for Production environment
generate-krakend-json-prod:
	$(MAKE) generate-krakend-json ENV=PROD

# Helper commmand to prepare and convert for All environment
generate-krakend-json-all:
	$(MAKE) generate-krakend-json-local generate-krakend-json-dev generate-krakend-json-prod

# Define a target for installing Python dependencies
install-python-deps:
	pip install -r scripts/requirements.txt

# Checks the existing images in the 'api-gateway/krakend' ECR repository in the specified region.
aws-check-build:
	aws ecr describe-images --repository-name api-gateway/krakend --region ap-southeast-3
