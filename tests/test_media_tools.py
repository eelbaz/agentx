import pytest
import os
from PIL import Image
from src.tools.media_tools import ImageGenerationTool, VideoGenerationTool

@pytest.fixture
def image_generation_tool():
    return ImageGenerationTool()

@pytest.fixture
def video_generation_tool():
    return VideoGenerationTool()

def test_image_generation_openai(image_generation_tool):
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not available")
    
    prompt = "A beautiful sunset over mountains"
    result = image_generation_tool.forward(prompt, provider="openai")
    
    assert isinstance(result, str)
    assert os.path.exists(result)
    
    # Verify the image was created and is valid
    try:
        img = Image.open(result)
        assert img.size[0] > 0
        assert img.size[1] > 0
    except Exception as e:
        pytest.fail(f"Failed to open generated image: {str(e)}")
    finally:
        if os.path.exists(result):
            os.remove(result)

def test_image_generation_invalid_provider(image_generation_tool):
    prompt = "A beautiful sunset over mountains"
    with pytest.raises(ValueError) as exc_info:
        image_generation_tool.forward(prompt, provider="invalid_provider")
    assert "Unsupported provider" in str(exc_info.value)

def test_video_generation(video_generation_tool):
    prompt = "A car driving down a road"
    result = video_generation_tool.forward(prompt)
    
    # Currently returns placeholder message
    assert isinstance(result, str)
    assert "not yet implemented" in result.lower()

def test_image_generation_size_validation(image_generation_tool):
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OpenAI API key not available")
    
    prompt = "A beautiful sunset over mountains"
    
    # Test valid sizes
    valid_sizes = ["256x256", "512x512", "1024x1024"]
    for size in valid_sizes:
        result = image_generation_tool.forward(prompt, provider="openai", size=size)
        assert isinstance(result, str)
        assert os.path.exists(result)
        os.remove(result)
    
    # Test invalid size
    with pytest.raises(ValueError) as exc_info:
        image_generation_tool.forward(prompt, provider="openai", size="invalid_size")
    assert "size" in str(exc_info.value).lower() 