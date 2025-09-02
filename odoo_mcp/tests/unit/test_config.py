"""Unit tests for configuration handling."""

import pytest
import os
from pathlib import Path
from unittest.mock import patch, mock_open
import json
import yaml

from odoo_mcp.config import (
    Config,
    ServerConfig,
    SecurityConfig,
    ConnectionConfig,
    load_config,
    load_from_env,
    load_from_file,
    validate_config,
    ConfigError,
)


class TestConfigStructures:
    """Test configuration data structures."""

    def test_server_config_defaults(self) -> None:
        """Test ServerConfig with default values."""
        config = ServerConfig()
        
        assert config.host == "localhost"
        assert config.port == 3000
        assert config.log_level == "INFO"
        assert config.max_connections == 100
        assert config.timeout == 30

    def test_server_config_custom(self) -> None:
        """Test ServerConfig with custom values."""
        config = ServerConfig(
            host="0.0.0.0",
            port=8080,
            log_level="DEBUG",
            max_connections=50,
            timeout=60,
        )
        
        assert config.host == "0.0.0.0"
        assert config.port == 8080
        assert config.log_level == "DEBUG"
        assert config.max_connections == 50
        assert config.timeout == 60

    def test_security_config(self) -> None:
        """Test SecurityConfig."""
        config = SecurityConfig(
            enable_tls=True,
            tls_cert_path="/path/to/cert.pem",
            tls_key_path="/path/to/key.pem",
            api_key_header="X-API-Key",
            enable_auth=True,
        )
        
        assert config.enable_tls is True
        assert config.tls_cert_path == "/path/to/cert.pem"
        assert config.tls_key_path == "/path/to/key.pem"
        assert config.api_key_header == "X-API-Key"
        assert config.enable_auth is True

    def test_connection_config(self) -> None:
        """Test ConnectionConfig."""
        config = ConnectionConfig(
            instance_id="production",
            url="https://odoo.example.com",
            database="prod_db",
            username="admin",
            password="secret",
            timeout=45,
            max_connections=20,
        )
        
        assert config.instance_id == "production"
        assert config.url == "https://odoo.example.com"
        assert config.database == "prod_db"
        assert config.username == "admin"
        assert config.password == "secret"
        assert config.timeout == 45
        assert config.max_connections == 20

    def test_main_config(self) -> None:
        """Test main Config structure."""
        server = ServerConfig(port=8080)
        security = SecurityConfig(enable_auth=True)
        connections = [
            ConnectionConfig(
                instance_id="prod",
                url="https://prod.odoo.com",
                database="prod",
                username="admin",
                password="secret",
            )
        ]
        
        config = Config(
            server=server,
            security=security,
            connections=connections,
        )
        
        assert config.server.port == 8080
        assert config.security.enable_auth is True
        assert len(config.connections) == 1
        assert config.connections[0].instance_id == "prod"


class TestConfigLoading:
    """Test configuration loading from various sources."""

    def test_load_from_env_server_config(self) -> None:
        """Test loading server config from environment variables."""
        env_vars = {
            "MCP_SERVER_HOST": "0.0.0.0",
            "MCP_SERVER_PORT": "8080",
            "MCP_LOG_LEVEL": "DEBUG",
            "MCP_MAX_CONNECTIONS": "50",
            "MCP_TIMEOUT": "60",
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_from_env()
            
            assert config.server.host == "0.0.0.0"
            assert config.server.port == 8080
            assert config.server.log_level == "DEBUG"
            assert config.server.max_connections == 50
            assert config.server.timeout == 60

    def test_load_from_env_security_config(self) -> None:
        """Test loading security config from environment variables."""
        env_vars = {
            "MCP_ENABLE_TLS": "true",
            "MCP_TLS_CERT_PATH": "/certs/cert.pem",
            "MCP_TLS_KEY_PATH": "/certs/key.pem",
            "MCP_API_KEY_HEADER": "Authorization",
            "MCP_ENABLE_AUTH": "true",
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_from_env()
            
            assert config.security.enable_tls is True
            assert config.security.tls_cert_path == "/certs/cert.pem"
            assert config.security.tls_key_path == "/certs/key.pem"
            assert config.security.api_key_header == "Authorization"
            assert config.security.enable_auth is True

    def test_load_from_env_connections(self) -> None:
        """Test loading connection configs from environment variables."""
        env_vars = {
            "ODOO_CONNECTIONS": "prod,staging",
            "ODOO_PROD_URL": "https://prod.odoo.com",
            "ODOO_PROD_DATABASE": "production",
            "ODOO_PROD_USERNAME": "prod_user",
            "ODOO_PROD_PASSWORD": "prod_pass",
            "ODOO_STAGING_URL": "https://staging.odoo.com",
            "ODOO_STAGING_DATABASE": "staging",
            "ODOO_STAGING_USERNAME": "staging_user",
            "ODOO_STAGING_PASSWORD": "staging_pass",
        }
        
        with patch.dict(os.environ, env_vars):
            config = load_from_env()
            
            assert len(config.connections) == 2
            
            prod = next(c for c in config.connections if c.instance_id == "prod")
            assert prod.url == "https://prod.odoo.com"
            assert prod.database == "production"
            assert prod.username == "prod_user"
            assert prod.password == "prod_pass"
            
            staging = next(c for c in config.connections if c.instance_id == "staging")
            assert staging.url == "https://staging.odoo.com"
            assert staging.database == "staging"
            assert staging.username == "staging_user"
            assert staging.password == "staging_pass"

    def test_load_from_json_file(self) -> None:
        """Test loading config from JSON file."""
        json_content = {
            "server": {
                "host": "0.0.0.0",
                "port": 8080,
                "log_level": "DEBUG",
            },
            "security": {
                "enable_auth": True,
            },
            "connections": [
                {
                    "instance_id": "main",
                    "url": "https://odoo.example.com",
                    "database": "main_db",
                    "username": "admin",
                    "password": "secret",
                }
            ],
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(json_content))):
            with patch("pathlib.Path.exists", return_value=True):
                config = load_from_file("config.json")
            
            assert config.server.host == "0.0.0.0"
            assert config.server.port == 8080
            assert config.security.enable_auth is True
            assert len(config.connections) == 1
            assert config.connections[0].instance_id == "main"

    def test_load_from_yaml_file(self) -> None:
        """Test loading config from YAML file."""
        yaml_content = """
        server:
          host: 0.0.0.0
          port: 8080
          log_level: DEBUG
        security:
          enable_auth: true
        connections:
          - instance_id: main
            url: https://odoo.example.com
            database: main_db
            username: admin
            password: secret
        """
        
        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with patch("pathlib.Path.exists", return_value=True):
                config = load_from_file("config.yaml")
            
            assert config.server.host == "0.0.0.0"
            assert config.server.port == 8080
            assert config.security.enable_auth is True
            assert len(config.connections) == 1
            assert config.connections[0].instance_id == "main"

    def test_load_config_precedence(self) -> None:
        """Test config loading precedence (env > file > defaults)."""
        # File config
        file_config = {
            "server": {
                "host": "127.0.0.1",
                "port": 3000,
            },
        }
        
        # Env config (should override file)
        env_vars = {
            "MCP_SERVER_PORT": "8080",
        }
        
        with patch("builtins.open", mock_open(read_data=json.dumps(file_config))):
            with patch.dict(os.environ, env_vars):
                with patch("os.path.exists", return_value=True):
                    with patch("pathlib.Path.exists", return_value=True):
                        config = load_config("config.json")
                    
                    # Host from file
                    assert config.server.host == "127.0.0.1"
                    # Port from env (overrides file)
                    assert config.server.port == 8080


class TestConfigValidation:
    """Test configuration validation."""

    def test_validate_valid_config(self) -> None:
        """Test validation of valid configuration."""
        config = Config(
            server=ServerConfig(),
            security=SecurityConfig(),
            connections=[
                ConnectionConfig(
                    instance_id="main",
                    url="https://odoo.example.com",
                    database="db",
                    username="user",
                    password="pass",
                )
            ],
        )
        
        # Should not raise
        validate_config(config)

    def test_validate_invalid_port(self) -> None:
        """Test validation with invalid port."""
        config = Config(
            server=ServerConfig(port=70000),  # Invalid port
            security=SecurityConfig(),
            connections=[],
        )
        
        with pytest.raises(ConfigError, match="Invalid port"):
            validate_config(config)

    def test_validate_missing_connections(self) -> None:
        """Test validation with no connections."""
        config = Config(
            server=ServerConfig(),
            security=SecurityConfig(),
            connections=[],
        )
        
        with pytest.raises(ConfigError, match="No connections configured"):
            validate_config(config)

    def test_validate_duplicate_instance_ids(self) -> None:
        """Test validation with duplicate instance IDs."""
        config = Config(
            server=ServerConfig(),
            security=SecurityConfig(),
            connections=[
                ConnectionConfig(
                    instance_id="main",
                    url="https://odoo1.com",
                    database="db1",
                    username="user",
                    password="pass",
                ),
                ConnectionConfig(
                    instance_id="main",  # Duplicate
                    url="https://odoo2.com",
                    database="db2",
                    username="user",
                    password="pass",
                ),
            ],
        )
        
        with pytest.raises(ConfigError, match="Duplicate instance_id"):
            validate_config(config)

    def test_validate_tls_config(self) -> None:
        """Test validation of TLS configuration."""
        # TLS enabled but missing cert path
        config = Config(
            server=ServerConfig(),
            security=SecurityConfig(
                enable_tls=True,
                tls_cert_path=None,
                tls_key_path="/path/to/key.pem",
            ),
            connections=[
                ConnectionConfig(
                    instance_id="main",
                    url="https://odoo.com",
                    database="db",
                    username="user",
                    password="pass",
                )
            ],
        )
        
        with pytest.raises(ConfigError, match="TLS enabled but cert_path not provided"):
            validate_config(config)
