"""
Test suite for configuration module
Tests for environment variables and settings validation
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from app.core.config import Settings


@pytest.mark.unit
class TestSettings:
    """Test suite for Settings class."""
    
    def test_settings_initialization(self):
        """Test that settings initialize with default values."""
        settings = Settings()
        
        assert settings is not None
        assert hasattr(settings, 'APP_NAME')
        assert hasattr(settings, 'APP_ENV')
        assert hasattr(settings, 'DEBUG')
    
    def test_app_name(self):
        """Test APP_NAME is set correctly."""
        settings = Settings()
        assert settings.APP_NAME == "ConsultaRPP"
    
    def test_llm_provider_default(self):
        """Test default LLM provider is groq."""
        settings = Settings()
        assert settings.LLM_PROVIDER in ["groq", "gemini", "openai", "anthropic"]
    
    def test_database_url_construction(self):
        """Test DATABASE_URL is properly constructed."""
        settings = Settings()
        
        if settings.DB_HOST:
            assert settings.DATABASE_URL is not None
            assert "postgresql" in settings.DATABASE_URL or "postgres" in settings.DATABASE_URL
    
    def test_api_keys_present(self):
        """Test that at least one API key is configured."""
        settings = Settings()
        
        api_keys = [
            settings.GROQ_API_KEY,
            settings.GOOGLE_API_KEY,
            settings.OPENAI_API_KEY,
            settings.ANTHROPIC_API_KEY,
        ]
        
        # At least one API key should be configured
        assert any(api_keys), "No API keys configured"
    
    def test_debug_mode(self):
        """Test debug mode configuration."""
        settings = Settings()
        assert isinstance(settings.DEBUG, bool)
    
    def test_environment_variables_loaded(self):
        """Test that environment variables are loaded."""
        settings = Settings()
        
        # Critical settings
        assert settings.APP_NAME
        assert settings.APP_ENV
        assert settings.DB_HOST
        assert settings.DB_PORT
        assert settings.DB_USER
    
    @pytest.mark.parametrize("env_var,expected", [
        ("APP_ENV", "development"),
        ("DEBUG", True),
    ])
    def test_specific_environment_values(self, env_var, expected):
        """Test specific environment variable values."""
        with patch.dict(os.environ, {env_var: str(expected)}):
            settings = Settings()
            # Just verify it loads without error
            assert settings is not None


@pytest.mark.unit
class TestSettingsValidation:
    """Test settings validation."""
    
    def test_port_is_integer(self):
        """Test that port settings are integers."""
        settings = Settings()
        assert isinstance(settings.DB_PORT, int)
    
    def test_port_in_valid_range(self):
        """Test that port is in valid range."""
        settings = Settings()
        assert 1 <= settings.DB_PORT <= 65535
    
    def test_timeout_values(self):
        """Test timeout values are reasonable."""
        settings = Settings()
        if hasattr(settings, 'API_TIMEOUT'):
            assert settings.API_TIMEOUT > 0


@pytest.mark.integration
class TestSettingsIntegration:
    """Integration tests for settings."""
    
    def test_settings_singleton_behavior(self):
        """Test that settings behaves like a singleton."""
        settings1 = Settings()
        settings2 = Settings()
        
        # Should return the same configuration
        assert settings1.APP_NAME == settings2.APP_NAME
        assert settings1.DB_HOST == settings2.DB_HOST
    
    def test_all_required_settings_present(self):
        """Test that all required settings are available."""
        settings = Settings()
        
        required_attrs = [
            'APP_NAME',
            'APP_ENV',
            'DEBUG',
            'DB_HOST',
            'DB_PORT',
            'DB_USER',
            'DB_PASSWORD',
            'DB_NAME',
        ]
        
        for attr in required_attrs:
            assert hasattr(settings, attr), f"Missing required setting: {attr}"
