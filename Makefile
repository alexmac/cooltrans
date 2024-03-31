HASH := $(shell tar -cf - --exclude='./.git' . | shasum | cut -d' ' -f1)

DOCKER_IMAGE_BASE := ${AWS_ACCOUNT_ID}.dkr.ecr.us-west-2.amazonaws.com

build: docker-push-cooltrans docker-push-twitch

.PHONY: docker-build-% docker-push-% create-ecr-repo-%

docker-build-%:
	@if ! docker image inspect $(DOCKER_IMAGE_BASE)/staging/$*:$(HASH) > /dev/null; then \
		echo "Building Docker image $*..."; \
		docker build --progress plain -t $(DOCKER_IMAGE_BASE)/staging/$*:$(HASH) -f $*.dockerfile .; \
	fi

create-ecr-repo-%:
	@echo "Checking if ECR repository 'staging/$*' exists..."
	@if ! aws ecr describe-repositories --repository-names "staging/$*" >/dev/null ; then \
		@echo "Repository does not exist. Creating repository staging/$*..."; \
		aws ecr create-repository --repository-name "staging/$*"; \
	fi

docker-push-%: docker-build-% create-ecr-repo-%
	@echo "Pushing Docker image $*..."
	@docker push $(DOCKER_IMAGE_BASE)/staging/$*:$(HASH)
	@echo "example: docker run --rm -it $(DOCKER_IMAGE_BASE)/staging/$*:$(HASH) bash"
