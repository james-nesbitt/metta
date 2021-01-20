FROM alpine:3.13

ARG MTT_UID=1000

RUN apk add git curl python3 py3-pip terraform>0.14.0
RUN pip install pytest

RUN adduser --uid=$MTT_UID --disabled-password mtt
USER mtt
ENV PATH="$PATH:/home/mtt/.local/bin"
RUN mkdir -p /home/mtt/.local/bin \
 && curl -Ls -o /home/mtt/.local/bin/launchpad https://github.com/Mirantis/launchpad/releases/download/1.1.1/launchpad-linux-x64 \
 && chmod u+x /home/mtt/.local/bin/launchpad
COPY --chown=mtt ./ /mtt_source

RUN pip install --user --no-cache-dir /mtt_source

WORKDIR "/home/mtt"
ENTRYPOINT ["pytest"]
