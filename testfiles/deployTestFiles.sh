#!/bin/bash

kubectl apply -f ephemerator-delete.yaml
kubectl apply -f ephemerator-disabled.yaml
kubectl apply -f ephemerator-ignored.yaml
kubectl apply -f ephemerator-until.yaml
