# Copyright (c) Nex-AGI. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Tests for tool_types module."""

import json
from datetime import datetime

import pytest

from nexdr.agents.tool_types import (
    GenericToolResult,
    ToolStatus,
    create_error_tool_result,
    create_success_tool_result,
    extract_tool_error_message,
    extract_tool_result_data,
    is_error_tool_result,
    is_success_tool_result,
)


class TestToolStatus:
    """Tests for ToolStatus enum."""

    def test_tool_status_values(self):
        """Test that ToolStatus has expected values."""
        assert ToolStatus.SUCCESS == "success"
        assert ToolStatus.ERROR == "error"

    def test_tool_status_string_conversion(self):
        """Test ToolStatus string conversion."""
        # Note: str(Enum) returns "EnumName.VALUE" format in Python
        assert ToolStatus.SUCCESS.value == "success"
        assert ToolStatus.ERROR.value == "error"


class TestGenericToolResult:
    """Tests for GenericToolResult dataclass."""

    def test_basic_creation(self):
        """Test basic creation of GenericToolResult."""
        result = GenericToolResult(
            status=ToolStatus.SUCCESS,
            message="Operation completed",
        )
        assert result.status == ToolStatus.SUCCESS
        assert result.message == "Operation completed"
        assert result.data is None
        assert result.tool_name == ""
        assert result.params is None
        assert result.timestamp != ""

    def test_creation_with_all_fields(self):
        """Test creation with all fields."""
        result = GenericToolResult(
            status=ToolStatus.SUCCESS,
            message="Test message",
            data={"key": "value"},
            tool_name="test_tool",
            params={"param1": "value1"},
            timestamp="2024-01-01T00:00:00",
        )
        assert result.status == ToolStatus.SUCCESS
        assert result.message == "Test message"
        assert result.data == {"key": "value"}
        assert result.tool_name == "test_tool"
        assert result.params == {"param1": "value1"}
        assert result.timestamp == "2024-01-01T00:00:00"

    def test_timestamp_auto_generation(self):
        """Test that timestamp is auto-generated if not provided."""
        result = GenericToolResult(
            status=ToolStatus.SUCCESS,
            message="Test",
        )
        # Verify timestamp is a valid ISO format
        try:
            datetime.fromisoformat(result.timestamp)
        except ValueError:
            pytest.fail("Timestamp is not in valid ISO format")

    def test_to_dict(self):
        """Test to_dict method."""
        result = GenericToolResult(
            status=ToolStatus.SUCCESS,
            message="Test message",
            data={"key": "value"},
            tool_name="test_tool",
            params={"param1": "value1"},
            timestamp="2024-01-01T00:00:00",
        )
        result_dict = result.to_dict()
        assert result_dict["status"] == "success"
        assert result_dict["message"] == "Test message"
        assert result_dict["data"] == {"key": "value"}
        assert result_dict["tool_name"] == "test_tool"
        assert result_dict["params"] == {"param1": "value1"}
        assert result_dict["timestamp"] == "2024-01-01T00:00:00"

    def test_to_dict_without_params(self):
        """Test to_dict without params."""
        result = GenericToolResult(
            status=ToolStatus.ERROR,
            message="Error message",
            data="Error details",
        )
        result_dict = result.to_dict()
        assert "params" not in result_dict

    def test_to_json(self):
        """Test to_json method."""
        result = GenericToolResult(
            status=ToolStatus.SUCCESS,
            message="Test message",
            data={"key": "value"},
            tool_name="test_tool",
        )
        json_str = result.to_json()
        parsed = json.loads(json_str)
        assert parsed["status"] == "success"
        assert parsed["message"] == "Test message"


class TestCreateSuccessToolResult:
    """Tests for create_success_tool_result function."""

    def test_basic_success_result(self):
        """Test basic success result creation."""
        result = create_success_tool_result()
        assert result["status"] == "success"
        assert result["message"] == "Operation completed successfully"

    def test_success_result_with_data(self):
        """Test success result with data."""
        data = {"items": [1, 2, 3]}
        result = create_success_tool_result(data=data, message="Found 3 items")
        assert result["status"] == "success"
        assert result["data"] == data
        assert result["message"] == "Found 3 items"

    def test_success_result_with_all_params(self):
        """Test success result with all parameters."""
        result = create_success_tool_result(
            data={"result": "ok"},
            message="Custom message",
            tool_name="my_tool",
            params={"input": "test"},
        )
        assert result["status"] == "success"
        assert result["data"] == {"result": "ok"}
        assert result["message"] == "Custom message"
        assert result["tool_name"] == "my_tool"
        assert result["params"] == {"input": "test"}


class TestCreateErrorToolResult:
    """Tests for create_error_tool_result function."""

    def test_basic_error_result(self):
        """Test basic error result creation."""
        result = create_error_tool_result()
        assert result["status"] == "error"
        assert result["message"] == "Operation failed"

    def test_error_result_with_details(self):
        """Test error result with error details."""
        result = create_error_tool_result(
            error="File not found: test.txt",
            message="Failed to read file",
        )
        assert result["status"] == "error"
        assert result["data"] == "File not found: test.txt"
        assert result["message"] == "Failed to read file"

    def test_error_result_with_all_params(self):
        """Test error result with all parameters."""
        result = create_error_tool_result(
            error="Connection refused",
            message="Network error",
            tool_name="network_tool",
            params={"host": "example.com"},
        )
        assert result["status"] == "error"
        assert result["data"] == "Connection refused"
        assert result["message"] == "Network error"
        assert result["tool_name"] == "network_tool"


class TestIsSuccessToolResult:
    """Tests for is_success_tool_result function."""

    def test_dict_success_result(self):
        """Test with dict success result."""
        result = {"status": "success", "message": "OK"}
        assert is_success_tool_result(result) is True

    def test_dict_success_with_enum_value(self):
        """Test with dict containing ToolStatus enum."""
        result = {"status": ToolStatus.SUCCESS, "message": "OK"}
        assert is_success_tool_result(result) is True

    def test_dict_error_result(self):
        """Test with dict error result."""
        result = {"status": "error", "message": "Failed"}
        assert is_success_tool_result(result) is False

    def test_object_with_status_attr(self):
        """Test with object having status attribute."""
        obj = GenericToolResult(status=ToolStatus.SUCCESS, message="OK")
        assert is_success_tool_result(obj) is True

    def test_object_with_error_status(self):
        """Test with object having error status."""
        obj = GenericToolResult(status=ToolStatus.ERROR, message="Failed")
        assert is_success_tool_result(obj) is False

    def test_invalid_input(self):
        """Test with invalid input."""
        assert is_success_tool_result(None) is False
        assert is_success_tool_result("string") is False
        assert is_success_tool_result(123) is False


class TestIsErrorToolResult:
    """Tests for is_error_tool_result function."""

    def test_dict_error_result(self):
        """Test with dict error result."""
        result = {"status": "error", "message": "Failed"}
        assert is_error_tool_result(result) is True

    def test_dict_error_with_enum_value(self):
        """Test with dict containing ToolStatus enum."""
        result = {"status": ToolStatus.ERROR, "message": "Failed"}
        assert is_error_tool_result(result) is True

    def test_dict_success_result(self):
        """Test with dict success result."""
        result = {"status": "success", "message": "OK"}
        assert is_error_tool_result(result) is False

    def test_object_with_error_status(self):
        """Test with object having error status."""
        obj = GenericToolResult(status=ToolStatus.ERROR, message="Failed")
        assert is_error_tool_result(obj) is True

    def test_invalid_input(self):
        """Test with invalid input."""
        assert is_error_tool_result(None) is False
        assert is_error_tool_result("string") is False


class TestExtractToolResultData:
    """Tests for extract_tool_result_data function."""

    def test_extract_from_dict(self):
        """Test extracting data from dict."""
        result = {"status": "success", "data": {"items": [1, 2, 3]}}
        data = extract_tool_result_data(result)
        assert data == {"items": [1, 2, 3]}

    def test_extract_from_object(self):
        """Test extracting data from object."""
        obj = GenericToolResult(
            status=ToolStatus.SUCCESS,
            message="OK",
            data="result data",
        )
        data = extract_tool_result_data(obj)
        assert data == "result data"

    def test_extract_from_non_result(self):
        """Test extracting from non-result value."""
        assert extract_tool_result_data("string") == "string"
        assert extract_tool_result_data(123) == 123


class TestExtractToolErrorMessage:
    """Tests for extract_tool_error_message function."""

    def test_extract_from_dict(self):
        """Test extracting error message from dict."""
        result = {"status": "error", "data": "File not found"}
        error = extract_tool_error_message(result)
        assert error == "File not found"

    def test_extract_from_object(self):
        """Test extracting error message from object."""
        obj = GenericToolResult(
            status=ToolStatus.ERROR,
            message="Failed",
            data="Connection timeout",
        )
        error = extract_tool_error_message(obj)
        assert error == "Connection timeout"

    def test_extract_from_none(self):
        """Test extracting from None."""
        assert extract_tool_error_message(None) is None


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    def test_result_with_none_data(self):
        """Test result with None data."""
        result = create_success_tool_result(data=None)
        assert result["data"] is None

    def test_result_with_complex_data(self):
        """Test result with complex nested data."""
        complex_data = {
            "nested": {
                "list": [1, 2, {"key": "value"}],
                "string": "test",
            },
            "number": 42,
        }
        result = create_success_tool_result(data=complex_data)
        assert result["data"] == complex_data

    def test_result_with_unicode_message(self):
        """Test result with unicode characters."""
        result = create_success_tool_result(message="操作成功")
        assert result["message"] == "操作成功"

    def test_result_with_empty_string(self):
        """Test result with empty string data."""
        result = create_success_tool_result(data="", message="Empty result")
        assert result["data"] == ""

    def test_result_with_list_data(self):
        """Test result with list data."""
        result = create_success_tool_result(data=[1, 2, 3, 4, 5])
        assert result["data"] == [1, 2, 3, 4, 5]
