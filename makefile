ENV ?= LOCAL  # Allow ENV to be overridden (defaults 
# Run JWK fingerprint preparation and convert Excel to JSON based on ENV
generate-krakend-json:
	python scripts/krakend_json_generator.py

# Helper command to prepare and convert for Local environment
generate-krakend-json-local:
	$(MAKE) generate-krakend-json ENV=LOCAL

# Helper command to prepare and convert for Development environment
generate-krakend-json-dev:
	$(MAKE) generate-krakend-json ENV=DEV

# Helper command to prepare and convert for Production environment
generate-krakend-json-prod:
	$(MAKE) generate-krakend-json ENV=PROD

# Helper commmand to prepare and convert for All environment
generate-krakend-json-all:
	$(MAKE) generate-krakend-json-local generate-krakend-json-dev generate-krakend-json-prod
