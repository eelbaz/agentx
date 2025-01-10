import os
import sys
import pytest
from contextlib import contextmanager

# Add project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from src.agent_manager import AgentManager

@contextmanager
def assert_import_blocked(package_name: str):
    """Context manager to verify that importing a package raises ImportError"""
    try:
        yield
        pytest.fail(f"Should not be able to import {package_name}")
    except ImportError as e:
        assert f"Import from {package_name} is not allowed" in str(e)

def test_package_management():
    """Test the package management functionality"""
    
    # Initialize agent manager
    agent_manager = AgentManager()
    
    # Test allowing a package
    result = agent_manager.allow_package("midiutil")
    assert isinstance(result, dict), "Result should be a dictionary"
    assert 'success' in result, "Result should have 'success' key"
    assert 'message' in result, "Result should have 'message' key"
    print(f"Allow package result: {result}")
    
    if result['success']:
        # If package was successfully allowed, test importing it
        try:
            from midiutil import MIDIFile
            midi_created = True
            print("Successfully imported midiutil")
        except ImportError as e:
            midi_created = False
            print(f"Failed to import midiutil: {e}")
        assert midi_created, "Failed to import midiutil after allowing it"
        
        # Test disallowing the package
        result = agent_manager.disallow_package("midiutil")
        assert result['success'], "Failed to disallow midiutil"
        print(f"Disallow package result: {result}")
        
        # Create a new AgentManager instance to ensure clean state
        agent_manager = AgentManager()
        print("Created new AgentManager instance")
        
        # Verify package is blocked in new instance
        with assert_import_blocked("midiutil"):
            from midiutil import MIDIFile
        print("Successfully blocked midiutil import")
    else:
        print("Skipping further tests as midiutil package is not installed")

if __name__ == '__main__':
    test_package_management() 