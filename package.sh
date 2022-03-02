#!/bin/bash

# Save the current directory
current_dir=$(pwd)
# We'll assume pip packages are already installed in this venv
rm ${current_dir}/function.zip

# Change to vemv
cd ${current_dir}/venv/Lib/site-packages
# Zip everything up
zip -9 -r ${current_dir}/function.zip .
# cd back to that current directory
cd ${current_dir}
# Add our shell script to the zip
zip -g ${current_dir}/function.zip main.py

# Now function.zip will have the entire deployment package.