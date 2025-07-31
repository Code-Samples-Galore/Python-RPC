import pytest
from client import XMLRPCClient
from utils import Data


def _check_xmlrpc_server_availability(url, verify_ssl=False):
    """Check if XML-RPC server is available and responding"""
    try:
        client = XMLRPCClient(url, verify_ssl=verify_ssl)
        return client.test_connection()
    except Exception:
        return False


@pytest.fixture(scope="session", autouse=True)
def check_xmlrpc_server_availability():
    """Check server availability before running tests"""
    print("\nChecking XML-RPC server availability...")

    # Check HTTP server
    if not _check_xmlrpc_server_availability("http://localhost:8000", verify_ssl=False):
        pytest.exit("HTTP XML-RPC server is not available on localhost:8000. Please start the server before running tests.", returncode=1)

    # Check HTTPS server
    if not _check_xmlrpc_server_availability("https://localhost:8443", verify_ssl=False):
        pytest.exit("HTTPS XML-RPC server is not available on localhost:8443. Please start the server before running tests.", returncode=1)

    print("Both XML-RPC servers are available. Proceeding with tests...")


@pytest.fixture
def http_client():
    """Fixture for HTTP client"""
    return XMLRPCClient("http://localhost:8000", verify_ssl=False)


@pytest.fixture
def https_client():
    """Fixture for HTTPS client"""
    return XMLRPCClient("https://localhost:8443", verify_ssl=False)


class TestBasicOperations:
    """Test basic math operations"""

    def test_http_connection(self, http_client):
        """Test HTTP server connection"""
        assert http_client.test_connection()

    def test_https_connection(self, https_client):
        """Test HTTPS server connection"""
        assert https_client.test_connection()

    def test_math_operations_http(self, http_client):
        """Test math operations on HTTP server"""
        # Test addition
        result = http_client.proxy.add(10, 5)
        assert result['result'] == 15
        assert result['response_code'] == 200

        # Test subtraction
        result = http_client.proxy.subtract(10, 5)
        assert result['result'] == 5
        assert result['response_code'] == 200

        # Test multiplication
        result = http_client.proxy.multiply(10, 5)
        assert result['result'] == 50
        assert result['response_code'] == 200

        # Test division
        result = http_client.proxy.divide(10, 5)
        assert result['result'] == 2.0
        assert result['response_code'] == 200

    def test_math_operations_https(self, https_client):
        """Test math operations on HTTPS server"""
        # Test addition
        result = https_client.proxy.add(10, 5)
        assert result['result'] == 15
        assert result['response_code'] == 200

        # Test error handling
        result = https_client.proxy.divide(10, 0)
        assert result['response_code'] == 400
        assert 'error' in result


class TestDataClassOperations:
    """Test operations using Data class"""

    def test_kwargs_operations_http(self, http_client):
        """Test kwargs operations on HTTP server"""
        # Test addition with kwargs
        result = http_client.proxy.add(Data(x=10, y=5))
        assert result['result'] == 15
        assert result['response_code'] == 200

        # Test multiplication with kwargs
        result = http_client.proxy.multiply(Data(x=7, y=6))
        assert result['result'] == 42
        assert result['response_code'] == 200

    def test_args_operations_http(self, http_client):
        """Test args operations on HTTP server"""
        # Test addition with args
        result = http_client.proxy.add(Data(10, 5))
        assert result['result'] == 15
        assert result['response_code'] == 200

        # Test subtraction with args
        result = http_client.proxy.subtract(Data(20, 8))
        assert result['result'] == 12
        assert result['response_code'] == 200

    def test_mixed_operations_http(self, http_client):
        """Test mixed args/kwargs operations on HTTP server"""
        # Test with first arg positional, second as kwarg
        result = http_client.proxy.add(Data(10, y=5))
        assert result['result'] == 15
        assert result['response_code'] == 200

    def test_kwargs_operations_https(self, https_client):
        """Test kwargs operations on HTTPS server"""
        # Test addition with kwargs
        result = https_client.proxy.add(Data(x=10, y=5))
        assert result['result'] == 15
        assert result['response_code'] == 200

        # Test error handling with kwargs
        result = https_client.proxy.divide(Data(x=10, y=0))
        assert result['response_code'] == 400
        assert 'error' in result


class TestErrorHandling:
    """Test error handling scenarios"""

    def test_division_by_zero_http(self, http_client):
        """Test division by zero on HTTP server"""
        result = http_client.proxy.divide(10, 0)
        assert result['response_code'] == 400
        assert 'Cannot divide by zero' in result['error']

    def test_division_by_zero_https(self, https_client):
        """Test division by zero on HTTPS server"""
        result = https_client.proxy.divide(Data(x=15, y=0))
        assert result['response_code'] == 400
        assert 'Cannot divide by zero' in result['error']


class TestIntrospection:
    """Test server introspection capabilities"""

    def test_list_methods_http(self, http_client):
        """Test method listing on HTTP server"""
        methods = http_client.proxy.system.listMethods()
        assert 'add' in methods
        assert 'subtract' in methods
        assert 'multiply' in methods
        assert 'divide' in methods

    def test_list_methods_https(self, https_client):
        """Test method listing on HTTPS server"""
        methods = https_client.proxy.system.listMethods()
        assert 'add' in methods
        assert 'subtract' in methods
        assert 'multiply' in methods
        assert 'divide' in methods


if __name__ == "__main__":
    pytest.main([__file__])
