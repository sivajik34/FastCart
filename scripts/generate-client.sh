#! /usr/bin/env bash

set -e
set -x

SERVICES_DIR="services"
COMBINED_OPENAPI="openapi.json"

# Clean up old combined file
rm -f "$COMBINED_OPENAPI"

# Start combined JSON (basic OpenAPI structure)
echo '{"openapi":"3.0.0","info":{"title":"FastCart API","version":"1.0.0"},"paths":{},"components":{"schemas":{}}}' > "$COMBINED_OPENAPI"

# Merge function (using jq)
merge_openapi() {
  local service=$1
  local tmp_file="${service}-openapi.json"

  echo "Exporting OpenAPI from $service"
  cd "$SERVICES_DIR/$service"

  python -c "import app.main, json; print(json.dumps(app.main.app.openapi()))" > "../../$tmp_file"
  cd - >/dev/null

  echo "Merging $tmp_file into $COMBINED_OPENAPI"
  jq -s '
    reduce .[] as $item ({}; 
      .paths += $item.paths // {} |
      .components.schemas += $item.components.schemas // {}
    ) 
    | .openapi = "3.0.0"
    | .info = {"title":"FastCart API","version":"1.0.0"}
  ' "$COMBINED_OPENAPI" "$tmp_file" > tmp.json && mv tmp.json "$COMBINED_OPENAPI"

  rm "$tmp_file"
}

# Merge all services
merge_openapi "user-service"
merge_openapi "product-service"
merge_openapi "order-service"

# Move final OpenAPI into frontend
mv "$COMBINED_OPENAPI" frontend/

# Generate client
cd frontend
npm run generate-client -- --input openapi.json --output src/client
npx biome format --write ./src/client
cd ..

