import pytest
from src.tools.base_tools import (
    WebSearchTool,
    WebScrapeTool,
    SystemCommandTool,
    FileSystemTool,
    TwitterSearchTool,
    SystemInfoTool
)
import os
import tempfile

@pytest.fixture
def web_search_tool():
    return WebSearchTool()

@pytest.fixture
def web_scrape_tool():
    return WebScrapeTool()

@pytest.fixture
def system_command_tool():
    return SystemCommandTool()

@pytest.fixture
def file_system_tool():
    return FileSystemTool()

@pytest.fixture
def twitter_search_tool():
    return TwitterSearchTool()

@pytest.fixture
def system_info_tool():
    return SystemInfoTool()

def test_web_search_tool(web_search_tool):
    results = web_search_tool.forward("python programming")
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(result, dict) for result in results)

def test_web_scrape_tool(web_scrape_tool):
    result = web_scrape_tool.forward("https://example.com")
    assert isinstance(result, str)
    assert len(result) > 0

def test_system_command_tool(system_command_tool):
    result = system_command_tool.forward("echo 'test'")
    assert isinstance(result, str)
    assert "test" in result

def test_file_system_tool(file_system_tool):
    # Create a temporary file for testing
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test content")
        tmp_path = tmp.name

    try:
        # Test write operation
        write_result = file_system_tool.forward("write", tmp_path, "new content")
        assert "Successfully wrote" in write_result

        # Test read operation
        read_result = file_system_tool.forward("read", tmp_path)
        assert read_result == "new content"

        # Test list operation
        dir_path = os.path.dirname(tmp_path)
        list_result = file_system_tool.forward("list", dir_path)
        assert isinstance(list_result, str)
        assert os.path.basename(tmp_path) in list_result
    finally:
        os.unlink(tmp_path)

def test_twitter_search_tool(twitter_search_tool):
    if not os.getenv("TWITTER_API_KEY"):
        pytest.skip("Twitter API credentials not available")
    
    results = twitter_search_tool.forward("python")
    assert isinstance(results, list)
    assert all(isinstance(result, dict) for result in results)

def test_system_info_tool(system_info_tool):
    # Test CPU metrics
    cpu_result = system_info_tool.forward("cpu")
    assert isinstance(cpu_result, dict)
    assert "cpu_percent" in cpu_result
    assert "cpu_count" in cpu_result

    # Test memory metrics
    memory_result = system_info_tool.forward("memory")
    assert isinstance(memory_result, dict)
    assert "total" in memory_result
    assert "available" in memory_result
    assert "percent" in memory_result

    # Test disk metrics
    disk_result = system_info_tool.forward("disk")
    assert isinstance(disk_result, dict)
    assert "total" in disk_result
    assert "used" in disk_result
    assert "free" in disk_result
    assert "percent" in disk_result 