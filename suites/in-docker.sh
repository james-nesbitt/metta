

docker run --rm -ti -e REGISTRY_PASSWORD -e REGISTRY_USERNAME -e AWS_ACCESS_KEY_ID -e AWS_SECRET_ACCESS_KEY -e AWS_SESSION_TOKEN -e AWS_PAGER -v "$(pwd):/work" -w "/work" jamesnmirantis/dockerized-builds:0.1.9
