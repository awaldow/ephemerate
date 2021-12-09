#!/bin/bash

scriptRoot=$(pwd)
cd ../../Ephemerator/v1alpha1
docker build -t local/ephemerator:v1alpha1-latest .
cd $scriptRoot