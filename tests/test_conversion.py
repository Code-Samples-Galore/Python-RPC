import pytest
from utils import convert_value_for_xmlrpc, convert_value_from_xmlrpc, Data


class TestConvertValueForXmlrpc:
    """Test convert_value_for_xmlrpc function"""

    def test_convert_integers(self):
        """Test integer conversion"""
        assert convert_value_for_xmlrpc(42) == "__INT__42"
        assert convert_value_for_xmlrpc(-17) == "__INT__-17"
        assert convert_value_for_xmlrpc(0) == "__INT__0"

    def test_convert_large_integers(self):
        """Test large integer conversion that would exceed XML-RPC limits"""
        large_int = 2**63 + 1000
        result = convert_value_for_xmlrpc(large_int)
        assert result == f"__INT__{large_int}"

    def test_convert_floats(self):
        """Test float conversion"""
        assert convert_value_for_xmlrpc(3.14) == "__FLOAT__3.14"
        assert convert_value_for_xmlrpc(-2.5) == "__FLOAT__-2.5"
        assert convert_value_for_xmlrpc(0.0) == "__FLOAT__0.0"

    def test_convert_large_floats(self):
        """Test large float conversion"""
        large_float = 1.23e100
        result = convert_value_for_xmlrpc(large_float)
        assert result == f"__FLOAT__{large_float}"

    def test_strings_unchanged(self):
        """Test that strings are not converted"""
        assert convert_value_for_xmlrpc("hello") == "hello"
        assert convert_value_for_xmlrpc("123") == "123"
        assert convert_value_for_xmlrpc("__INT__42") == "__INT__42"  # Already a marker
        assert convert_value_for_xmlrpc("") == ""

    def test_other_types_unchanged(self):
        """Test that other types remain unchanged"""
        assert convert_value_for_xmlrpc(None) is None
        assert convert_value_for_xmlrpc(True) is True
        assert convert_value_for_xmlrpc(False) is False

    def test_convert_lists(self):
        """Test list conversion"""
        input_list = [1, 2.5, "hello", 42, True, False]
        expected = ["__INT__1", "__FLOAT__2.5", "hello", "__INT__42", True, False]
        assert convert_value_for_xmlrpc(input_list) == expected

    def test_convert_nested_lists(self):
        """Test nested list conversion"""
        input_list = [1, [2, 3.14, True], ["nested", 5, False]]
        expected = ["__INT__1", ["__INT__2", "__FLOAT__3.14", True], ["nested", "__INT__5", False]]
        assert convert_value_for_xmlrpc(input_list) == expected

    def test_convert_tuples(self):
        """Test tuple conversion"""
        input_tuple = (1, 2.5, "hello", True)
        expected = ["__INT__1", "__FLOAT__2.5", "hello", True]
        result = convert_value_for_xmlrpc(input_tuple)
        assert result == expected
        assert isinstance(result, list)  # Tuples become lists

    def test_convert_dictionaries(self):
        """Test dictionary conversion"""
        input_dict = {"a": 1, "b": 2.5, "c": "hello", "d": True, "e": False}
        expected = {"a": "__INT__1", "b": "__FLOAT__2.5", "c": "hello", "d": True, "e": False}
        assert convert_value_for_xmlrpc(input_dict) == expected

    def test_convert_nested_dictionaries(self):
        """Test nested dictionary conversion"""
        input_dict = {
            "outer": {
                "inner": 42,
                "float_val": 3.14,
                "bool_val": True
            },
            "list": [1, 2, 3, False],
            "string": "unchanged"
        }
        expected = {
            "outer": {
                "inner": "__INT__42",
                "float_val": "__FLOAT__3.14",
                "bool_val": True
            },
            "list": ["__INT__1", "__INT__2", "__INT__3", False],
            "string": "unchanged"
        }
        assert convert_value_for_xmlrpc(input_dict) == expected


class TestConvertValueFromXmlrpc:
    """Test convert_value_from_xmlrpc function"""

    def test_convert_integer_markers(self):
        """Test converting integer markers back to integers"""
        assert convert_value_from_xmlrpc("__INT__42") == 42
        assert convert_value_from_xmlrpc("__INT__-17") == -17
        assert convert_value_from_xmlrpc("__INT__0") == 0

    def test_convert_large_integer_markers(self):
        """Test converting large integer markers"""
        large_int = 2**63 + 1000
        marker = f"__INT__{large_int}"
        assert convert_value_from_xmlrpc(marker) == large_int

    def test_convert_float_markers(self):
        """Test converting float markers back to floats"""
        assert convert_value_from_xmlrpc("__FLOAT__3.14") == 3.14
        assert convert_value_from_xmlrpc("__FLOAT__-2.5") == -2.5
        assert convert_value_from_xmlrpc("__FLOAT__0.0") == 0.0

    def test_convert_large_float_markers(self):
        """Test converting large float markers"""
        large_float = 1.23e100
        marker = f"__FLOAT__{large_float}"
        result = convert_value_from_xmlrpc(marker)
        assert result == large_float

    def test_regular_strings_unchanged(self):
        """Test that regular strings are not converted"""
        assert convert_value_from_xmlrpc("hello") == "hello"
        assert convert_value_from_xmlrpc("123") == "123"
        assert convert_value_from_xmlrpc("") == ""
        assert convert_value_from_xmlrpc("__INVALID__42") == "__INVALID__42"

    def test_partial_markers_unchanged(self):
        """Test that partial markers are treated as regular strings"""
        assert convert_value_from_xmlrpc("__INT") == "__INT"
        assert convert_value_from_xmlrpc("INT__42") == "INT__42"
        assert convert_value_from_xmlrpc("__FLOAT") == "__FLOAT"

    def test_other_types_unchanged(self):
        """Test that other types remain unchanged"""
        assert convert_value_from_xmlrpc(None) is None
        assert convert_value_from_xmlrpc(True) is True
        assert convert_value_from_xmlrpc(False) is False
        assert convert_value_from_xmlrpc(42) == 42  # Already an int

    def test_convert_lists(self):
        """Test list conversion"""
        input_list = ["__INT__1", "__FLOAT__2.5", "hello", "__INT__42", True, False]
        expected = [1, 2.5, "hello", 42, True, False]
        assert convert_value_from_xmlrpc(input_list) == expected

    def test_convert_nested_lists(self):
        """Test nested list conversion"""
        input_list = ["__INT__1", ["__INT__2", "__FLOAT__3.14", True], ["nested", "__INT__5", False]]
        expected = [1, [2, 3.14, True], ["nested", 5, False]]
        assert convert_value_from_xmlrpc(input_list) == expected

    def test_convert_tuples(self):
        """Test tuple conversion"""
        input_tuple = ("__INT__1", "__FLOAT__2.5", "hello", True)
        expected = (1, 2.5, "hello", True)
        result = convert_value_from_xmlrpc(input_tuple)
        assert result == expected
        assert isinstance(result, tuple)  # Preserves tuple type

    def test_convert_dictionaries(self):
        """Test dictionary conversion"""
        input_dict = {"a": "__INT__1", "b": "__FLOAT__2.5", "c": "hello", "d": True, "e": False}
        expected = {"a": 1, "b": 2.5, "c": "hello", "d": True, "e": False}
        assert convert_value_from_xmlrpc(input_dict) == expected

    def test_convert_nested_dictionaries(self):
        """Test nested dictionary conversion"""
        input_dict = {
            "outer": {
                "inner": "__INT__42",
                "float_val": "__FLOAT__3.14",
                "bool_val": True
            },
            "list": ["__INT__1", "__INT__2", "__INT__3", False],
            "string": "unchanged"
        }
        expected = {
            "outer": {
                "inner": 42,
                "float_val": 3.14,
                "bool_val": True
            },
            "list": [1, 2, 3, False],
            "string": "unchanged"
        }
        assert convert_value_from_xmlrpc(input_dict) == expected


class TestRoundTripConversion:
    """Test round-trip conversion (to XML-RPC and back)"""

    def test_roundtrip_integers(self):
        """Test integer round-trip conversion"""
        original = 42
        converted = convert_value_for_xmlrpc(original)
        restored = convert_value_from_xmlrpc(converted)
        assert restored == original
        assert type(restored) == type(original)

    def test_roundtrip_large_integers(self):
        """Test large integer round-trip conversion"""
        original = 2**63 + 1000
        converted = convert_value_for_xmlrpc(original)
        restored = convert_value_from_xmlrpc(converted)
        assert restored == original
        assert type(restored) == type(original)

    def test_roundtrip_floats(self):
        """Test float round-trip conversion"""
        original = 3.141592653589793
        converted = convert_value_for_xmlrpc(original)
        restored = convert_value_from_xmlrpc(converted)
        assert restored == original
        assert type(restored) == type(original)

    def test_roundtrip_strings(self):
        """Test string round-trip conversion (should remain unchanged)"""
        original = "hello world"
        converted = convert_value_for_xmlrpc(original)
        restored = convert_value_from_xmlrpc(converted)
        assert restored == original
        assert type(restored) == type(original)

    def test_roundtrip_complex_structures(self):
        """Test complex structure round-trip conversion"""
        original = {
            "integers": [1, 2, 3],
            "floats": [1.1, 2.2, 3.3],
            "booleans": [True, False],
            "mixed": {
                "int": 42,
                "float": 3.14,
                "string": "unchanged",
                "bool": True,
                "nested": [100, "test", 2.5, False]
            }
        }
        converted = convert_value_for_xmlrpc(original)
        restored = convert_value_from_xmlrpc(converted)
        assert restored == original


class TestDataClassConversion:
    """Test conversion within Data class"""

    def test_data_class_args_conversion(self):
        """Test Data class converts args properly"""
        data = Data(42, 3.14, "hello", True, False)
        assert data.args == ["__INT__42", "__FLOAT__3.14", "hello", True, False]

    def test_data_class_kwargs_conversion(self):
        """Test Data class converts kwargs properly"""
        data = Data(x=42, y=3.14, name="hello", active=True, disabled=False)
        expected_kwargs = {"x": "__INT__42", "y": "__FLOAT__3.14", "name": "hello", "active": True, "disabled": False}
        assert data.kwargs == expected_kwargs

    def test_data_class_result_conversion(self):
        """Test Data class converts result properly"""
        data = Data(result=42)
        assert data.result == "__INT__42"

        data_float = Data(result=3.14)
        assert data_float.result == "__FLOAT__3.14"

        data_string = Data(result="hello")
        assert data_string.result == "hello"

    def test_data_class_get_result_method(self):
        """Test Data class get_result method converts back"""
        data = Data(result=42)
        assert data.get_result() == 42

        data_float = Data(result=3.14)
        assert data_float.get_result() == 3.14

        data_string = Data(result="hello")
        assert data_string.get_result() == "hello"


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_malformed_markers(self):
        """Test handling of malformed markers"""
        # Missing value after marker
        assert convert_value_from_xmlrpc("__INT__") == "__INT__"
        assert convert_value_from_xmlrpc("__FLOAT__") == "__FLOAT__"

        # Invalid values after marker (should not raise ValueError)
        result = convert_value_from_xmlrpc("__INT__not_a_number")
        assert result == "__INT__not_a_number"  # Should remain unchanged on error

        result = convert_value_from_xmlrpc("__FLOAT__not_a_number")
        assert result == "__FLOAT__not_a_number"  # Should remain unchanged on error

    def test_extreme_values(self):
        """Test extremely large and small values"""
        # Very large integer
        huge_int = 10**100
        converted = convert_value_for_xmlrpc(huge_int)
        restored = convert_value_from_xmlrpc(converted)
        assert restored == huge_int

        # Very small float
        tiny_float = 1e-100
        converted = convert_value_for_xmlrpc(tiny_float)
        restored = convert_value_from_xmlrpc(converted)
        assert restored == tiny_float

    def test_special_float_values(self):
        """Test special float values"""
        import math

        # Test infinity
        converted = convert_value_for_xmlrpc(float('inf'))
        restored = convert_value_from_xmlrpc(converted)
        assert math.isinf(restored)

        # Test negative infinity
        converted = convert_value_for_xmlrpc(float('-inf'))
        restored = convert_value_from_xmlrpc(converted)
        assert math.isinf(restored) and restored < 0

        # Test NaN
        converted = convert_value_for_xmlrpc(float('nan'))
        restored = convert_value_from_xmlrpc(converted)
        assert math.isnan(restored)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
