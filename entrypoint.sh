#!/bin/sh

if [ ! -f .env ]; then
  echo "GEMINI_API_KEY=your_default_api_key" > .env
  echo ".env file created with default values."
else
  echo ".env file already exists."
fi

exec "$@"