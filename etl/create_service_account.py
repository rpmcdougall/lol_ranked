#!/usr/bin/env python3
"""
Google Cloud Service Account JSON Generator
Creates a service account JSON file from environment variables for authentication.
This script allows you to store service account credentials as environment variables
and generate the JSON file at runtime, avoiding the need to store credentials in files.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_service_account_data() -> Optional[Dict[str, Any]]:
    """
    Build service account JSON structure from environment variables
    
    Returns:
        Dictionary containing service account data or None if required fields are missing
    """
    # Required fields for service account JSON
    required_fields = {
        'type': 'GCLOUD_TYPE',
        'project_id': 'GCLOUD_PROJECT_ID',
        'private_key_id': 'GCLOUD_PRIVATE_KEY_ID',
        'private_key': 'GCLOUD_PRIVATE_KEY',
        'client_email': 'GCLOUD_CLIENT_EMAIL',
        'client_id': 'GCLOUD_CLIENT_ID',
        'auth_uri': 'GCLOUD_AUTH_URI',
        'token_uri': 'GCLOUD_TOKEN_URI',
        'auth_provider_x509_cert_url': 'GCLOUD_AUTH_PROVIDER_X509_CERT_URL',
        'client_x509_cert_url': 'GCLOUD_CLIENT_X509_CERT_URL'
    }
    
    # Optional fields with defaults
    optional_fields = {
        'universe_domain': 'GCLOUD_UNIVERSE_DOMAIN'
    }
    
    service_account_data = {}
    
    # Check required fields
    missing_fields = []
    for json_key, env_var in required_fields.items():
        value = os.getenv(env_var)
        if not value:
            missing_fields.append(env_var)
        else:
            service_account_data[json_key] = value
    
    if missing_fields:
        logger.error(f"Missing required environment variables: {', '.join(missing_fields)}")
        logger.error("Please set all required GCLOUD_* environment variables")
        return None
    
    # Add optional fields with defaults
    for json_key, env_var in optional_fields.items():
        value = os.getenv(env_var)
        if value:
            service_account_data[json_key] = value
        else:
            # Set default values for optional fields
            if json_key == 'universe_domain':
                service_account_data[json_key] = 'googleapis.com'
    
    return service_account_data

def create_service_account_file(output_path: str = "service-account.json") -> bool:
    """
    Create service account JSON file from environment variables
    
    Args:
        output_path: Path where to save the service account JSON file
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get service account data from environment variables
        service_account_data = get_service_account_data()
        
        if not service_account_data:
            logger.error("Failed to get service account data from environment variables")
            return False
        
        # Create output directory if it doesn't exist
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            logger.info(f"Created directory: {output_dir}")
        
        # Write service account JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(service_account_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully created service account file: {output_path}")
        
        # Set restrictive permissions (read/write for owner only)
        os.chmod(output_path, 0o600)
        logger.info(f"Set restrictive permissions on {output_path}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating service account file: {e}")
        return False

def validate_service_account_data(data: Dict[str, Any]) -> bool:
    """
    Validate service account data structure
    
    Args:
        data: Service account data dictionary
        
    Returns:
        bool: True if valid, False otherwise
    """
    required_keys = [
        'type', 'project_id', 'private_key_id', 'private_key',
        'client_email', 'client_id', 'auth_uri', 'token_uri',
        'auth_provider_x509_cert_url', 'client_x509_cert_url'
    ]
    
    for key in required_keys:
        if key not in data:
            logger.error(f"Missing required key: {key}")
            return False
        
        if not data[key]:
            logger.error(f"Empty value for required key: {key}")
            return False
    
    # Validate specific fields
    if data['type'] != 'service_account':
        logger.error("Type must be 'service_account'")
        return False
    
    if not data['private_key'].startswith('-----BEGIN PRIVATE KEY-----'):
        logger.error("Invalid private key format")
        return False
    
    if not data['client_email'].endswith('.gserviceaccount.com'):
        logger.warning("Client email should end with .gserviceaccount.com")
    
    return True

def main():
    """Main function to create service account JSON file"""
    logger.info("Google Cloud Service Account JSON Generator")
    logger.info("=" * 50)
    
    # Check if we're in a git repository and warn about credentials
    if os.path.exists('.git'):
        logger.warning("⚠️  WARNING: You are in a git repository!")
        logger.warning("Make sure service-account.json is in your .gitignore file")
        logger.warning("Never commit service account credentials to version control")
    
    # Get output path from environment or use default
    output_path = os.getenv('GCLOUD_CREDENTIALS_PATH', 'service-account.json')
    
    # Create the service account file
    success = create_service_account_file(output_path)
    
    if success:
        logger.info("✅ Service account file created successfully!")
        logger.info(f"📁 File location: {output_path}")
        logger.info("🔐 File permissions set to 600 (owner read/write only)")
        
        # Validate the created file
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if validate_service_account_data(data):
                logger.info("✅ Service account data validation passed")
            else:
                logger.error("❌ Service account data validation failed")
                return 1
                
        except Exception as e:
            logger.error(f"❌ Error validating service account file: {e}")
            return 1
        
        # Set environment variable for the ETL script
        os.environ['GCLOUD_CREDENTIALS_PATH'] = output_path
        logger.info(f"🔧 Set GCLOUD_CREDENTIALS_PATH={output_path}")
        
        return 0
    else:
        logger.error("❌ Failed to create service account file")
        return 1

if __name__ == "__main__":
    exit(main()) 