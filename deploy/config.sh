#!/usr/bin/env bash
# Deployment configuration for Real-time-chess-battle.
# Source this file in other deploy scripts: source "$(dirname "$0")/config.sh"
#
# This file is tracked in git — do NOT put secrets here.
# Put secrets in deploy/.env (gitignored). See deploy/.env.example.

# Number of uvicorn worker processes
NUM_WORKERS=2

# Where the repo is cloned on the server
DEPLOY_DIR=/var/www/real-time-chess-battle

# Domain name (used in Caddyfile)
DOMAIN=real-time-chess-battle.example.com

# Git remote
REPO_URL=https://github.com/paladin8/kfchess-cc.git
BRANCH=main
