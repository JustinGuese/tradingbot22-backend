#!/bin/bash
docker build -t guestros/tradingbot22-backend:latest --platform linux/amd64 .
docker push guestros/tradingbot22-backend:latest