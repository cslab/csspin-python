# This file is being used for testing the activation script for powershell.
# It checks, whether the environment variables patched into the script are being
# set/unset correctly when activating the environment. It also checks, whether
# the variables being set are actually reset/unset properly when deactivating
# the environment, so that the state before activating equals the state after
# deactivating.

$activate_script = $args


#############################
# Checking the pre-conditions
Write-Host -NoNewline Checking the pre-conditions...........

if ($env:FOO -ne "foo") {
    Write-Host failed
    Write-Host Expected `$env:FOO to have the value `"foo`" instead of `"$env:FOO`"
    exit 1
}

if ($env:BAR -ne "bar") {
    Write-Host failed
    Write-Host Expected `$env:BAR to have the value `"bar`" instead of `"$env:BAR`"
    exit 1
}

Write-Host ok
# Checking the pre-conditions
###############################

###################################
# Checking the env after activating
Write-Host -NoNewline Checking the env after activating.....

& "$activate_script"

if ($env:FOO -ne "c:\tmp\foobar;foo") {
    Write-Host failed
    Write-Host Expected `$env:FOO to have the value `"c:\tmp\foobar`;foo`" instead of `"$env:FOO`"
    exit 1
}

if ($env:BAR -ne $null) {
    Write-Host failed
    Write-Host Expected `$env:BAR to be unset instead of having the value `"$env:BAR`"
    exit 1
}

deactivate

Write-Host ok
# Checking the env after activating
###################################

#####################################
# Checking the env after deactivating
Write-Host -NoNewline Checking the env after deactivating...

if ($env:FOO -ne "foo") {
    Write-Host failed
    Write-Host Expected `$env:FOO to have the value `"foo`" instead of `"$env:FOO`"
    exit 1
}

if ($env:BAR -ne "bar") {
    Write-Host failed
    Write-Host Expected `$env:BAR to have the value `"bar`" instead of `"$env:BAR`"
    exit 1
}

Write-Host ok
# Checking the env after deactivating
#####################################
