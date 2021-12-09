# Ephemerate

[![lint-v1alpha1](https://github.com/awaldow/ephemerate/actions/workflows/lint-v1alpha1.yml/badge.svg)](https://github.com/awaldow/ephemerate/actions/workflows/lint-v1alpha1.yml)
[![ci-v1alpha1](https://github.com/awaldow/ephemerate/actions/workflows/ci-v1alpha1.yml/badge.svg)](https://github.com/awaldow/ephemerate/actions/workflows/ci-v1alpha1.yml)

This project is designed to allow K8s admins/developers to place lifetimes on
namespaces in their cluster. This is accomplished by an operator and a CRD
defining the parameters for ephemeration. The operator will register the CRD
with the K8s API and then will poll for the Ephemerator custom object on an
interval (in seconds) defined by ```EPHEMERATE_INTERVAL``` in the environment
of the operator's pod. If you want to want to register a Ephemerator but not
activate it, give it the annotation
```'ephmerators.tessellate.io/enabled': 'false'```
and it will be ignored (or you can omit the label altogether). If the
```'ephmerators.tessellate.io/enabled'``` annotation is set to ```'true'```,
the operator will activate the ephemerator.

The operator and custom objects must be cluster scoped. This helps save on
requests to the K8s API to get all the namespaces, as well as saves on the
complexity of watching many different namespaces.

## Defining a lifetime

Lifetimes are defined with either a map of time units and their values, or
as a date/time (24hr)/timezone map. Valid time units are
```[minutes, hours, days, weeks, months, years]```. See the examples below
for more information.

A good list of timezone strings can be seen [here](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568)

### A note about actual vs. expected lifetimes

Because ephemerate occurs on a user defined interval, it is possible that the
actual lifetime of a namespace may be more than the expected/defined lifetime.
This is due to how to timers in kopf get registered and the evaluation
interval. If you define a ```duration``` or ```until``` in the spec that is
less than the evaluation interval, it will get deleted on the next timer
evaluation. It is recommended to set durations in multiples of your evaluation
interval.

## Sample Ephemerators

```yaml
apiVersion: tessellate.io/v1alpha1
kind: Ephemerator
metadata:
    name: my-ephemerator
    annotations:
        ephemerators.tessellate.io/enabled: 'true'
spec:
    namespaceToWatch: my-namespace
    lifetime: 
        duration:
            years: 1
            months: 2
            weeks: 3
            days: 4
            hours: 5
            minutes: 6
```

```yaml
apiVersion: tessellate.io/v1alpha1
kind: Ephemerator
metadata:
    name: my-ephemerator
    annotations:
        ephemerators.tessellate.io/enabled: 'true'
spec:
    namespaceToWatch: thanksgiving
    lifetime: 
        until:
            date: '2021-11-25'
            time: '12:00:00'
            timezone: 'America/Phoenix'
```

## Cleanup

As ephemerate is installed via helm, it should be uninstalled the same way;
the only caveat is that any active ephemerators should be deleted before
uninstalling so that helm can actually delete the CRD for you. Kopf adds
finalizers to the custom objects so kubectl/k8s dashboard/etc. will not be able
to delete them without the operator running.
