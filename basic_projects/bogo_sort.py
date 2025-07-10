import random

def is_sorted(arr):
    """Check if the array is sorted in ascending order."""
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            return False
    return True

def bogo_sort(arr):
    """
    Bogo Sort: A highly inefficient sorting algorithm that randomly shuffles
    the array until it happens to be sorted.
    
    Time Complexity: O((n+1)!) in the worst case
    Space Complexity: O(1)
    
    Args:
        arr: List of comparable elements to sort
    
    Returns:
        The sorted array
    """
    attempts = 0
    
    # Keep shuffling until the array is sorted
    while not is_sorted(arr):
        random.shuffle(arr)
        attempts += 1
    
    print(f"Bogo sort completed after {attempts} attempts!")
    return arr

def main():
    """Demonstrate bogo sort with example arrays."""
    
    # Example 1: Small array (reasonable chance of sorting quickly)
    print("Example 1: Small array")
    arr1 = [3, 1, 4, 1, 5]
    print(f"Original: {arr1}")
    sorted_arr1 = bogo_sort(arr1.copy())
    print(f"Sorted: {sorted_arr1}")
    print()
    
    # Example 2: Already sorted array
    print("Example 2: Already sorted array")
    arr2 = [1, 2, 3, 4, 5]
    print(f"Original: {arr2}")
    sorted_arr2 = bogo_sort(arr2.copy())
    print(f"Sorted: {sorted_arr2}")
    print()
    
    # Example 3: Very small array (for demonstration)
    print("Example 3: Very small array")
    arr3 = [5, 2, 8]
    print(f"Original: {arr3}")
    sorted_arr3 = bogo_sort(arr3.copy())
    print(f"Sorted: {sorted_arr3}")
    print()
    
    # Warning about larger arrays
    print("WARNING: Bogo sort is extremely inefficient!")
    print("Arrays larger than 10 elements may take an impractical amount of time.")

if __name__ == "__main__":
    main()