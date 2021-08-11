MAJOR?=0
MINOR?=18
VERSION=$(MAJOR).$(MINOR)

BUILD_DATE=$(shell date +%Y%m%d.%H%M%S)

APP_NAME?="n-pods-app"

# Relative to $GOPATH/app
PROJECT_DIR="github.com/docker/testing-eng/test-apps/n-pods-app/"
# Our Hub account name
HUB_NAMESPACE?="jnesbitt"
# MSR url
HUB_URL?= "msr.ci.mirantis.com"


# Find go files and packages in this repo for go test
GOPACKAGES=$(shell go list ${PROJECT_DIR}/... | grep -v -e /vendor/ )
GOFILES = $(shell find . -type f -name '*.go')
GOFILES_NOVENDOR = $(shell find . -type f -name '*.go' -not -path "*/vendor/*")

# Current git state of repo
GIT_COMMIT = $(shell git rev-parse HEAD)
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)

# Host we will be building image on. Windows and IBM Z nodes are special cases
# requiring custom dockerfiles and produce different docker images.
#
# Use 'make host-info' to confirm what image will get built before trying to build.
#
# OS_FAMILY | OS_ARCH | KERNEL_VERSION| testkit pform | Release | Resulting Image
# linux     | x86_64  | N/A           | rhel_7.5, etc.| N/A     | reference-app

# regular engine returns e.g., '18.09.1' UCP returns 'ucp/3.1.2-1198d50'
# If pointed at UCP, the OS_FAMILY will be empty, and we can not build.
IS_UCP = $(shell docker version --format '{{ .Server.Version }}' | grep 'ucp')

OS_INFO = $(shell docker info --format='{{.OSType}}:{{.Architecture}}')
OS_FAMILY = $(shell echo ${OS_INFO} | awk -F: '{print $$1}')
OS_ARCH = $(shell echo ${OS_INFO} | awk -F: '{print $$2}')
KERNEL_VERSION = $(shell docker info --format='{{.KernelVersion}}' | awk '{print $$2}')

DOCKERFILE = "Dockerfile"
IMAGE_NAME = "${APP_NAME}"


##########################
# Help screen. invoked by any of: 'make', 'make default', 'make help'
##########################
.PHONY: default
default:
	@echo "${IMAGE_NAME} version ${VERSION}"
	@echo ""
	@echo "Note: To use test-static, install the tools first:"
	@echo "      go get -u github.com/golang/lint/golint"
	@echo "      go get -u github.com/gordonklaus/ineffassign"
	@echo ""
	@echo "Please specify a target. The choices are:"
	@echo ""
	@echo "------------ Info ----------"
	@echo "host-info  : Identify what host OS the docker CLI is pointed at (and"
	@echo "             therefore what image will get built) and stop."
	@echo "---------- Testing ---------"
	@echo "test-static: Run go static analysis tools: go vet, golint"
	@echo "check-fmt  : Run go fmt and report. Does not alter files."
	@echo "fmt        : Run go fmt and modify files (ignores vendor/)"
	@echo "---------- Docker ----------"
	@echo "image      : Build image ${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION}"
	@echo "push       : Build image ${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION} and push to Hub"
	@echo "clean-image: Run docker rmi ${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION}"
	@echo "---------- Release ---------"
	@echo "tag        : Git tag master branch with ${VERSION}"
	@echo "release    : Execute test, build, image, tag, push"

.PHONY: help
help: default
	@echo ""

#################################
# Docker targets
#################################
.PHONY: clean-image
clean-image: version-check
	@echo "+ $@"
	@docker rmi ${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION}
	@docker rmi ${HUB_NAMESPACE}/${IMAGE_NAME}:latest

.PHONY: host-info
host-info:
	@echo "OS_INFO         is '${OS_INFO}'"
	@echo "OS_ARCH         is '${OS_ARCH}'"
	@echo "OS_FAMILY       is '${OS_FAMILY}'"
	@echo "KERNEL_VERSION  is '${KERNEL_VERSION}'"
	@echo "DOCKERFILE      is '${DOCKERFILE}'"
	@echo "IMAGE_NAME      is '${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION}'"
	@echo "BUILD_DATE      is '${BUILD_DATE}'"
	@echo "HUB_URL    	   is '${HUB_URL}'"

.PHONY: image
image: target-check version-check
	@echo "+ $@"
	@docker build -t ${HUB_URL}/${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION} --build-arg VERSION=${VERSION} --build-arg BUILD_DATE=${BUILD_DATE} -f ./${DOCKERFILE} .
	@docker tag ${HUB_URL}/${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION} ${HUB_URL}/${HUB_NAMESPACE}/${IMAGE_NAME}:latest
	@echo 'Done.'
	@docker images --format '{{.Repository}}:{{.Tag}}\t\t Built: {{.CreatedSince}}\t\tSize: {{.Size}}' | grep ${IMAGE_NAME}:${VERSION}

.PHONY: push
push:
	@echo "+ $@"
	@docker push ${HUB_URL}/${HUB_NAMESPACE}/${IMAGE_NAME}:${VERSION}
	@docker push ${HUB_URL}/${HUB_NAMESPACE}/${IMAGE_NAME}:latest

#################################
# test targets
#################################
.PHONY: check-fmt
check-fmt:
	@echo "+ $@"
	@gofmt -d ${GOFILES_NOVENDOR}
	@gofmt -l ${GOFILES_NOVENDOR} | (! grep . -q) || (echo "Code differs from gofmt's style. Run 'make fmt'" && false)
	@echo "go fmt check OK"

# Runs gofmt -w on the project's source code, modifying any files that do not
# match its style.
.PHONY: fmt
fmt:
	@echo "+ $@"
	@gofmt -l -w ${GOFILES_NOVENDOR}
	@goimports -l -w ${GOFILES_NOVENDOR}

# run static analysis tools on code base.
# note the 'echo "tool X OK' messages will only execute
# if the tools succeded. (Make will halt on the first command
# that returns non-zero status.)
.PHONY: test-static
test-static: check-fmt
	@echo "+ $@"
	@echo "go vet ${GOPACKAGES}"
	@go vet ${GOPACKAGES}
	@echo "go vet OK"
	@echo "golint ${GOPACKAGES}"
	@golint ${GOPACKAGES}
	@echo "go lint OK"
	@echo "ineffassign ."
	@ineffassign .
	@echo "ineffassign OK"

#################################
# release targets
#################################
.PHONY: release
release: branch-check check-fmt build clean-image image tag push

.PHONY: tag
tag: version-check branch-check
	@echo "+ $@"
	@git fetch --all
	@git pull --rebase
	@echo "Tag commit ${GIT_COMMIT} as version ${VERSION}"
	@git tag release/${VERSION} ${GIT_COMMIT}
	@git tag -l -n
	@git push --tags origin

#################################
# Utilities
#################################
.PHONY: target-check image-name-check dockerfile-check is-ucp-check
target-check: is-ucp-check image-name-check dockerfile-check

is-ucp-check:
	@echo "+ $@"
	if [ -n "${IS_UCP}" ]; then \
	  echo "Can not build images with client pointed at UCP bundle" ; \
	  echo "Point client at a host's engine to build." ; \
	  false ; \
	fi

image-name-check:
	@echo "+ $@"
	if [ -z "${IMAGE_NAME}" ]; then \
	  echo "Could not determine OS" ; \
	  echo "Run 'make host-info' for details" ; \
	  false ; \
	fi

dockerfile-check:
	@echo "+ $@"
	if [ -z "${DOCKERFILE}" ]; then \
	  echo "Could not determine OS" ; \
	  echo "Run 'make host-info' for details" ; \
	  false ; \
	fi

.PHONY: version-check
version-check:
	@echo "+ $@"
	if [ -z "${VERSION}" ]; then \
	  echo "VERSION is not set" ; \
	  false ; \
	else \
	  echo "VERSION is ${VERSION}"; \
	fi

.PHONY: branch-check
branch-check:
	@echo "+ $@"
	@echo "git branch is ${GIT_BRANCH}" ; \
	if [ "${GIT_BRANCH}" = 'master' ]; then \
	  echo "Verified on master branch" ; \
	else  \
	  echo "must be on master branch" ; \
	  false ; \
	fi
