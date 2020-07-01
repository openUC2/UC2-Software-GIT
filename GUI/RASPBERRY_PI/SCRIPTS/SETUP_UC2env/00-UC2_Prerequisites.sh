#!/bin/bash

echo [UC2] Loading variables...
USER_HOME_DIR="/home/$USER"
WORKING_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ARCHITECTURE=$(uname -m)
UC2_ENVIRONMENT_NAME="UC2env"
