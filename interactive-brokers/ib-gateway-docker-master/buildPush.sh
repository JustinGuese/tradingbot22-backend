#!/bin/bash
docker build -t guestros/ib-gateway:latest .
docker push guestros/ib-gateway:latest