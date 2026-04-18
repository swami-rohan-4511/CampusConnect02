#!/bin/bash

cd /home/runner/workspace/backend/api-gateway && python main.py &
BACKEND_PID=$!

sleep 2

cd /home/runner/workspace/frontend && npm start &
FRONTEND_PID=$!

wait $FRONTEND_PID $BACKEND_PID
