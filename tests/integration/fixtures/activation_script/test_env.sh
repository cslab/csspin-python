#! /bin/bash
# This file is being used for testing the activation script for bash.
# It checks, whether the environment variables patched into the script are being
# set/unset correctly when activating the environment. It also checks, whether
# the variables being set are actually reset/unset properly when deactivating
# the environment, so that the state before activating equals the state after
# deactivating.

###############################
# Checking the pre-conditions
echo -n Checking the pre-conditions...........

if [[ "${FOO}" != "foo" ]]; then
    echo failed
    echo Expected \${FOO} to have the value \"foo\" instead of \"${FOO}\"
    exit 1
fi

if [[ "${BAR}" != "bar" ]]; then
    echo failed
    echo Expected \${BAR} to have the value \"bar\" instead of \"${BAR}\"
    exit 1
fi

echo ok
# Checking the pre-conditions
###############################

###################################
# Checking the env after activating
echo -n Checking the env after activating.....

source "$1"
if [[ "${FOO}" != "/tmp/foobar:foo" ]]; then
    echo failed
    echo Expected \${FOO} to have the value \"/tmp/foobar:foo\" instead of \"${FOO}\"
    exit 1
fi

if [[ -n ${BAR} ]]; then
    echo failed
    echo Expected \${BAR} to be unset instead of having the value \"${BAR}\"
    exit 1
fi
deactivate

echo ok
# Checking the env after activating
###################################

#####################################
# Checking the env after deactivating
echo -n Checking the env after deactivating...

if [[ "${FOO}" != "foo" ]]; then
    echo failed
    echo Expected \${FOO} to have the value \"foo\" instead of \"${FOO}\"
    exit 1
fi

if [[ "${BAR}" != "bar" ]]; then
    echo failed
    echo Expected \${BAR} to have the value \"bar\" instead of \"${BAR}\"
    exit 1
fi

echo ok
# Checking the env after deactivating
#####################################
