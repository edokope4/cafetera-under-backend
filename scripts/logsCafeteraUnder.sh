#!/bin/bash
docker logs -f $(docker ps | grep cafeteraUnder | awk '{print $1}')
