"""
Test script to verify class mapping functionality
"""

from yolo_module import load_class_mapping

def test_class_mapping():
    """Test if class mapping loads correctly"""
    print("=" * 60)
    print("Testing Class Mapping")
    print("=" * 60)
    
    # Load class mapping
    mapping = load_class_mapping("class_mapping.txt")
    
    print(f"\nTotal classes loaded: {len(mapping)}")
    print("\nFirst 10 class mappings:")
    print("-" * 60)
    
    for i, (key, value) in enumerate(mapping.items()):
        if i >= 10:
            break
        print(f"{key:20} -> {value}")
    
    # Test specific keys
    print("\n" + "=" * 60)
    print("Testing specific keys:")
    print("=" * 60)
    
    test_keys = ["W.224", "P.102", "Camera", "P.127*50"]
    for key in test_keys:
        if key in mapping:
            print(f"✓ {key:15} -> {mapping[key]}")
        else:
            print(f"✗ {key:15} -> NOT FOUND")
    
    print("\n" + "=" * 60)
    print("Test completed!")
    print("=" * 60)
    
    return mapping


if __name__ == "__main__":
    try:
        mapping = test_class_mapping()
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
