FROM golang:1.16.3-alpine AS build

COPY . /go/src/github.com/mirantis/testing-eng/test-apps/n-pods-app

WORKDIR /go/src/github.com/mirantis/testing-eng/test-apps/n-pods-app

ARG VERSION
ARG BUILD_DATE
RUN cd ./app && go build -ldflags "-X main.buildVersion=${VERSION} -X main.buildDate=${BUILD_DATE}" -o /go/bin/n-pods-app .

FROM alpine:3.7
COPY --from=build /go/bin/n-pods-app /usr/local/bin

ENTRYPOINT ["/usr/local/bin/n-pods-app"]
