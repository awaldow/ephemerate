#!/bin/bash

kubectl patch ephemerators.tessellate.io ephemerator-deleted -p '{"metadata": {"finalizers": []}}' --type merge
kubectl patch ephemerators.tessellate.io ephemerator-disabled -p '{"metadata": {"finalizers": []}}' --type merge
kubectl patch ephemerators.tessellate.io ephemerator-ignored -p '{"metadata": {"finalizers": []}}' --type merge
kubectl patch ephemerators.tessellate.io ephemerator-until -p '{"metadata": {"finalizers": []}}' --type merge
kubectl patch ephemerators.tessellate.io ephemerator-deleted -p '{"metadata": {"finalizers": []}}' --type merge
helm uninstall ephemerate