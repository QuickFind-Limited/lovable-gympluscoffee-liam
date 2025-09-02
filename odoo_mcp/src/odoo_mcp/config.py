"""Configuration management for Odoo MCP server."""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


class ConfigError(Exception):
    """Configuration related errors."""
    pass


@dataclass
class ServerConfig:
    """Server configuration."""
    host: str = "localhost"
    port: int = 3000
    log_level: str = "INFO"
    max_connections: int = 100
    timeout: int = 30


@dataclass
class SecurityConfig:
    """Security configuration."""
    enable_tls: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    api_key_header: str = "X-API-Key"
    enable_auth: bool = False


@dataclass
class ConnectionConfig:
    """Odoo connection configuration."""
    instance_id: str
    url: str
    database: str
    username: str
    password: str
    timeout: int = 30
    max_connections: int = 10


@dataclass
class Config:
    """Main configuration container."""
    server: ServerConfig = field(default_factory=ServerConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    connections: List[ConnectionConfig] = field(default_factory=list)


def load_from_env() -> Config:
    """Load configuration from environment variables.
    
    Returns:
        Config object populated from environment
    """
    # Server config
    server = ServerConfig(
        host=os.getenv("MCP_SERVER_HOST", "localhost"),
        port=int(os.getenv("MCP_SERVER_PORT", "3000")),
        log_level=os.getenv("MCP_LOG_LEVEL", "INFO"),
        max_connections=int(os.getenv("MCP_MAX_CONNECTIONS", "100")),
        timeout=int(os.getenv("MCP_TIMEOUT", "30")),
    )
    
    # Security config
    security = SecurityConfig(
        enable_tls=os.getenv("MCP_ENABLE_TLS", "false").lower() == "true",
        tls_cert_path=os.getenv("MCP_TLS_CERT_PATH"),
        tls_key_path=os.getenv("MCP_TLS_KEY_PATH"),
        api_key_header=os.getenv("MCP_API_KEY_HEADER", "X-API-Key"),
        enable_auth=os.getenv("MCP_ENABLE_AUTH", "false").lower() == "true",
    )
    
    # Connection configs
    connections = []
    connection_names = os.getenv("ODOO_CONNECTIONS", "").split(",")
    connection_names = [name.strip() for name in connection_names if name.strip()]
    
    for name in connection_names:
        prefix = f"ODOO_{name.upper()}_"
        
        url = os.getenv(f"{prefix}URL")
        database = os.getenv(f"{prefix}DATABASE")
        username = os.getenv(f"{prefix}USERNAME")
        password = os.getenv(f"{prefix}PASSWORD")
        
        if all([url, database, username, password]):
            # Type narrowing - all() ensures none are None
            assert url is not None
            assert database is not None
            assert username is not None
            assert password is not None
            
            connections.append(ConnectionConfig(
                instance_id=name,
                url=url,
                database=database,
                username=username,
                password=password,
                timeout=int(os.getenv(f"{prefix}TIMEOUT", "30")),
                max_connections=int(os.getenv(f"{prefix}MAX_CONNECTIONS", "10")),
            ))
    
    return Config(
        server=server,
        security=security,
        connections=connections,
    )


def load_from_file(file_path: str) -> Config:
    """Load configuration from a file.
    
    Args:
        file_path: Path to configuration file (JSON or YAML)
        
    Returns:
        Config object populated from file
        
    Raises:
        ConfigError: If file cannot be loaded or parsed
    """
    path = Path(file_path)
    
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {file_path}")
    
    try:
        with open(path, 'r') as f:
            if path.suffix.lower() in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif path.suffix.lower() == '.json':
                data = json.load(f)
            else:
                raise ConfigError(f"Unsupported file format: {path.suffix}")
    except Exception as e:
        raise ConfigError(f"Failed to load configuration: {e}") from e
    
    return _parse_config_dict(data)


def _parse_config_dict(data: Dict[str, Any]) -> Config:
    """Parse configuration dictionary into Config object.
    
    Args:
        data: Configuration dictionary
        
    Returns:
        Config object
    """
    config = Config()
    
    # Parse server config
    if "server" in data:
        server_data = data["server"]
        config.server = ServerConfig(
            host=server_data.get("host", "localhost"),
            port=server_data.get("port", 3000),
            log_level=server_data.get("log_level", "INFO"),
            max_connections=server_data.get("max_connections", 100),
            timeout=server_data.get("timeout", 30),
        )
    
    # Parse security config
    if "security" in data:
        security_data = data["security"]
        config.security = SecurityConfig(
            enable_tls=security_data.get("enable_tls", False),
            tls_cert_path=security_data.get("tls_cert_path"),
            tls_key_path=security_data.get("tls_key_path"),
            api_key_header=security_data.get("api_key_header", "X-API-Key"),
            enable_auth=security_data.get("enable_auth", False),
        )
    
    # Parse connections
    if "connections" in data:
        for conn_data in data["connections"]:
            if all(key in conn_data for key in ["instance_id", "url", "database", "username", "password"]):
                config.connections.append(ConnectionConfig(
                    instance_id=conn_data["instance_id"],
                    url=conn_data["url"],
                    database=conn_data["database"],
                    username=conn_data["username"],
                    password=conn_data["password"],
                    timeout=conn_data.get("timeout", 30),
                    max_connections=conn_data.get("max_connections", 10),
                ))
    
    return config


def load_config(config_file: Optional[str] = None) -> Config:
    """Load configuration with precedence: env > file > defaults.
    
    Args:
        config_file: Optional configuration file path
        
    Returns:
        Merged configuration
    """
    # Start with defaults
    config = Config()
    
    # Load from file if provided
    if config_file and os.path.exists(config_file):
        config = load_from_file(config_file)
    
    # Override with environment variables
    env_config = load_from_env()
    
    # Merge configurations (env takes precedence)
    if env_config.server.host != "localhost":
        config.server.host = env_config.server.host
    if env_config.server.port != 3000:
        config.server.port = env_config.server.port
    if env_config.server.log_level != "INFO":
        config.server.log_level = env_config.server.log_level
    if env_config.server.max_connections != 100:
        config.server.max_connections = env_config.server.max_connections
    if env_config.server.timeout != 30:
        config.server.timeout = env_config.server.timeout
    
    # Merge security settings
    if env_config.security.enable_tls:
        config.security.enable_tls = env_config.security.enable_tls
    if env_config.security.tls_cert_path:
        config.security.tls_cert_path = env_config.security.tls_cert_path
    if env_config.security.tls_key_path:
        config.security.tls_key_path = env_config.security.tls_key_path
    if env_config.security.api_key_header != "X-API-Key":
        config.security.api_key_header = env_config.security.api_key_header
    if env_config.security.enable_auth:
        config.security.enable_auth = env_config.security.enable_auth
    
    # Add env connections if any
    if env_config.connections:
        # Merge by instance_id
        existing_ids = {conn.instance_id for conn in config.connections}
        for conn in env_config.connections:
            if conn.instance_id not in existing_ids:
                config.connections.append(conn)
    
    return config


def validate_config(config: Config) -> None:
    """Validate configuration.
    
    Args:
        config: Configuration to validate
        
    Raises:
        ConfigError: If configuration is invalid
    """
    # Validate port
    if not 1 <= config.server.port <= 65535:
        raise ConfigError(f"Invalid port: {config.server.port}")
    
    # Validate connections
    if not config.connections:
        raise ConfigError("No connections configured")
    
    # Check for duplicate instance IDs
    instance_ids = [conn.instance_id for conn in config.connections]
    if len(instance_ids) != len(set(instance_ids)):
        raise ConfigError("Duplicate instance_id found in connections")
    
    # Validate TLS configuration
    if config.security.enable_tls:
        if not config.security.tls_cert_path:
            raise ConfigError("TLS enabled but cert_path not provided")
        if not config.security.tls_key_path:
            raise ConfigError("TLS enabled but key_path not provided")
    
    # Validate log level
    valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if config.server.log_level.upper() not in valid_log_levels:
        raise ConfigError(f"Invalid log level: {config.server.log_level}")
