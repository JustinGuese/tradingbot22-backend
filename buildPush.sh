#!/bin/bash
docker buildx build -t guestros/tradingbot22-backend:latest --platform linux/amd64,linux/arm64 --push .