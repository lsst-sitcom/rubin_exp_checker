#!/bin/bash

# go to a subshell
(

# make sure all commands are executed
set -e

# chmod
chmod o+rx .
chmod o+r .htaccess *.html *.shtml *.php.inc
chmod o+rx *.php
chmod -R o+rX assets
chmod -R o+rwX .db

# end subshell
)
