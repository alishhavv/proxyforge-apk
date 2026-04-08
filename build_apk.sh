#!/bin/bash

# Navigate to the directory containing the buildozer.spec file
cd "$(dirname "$0")"

# Clean previous builds
echo "Cleaning previous builds..."
buildozer android clean
if [ $? -ne 0 ]; then
    echo "Error during cleanup. Exiting."
    exit 1
fi

# Build the APK
echo "Building the APK..."
buildozer android debug
if [ $? -ne 0 ]; then
    echo "Error during APK build. Exiting."
    exit 1
fi

echo "APK build completed successfully."