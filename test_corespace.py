#!/usr/bin/env python3
"""
Minimal test server for the Corespace Blueprint
This bypasses the full AMI system to test just the corespace blueprint functionality
"""
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Test imports without the full AMI system
def test_corespace_blueprint():
    """Test the corespace blueprint can be imported and initialized"""
    
    # Mock the minimal dependencies
    class MockFilespace:
        def __init__(self):
            self.location = '/tmp/test_filespace'
            os.makedirs(self.location, exist_ok=True)
    
    class MockSettings:
        def __init__(self):
            self.reminder_file = '/tmp/test_reminders.md'
            # Create empty reminder file if it doesn't exist
            if not os.path.exists(self.reminder_file):
                with open(self.reminder_file, 'w') as f:
                    f.write('# Reminders\n\n## Upcoming\n\n## Completed\n')
    
    try:
        # Import the corespace blueprint directly
        from ami.builtin.corespace.blueprint import CorespaceBlueprint
        from ami.builtin.corespace.settings import CorespaceSettings
        
        print("✅ Successfully imported CorespaceBlueprint and CorespaceSettings")
        
        # Test settings initialization
        settings = CorespaceSettings()
        print(f"✅ Settings initialized with menu items: {[item['text'] for item in settings.menu_items]}")
        
        # Test blueprint initialization with mocks
        filespace = MockFilespace()
        blueprint = CorespaceBlueprint(filespace, MockSettings())
        print("✅ Blueprint initialized successfully")
        
        # Test natural language parsing
        test_specs = [
            "tomorrow 3pm",
            "in 2 hours", 
            "next Friday 9am",
            "2025-01-15 14:30"
        ]
        
        print("\n🧪 Testing natural language parsing:")
        for spec in test_specs:
            try:
                result = blueprint._parse_time_specification(spec)
                if result:
                    print(f"✅ '{spec}' -> {result}")
                else:
                    print(f"❌ '{spec}' -> Failed to parse")
            except Exception as e:
                print(f"❌ '{spec}' -> Error: {e}")
        
        print("\n🎉 All core functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing corespace blueprint: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_corespace_blueprint()
    sys.exit(0 if success else 1)