#!/usr/bin/env bash

# Schedule inspection on PSI stage environment multiple times.
for i in {0..300}; do
  curl -X POST --header 'Content-Type: application/json' --header 'Accept: application/json' -d @inspection.json 'http://amun-api-thoth-amun-api-stage.cloud.paas.psi.redhat.com/api/v1/inspect'
done
