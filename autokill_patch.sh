#!/usr/bin/env bash
# A workaround to kill every event based deployment after 30 mintues - a
# workaround for deployments which are not receiving events after some time.
#
# Arguments for test deployment:
# graph-sync-scheduler-thoth-amun-inspection graph-sync-scheduler-thoth-test-core workload-operator-thoth-amun-inspection workload-operator-thoth-test-core
#
# Arguments for stage deployment - frontend:
# graph-sync-scheduler-thoth-backend-stage graph-sync-scheduler-thoth-middletier-stage workload-operator-thoth-backend-stage workload-operator-thoth-middletier-stage
#
# Arguments for stage deployment - amun-api:
# graph-sync-scheduler-thoth-amun-inspection-stage workload-operator-thoth-amun-inspection-stage

for item in "$@"
do
    oc set probe dc/$item --liveness --open-tcp=80 --initial-delay-seconds=1800  --failure-threshold=1
done
