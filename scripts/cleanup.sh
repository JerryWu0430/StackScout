#!/bin/bash
set -e

cd frontend
npm run lint
npm run build
