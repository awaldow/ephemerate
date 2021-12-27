#!/bin/bash

scriptRoot=$(pwd)
cd ../Ephemerator
docker build -t local/ephemerator:latest .
cd $scriptRoot