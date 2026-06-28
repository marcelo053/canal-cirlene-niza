#!/bin/sh
# Cria buckets necessários no MinIO local
set -e

mc alias set local http://minio:9000 minioadmin minioadmin

for bucket in cirlene-audio cirlene-arts cirlene-video cirlene-slides; do
  mc mb --ignore-existing local/$bucket
  mc anonymous set download local/$bucket
  echo "Bucket $bucket ready"
done
