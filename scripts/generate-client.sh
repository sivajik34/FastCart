#!/usr/bin/env bash
set -e
set -x

SERVICES_DIR="services"
OPENAPI_DIR="frontend/openapi"

mkdir -p "$OPENAPI_DIR"

generate_schema() {
  local service=$1
  local tmp_file="$OPENAPI_DIR/${service}.json"

  echo "Exporting OpenAPI schema from $service"
  cd "$SERVICES_DIR/$service"

  # Activate virtualenv (Linux/Mac or Windows Git Bash)
  if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
  elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
  fi

  # Load .env if exists
  if [ -f ".env" ]; then
    echo "Loading environment from $service/.env"
    # Export key=value pairs into current shell
    set -o allexport
    source .env
    set +o allexport
  fi

  # Generate OpenAPI schema
  python -c "import app.main, json; print(json.dumps(app.main.app.openapi()))" > "../../$tmp_file"

  deactivate || true
  cd - >/dev/null
}

# Export schemas for each service
generate_schema "user-service"
generate_schema "product-service"
generate_schema "order-service"

# Generate TypeScript clients
cd frontend
# ✅ Ensure openapi-ts is installed
if [ ! -f "node_modules/.bin/openapi-ts" ]; then
  echo "Installing @hey-api/openapi-ts..."
  npm install --save-dev @hey-api/openapi-ts
fi
npm run generate-client
npx biome format --write ./src/client
cd ..
