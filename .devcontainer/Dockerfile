FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    jq \
    vim \
    wget \
    unzip \
    build-essential \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install the AWS CLI v2 from Amazon's installer rather than apt: Ubuntu ships
# v1, and `aws sso login` (docs/deployment.md — credentials come from IAM
# Identity Center, never the repo) is v2-only. Arch-matched so the image builds
# on both Apple silicon and x86 hosts.
RUN ARCH="$(uname -m)" \
    && curl -fsSL "https://awscli.amazonaws.com/awscli-exe-linux-${ARCH}.zip" -o /tmp/awscliv2.zip \
    && unzip -q /tmp/awscliv2.zip -d /tmp \
    && /tmp/aws/install \
    && rm -rf /tmp/awscliv2.zip /tmp/aws

# Install Terraform from HashiCorp's apt repository. Provisions the already-
# decided infra toolchain: infra/ is Terraform per ADR 0006, targeting AWS
# eu-west-2. System-wide on the shared PATH so it is available on first boot.
# The source list and keyring are removed once terraform is installed: a cached
# copy of this layer otherwise carries a stale key into every later
# `apt-get update` (the devcontainer features run one), and HashiCorp rotating
# its signing key (2026-09, now FC9CA96ACA026560) then fails the whole build.
# Upgrading terraform means rebuilding the image, not `apt upgrade`.
RUN wget -O - https://apt.releases.hashicorp.com/gpg | gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg \
    && echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" > /etc/apt/sources.list.d/hashicorp.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends terraform \
    && rm -f /etc/apt/sources.list.d/hashicorp.list /usr/share/keyrings/hashicorp-archive-keyring.gpg \
    && rm -rf /var/lib/apt/lists/*

# Install the GitHub CLI from GitHub's apt repository. Ubuntu's `gh` package is
# absent from 24.04 entirely, and the repo's PR/CI workflow (trunk-based, short
# branches) runs through it. Same shape as the Terraform block above: keyring,
# pinned source list, system-wide on the shared PATH so it is there on first
# boot. Authentication is not baked in — no credential belongs in an image
# (rule 8); `gh auth login` runs once per clone, and its token persists in the
# gh config volume mounted by devcontainer.json.
RUN wget -O - https://cli.github.com/packages/githubcli-archive-keyring.gpg | gpg --dearmor -o /usr/share/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends gh \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js LTS (required for Claude Code)
RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code

# Install uv (system-wide, available to all users)
ENV UV_INSTALL_DIR=/usr/local/bin
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# Graphify (codebase knowledge-graph dev tool) as a system-wide uv tool, so the
# committed /graphify skill works on first boot (ADR 0030). The env vars are
# scoped to this RUN: the `graphify` executable lands on the shared PATH
# (/usr/local/bin) with its venv under /opt, leaving each user's own `uv tool`
# state untouched. Deliberately NOT a project dependency — never in
# backend/pyproject.toml or frontend/package.json.
RUN UV_TOOL_DIR=/opt/uv/tools UV_TOOL_BIN_DIR=/usr/local/bin uv tool install graphifyy

# Let the non-root `vscode` user install global npm packages without sudo.
# Node's global prefix defaults to /usr (root-owned), so a runtime `npm i -g`
# fails with EACCES — e.g. Expo auto-installing @expo/ngrok for `expo start
# --tunnel`. Point the user's npm prefix at a home-dir path they can write to.
ENV NPM_CONFIG_PREFIX=/home/vscode/.npm-global
ENV PATH=/home/vscode/.npm-global/bin:$PATH
RUN mkdir -p /home/vscode/.npm-global \
    && chown -R vscode:vscode /home/vscode/.npm-global

WORKDIR /workspaces/dark_spark
