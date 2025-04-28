import os
import json
import re
import pandas as pd
import glob

# Constants
DEFAULT_ENV = 'DEV'

# used directories
CONFIG_DIR = '../config'
BASE_MAPPING_API_DIR = '../mapping/api/base'
BASE_MAPPING_HOST_DIR = '../mapping/host/base'
RESULT_DIR = '../result'

# config files
KRAKEND_CONFIG_FILE = 'krakend_config.json'
EXTRA_CONFIG_FILE = 'krakend_extra_config.json'
ENDPOINT_AUTH_CONFIG_FILE = 'endpoint_auth_config.json'
SERVICE_HOST_MAPPING_FILE = 'services.json'
ORIGIN_ALLOW_LIST_FILE = 'krakend_origin_allow_list.json'

# Get environment variable
ENV = os.environ.get('ENV', DEFAULT_ENV)

def load_json_files(directory):
    """Load and parse all JSON files in a directory."""
    json_files = glob.glob(os.path.join(directory, "*.json"))
    all_data = []

    for json_file in json_files:
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
                all_data.extend(data)  # Combine data from all files
                print(f"[INFO] Successfully loaded: {json_file}")
        except Exception as e:
            print(f"[ERROR] Failed to load {json_file}: {e}")
    
    return all_data

def get_path(*args):
    """Utility function to build file paths."""
    return os.path.join(os.path.dirname(__file__), *args)

def create_result_dir(env):
    """Create result directory for the environment."""
    result_path = get_path(RESULT_DIR, env)
    os.makedirs(result_path, exist_ok=True)
    return result_path

def load_json_config(base_path, env_path):
    """Load JSON configuration with fallback to base if env-specific file is missing."""
    file_path = env_path if os.path.exists(env_path) else base_path
    with open(file_path, 'r') as f:
        return json.load(f)

def load_service_host_mapping(mapping_file):
    """Load service-host mapping from a JSON file."""
    with open(mapping_file, 'r') as f:
        return json.load(f)

def process_query_params(param_string):
    """Process query parameters into a list of keys."""
    params = []
    if pd.notna(param_string):
        param_string = param_string.lstrip('?')
        if param_string:
            for param in param_string.split('&'):
                key = param.split('=', 1)[0].strip()
                if key:
                    params.append(key)
    return params

def convert_path_variables(path):
    """Convert :param to {param} in endpoint paths."""
    return re.sub(r':([a-zA-Z0-9_-]+)', r'{\1}', path)

def load_allow_origins(env_path):
    """Load allow_origins from the environment-specific configuration."""
    origin_file = get_path(env_path, ORIGIN_ALLOW_LIST_FILE)
    if os.path.exists(origin_file):
        with open(origin_file, 'r') as f:
            return json.load(f).get("allow_origins", [])
    return []

def process_endpoint_data(json_data, services_host_mapping, processed_endpoints, unique_methods, unique_headers):
    """Process endpoint data and build the endpoint configuration."""
    endpoints = []

    for row in json_data:
        if pd.isna(row['service']) or pd.isna(row['method']) or pd.isna(row['path']):
            print(f"Skipping row with missing required fields: {row}")
            continue

        service_name, method, path = row.get('service'), row.get('method'), row.get('path')
        headers, params = [], process_query_params(row['params'])

        unique_methods.add(method)  # Track unique methods

        if pd.notna(row['header']):
            for header in row['header'].split(','):
                header_key = header.split(':')[0].strip()
                if header_key:
                    headers.append(header_key)
                    unique_headers.add(header_key)

        # Sort headers alphabetically
        headers = sorted(headers)

        endpoint_path = f"/{service_name}{path}" if service_name not in ['we', 'ne'] else path
        endpoint_path = convert_path_variables(endpoint_path)
        url_pattern = convert_path_variables(path)

        endpoint_key = (endpoint_path, method)

        if endpoint_key in processed_endpoints:
            existing_endpoint = processed_endpoints[endpoint_key]
            existing_endpoint['input_query_strings'].extend(params)
            existing_endpoint['input_headers'].extend(headers)

            # Remove duplicates and sort
            existing_endpoint['input_query_strings'] = sorted(list(set(existing_endpoint['input_query_strings'])))
            existing_endpoint['input_headers'] = sorted(list(set(existing_endpoint['input_headers'])))

            print(f"[INFO] Appending params and headers to existing endpoint: {endpoint_key}")
        else:
            backend = {
                "url_pattern": url_pattern,
                "encoding": row['encoding_type'],
                "sd": "static",
                "method": method,
                "disable_host_sanitize": False,
                "host": [services_host_mapping.get(service_name, 'http://default-service.example.com')]
            }

            # Sort query strings alphabetically
            params = sorted(params)

            endpoint = {
                "endpoint": endpoint_path,
                "method": method,
                "output_encoding": row['encoding_type'],
                "backend": [backend],
                "input_headers": headers,
                "input_query_strings": params,
                "extra_config": endpoint_auth_config if 'Authorization' in headers else {}
            }

            # Debug log before appending
            print(f"[DEBUG] Preparing to append endpoint: {endpoint_key}")
            print(f"[DEBUG] Endpoint details: {endpoint}")

            endpoints.append(endpoint)  # Append to endpoints
            processed_endpoints[endpoint_key] = endpoint  # Add to processed_endpoints

            # Validation log
            if endpoint in endpoints:
                print(f"[DEBUG] Successfully appended endpoint: {endpoint_key}")
            else:
                print(f"[ERROR] Failed to append endpoint: {endpoint_key}")

            print(f"[INFO] Added new endpoint: {endpoint_key}")
            print(f"[INFO] Current endpoint value: {processed_endpoints[endpoint_key]}")

    return endpoints

# Paths
base_config_path = get_path(CONFIG_DIR, 'base')
env_config_path = get_path(CONFIG_DIR, ENV)
result_path = create_result_dir(ENV)

# Load configurations
krakend_config = load_json_config(
    get_path(base_config_path, KRAKEND_CONFIG_FILE),
    get_path(env_config_path, KRAKEND_CONFIG_FILE)
)
extra_config = load_json_config(
    get_path(base_config_path, EXTRA_CONFIG_FILE),
    get_path(env_config_path, EXTRA_CONFIG_FILE)
)
endpoint_auth_config = load_json_config(
    get_path(base_config_path, ENDPOINT_AUTH_CONFIG_FILE),
    get_path(env_config_path, ENDPOINT_AUTH_CONFIG_FILE)
)

# Load allow_origins for CORS from environment-specific configuration
allow_origins = load_allow_origins(env_config_path)
extra_config["security/cors"]["allow_origins"] = allow_origins

# Load service-host mapping
service_host_mapping = load_service_host_mapping(get_path(BASE_MAPPING_HOST_DIR, SERVICE_HOST_MAPPING_FILE))

# Process API endpoints
json_data = load_json_files(get_path(BASE_MAPPING_API_DIR))
processed_endpoints = {}
all_endpoints, all_methods, all_headers = [], set(), set()

endpoints = process_endpoint_data(json_data, service_host_mapping, processed_endpoints, all_methods, all_headers)
all_endpoints.extend(endpoints)

krakend_config['endpoints'] = all_endpoints

# Update CORS and extra_config
extra_config["security/cors"]["allow_methods"] = sorted(list(all_methods))
extra_config["security/cors"]["allow_headers"] = sorted(list(all_headers))
krakend_config['extra_config'] = extra_config

# Write the final configuration to a file
krakend_file_path = os.path.join(result_path, 'krakend.json')
with open(krakend_file_path, 'w') as f:
    json.dump(krakend_config, f, indent=4)

print(f"KrakenD configuration for {ENV} environment generated successfully.")