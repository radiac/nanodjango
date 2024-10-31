#!/bin/bash
set -eox pipefail

# We can't (yet) let pytest collect all the modules, since
# we can't instantiate nanodjango.Django more than once (due to
# django-ninja).
for module in "counter" "hello_async" "hello_world"; do
  echo "Test $module"
  nanodjango manage ${module}.py makemigrations ${module}
  pytest ${module}.py --cov-append
done
