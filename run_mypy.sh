#!/usr/bin/env bash
# Script to run mypy from the custom_components directory to avoid module name conflicts
cd custom_components && mypy custom_areas/
