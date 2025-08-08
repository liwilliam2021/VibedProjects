import random
import time

def is_sorted(arr):
    """Check if the array is sorted in ascending order."""
    for i in range(len(arr) - 1):
        if arr[i] > arr[i + 1]:
            return False
    return True

def calculate_sortedness(arr):
    """
    Calculate how 'sorted' an array is as a percentage.
    Returns a value between 0 (completely unsorted) and 100 (fully sorted).
    
    This measures the percentage of adjacent pairs that are in correct order.
    """
    if len(arr) <= 1:
        return 100.0
    
    correct_pairs = 0
    total_pairs = len(arr) - 1
    
    for i in range(total_pairs):
        if arr[i] <= arr[i + 1]:
            correct_pairs += 1
    
    return (correct_pairs / total_pairs) * 100

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

def bogo_sort_with_visualization(arr, show_every_n=1000):
    """
    Bogo Sort with visualization of progress.
    
    This version shows the array state and 'sortedness' metric periodically
    during the sorting process, giving insight into how random the process is.
    
    Args:
        arr: List of comparable elements to sort
        show_every_n: Show progress every N attempts (default: 1000)
    
    Returns:
        Tuple of (sorted_array, total_attempts, sortedness_history)
    """
    attempts = 0
    sortedness_history = []
    best_sortedness = 0
    best_array = arr.copy()
    
    print(f"Starting Bogo Sort with visualization...")
    print(f"Initial array: {arr}")
    print(f"Initial sortedness: {calculate_sortedness(arr):.1f}%\n")
    
    start_time = time.time()
    
    while not is_sorted(arr):
        random.shuffle(arr)
        attempts += 1
        
        current_sortedness = calculate_sortedness(arr)
        
        # Track the best attempt so far
        if current_sortedness > best_sortedness:
            best_sortedness = current_sortedness
            best_array = arr.copy()
        
        # Show progress at intervals
        if attempts % show_every_n == 0:
            elapsed = time.time() - start_time
            print(f"Attempt {attempts:,}:")
            print(f"  Current: {arr[:10]}{'...' if len(arr) > 10 else ''}")
            print(f"  Sortedness: {current_sortedness:.1f}%")
            print(f"  Best so far: {best_sortedness:.1f}% - {best_array[:10]}{'...' if len(best_array) > 10 else ''}")
            print(f"  Time elapsed: {elapsed:.2f}s")
            print(f"  Rate: {attempts/elapsed:.0f} attempts/second\n")
            
            sortedness_history.append((attempts, current_sortedness))
    
    total_time = time.time() - start_time
    
    print(f"\n🎉 SUCCESS! Array sorted after {attempts:,} attempts!")
    print(f"Final array: {arr}")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average rate: {attempts/total_time:.0f} attempts/second")
    
    return arr, attempts, sortedness_history

def estimate_bogo_sort_time(n):
    """
    Estimate the expected time for bogo sort to complete.
    
    The expected number of shuffles for bogo sort is n! (n factorial).
    This function provides a rough estimate of how long it might take.
    
    Args:
        n: Size of the array to sort
    
    Returns:
        String describing the estimated time
    """
    import math
    
    # Calculate n!
    expected_attempts = math.factorial(n)
    
    # Assume we can do about 100,000 shuffles per second (rough estimate)
    shuffles_per_second = 100000
    
    seconds = expected_attempts / shuffles_per_second
    
    # Convert to human-readable format
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        return f"{seconds/60:.1f} minutes"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    elif seconds < 31536000:
        return f"{seconds/86400:.1f} days"
    else:
        years = seconds / 31536000
        if years < 1000:
            return f"{years:.1f} years"
        elif years < 1e6:
            return f"{years/1000:.1f} thousand years"
        elif years < 1e9:
            return f"{years/1e6:.1f} million years"
        else:
            return f"{years/1e9:.1f} billion years"

def quantum_bogo_sort(arr, max_universes=1000000):
    """
    Quantum Bogo Sort: A humorous "quantum" version of bogo sort.
    
    Based on the many-worlds interpretation of quantum mechanics, this algorithm
    "creates" multiple parallel universes where the array is shuffled differently.
    It then "collapses" to the universe where the array happens to be sorted.
    
    In reality, it just tries multiple shuffles in parallel (simulated) and
    returns the first sorted one found, or the best attempt if max universes
    is reached.
    
    Args:
        arr: List of comparable elements to sort
        max_universes: Maximum number of "parallel universes" to create
    
    Returns:
        Tuple of (sorted_array, universe_number, total_universes_created)
    """
    import multiprocessing
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    print(f"🌌 Initiating Quantum Bogo Sort across parallel universes...")
    print(f"Creating up to {max_universes:,} quantum states...")
    
    original_arr = arr.copy()
    start_time = time.time()
    
    def shuffle_universe(universe_id):
        """Simulate one universe's shuffle attempt."""
        universe_arr = original_arr.copy()
        random.shuffle(universe_arr)
        sortedness = calculate_sortedness(universe_arr)
        return universe_id, universe_arr, sortedness, is_sorted(universe_arr)
    
    # Use thread pool to simulate parallel universes
    max_workers = min(multiprocessing.cpu_count() * 2, 16)
    best_universe = None
    best_sortedness = 0
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all universe simulations
        futures = []
        for i in range(max_universes):
            future = executor.submit(shuffle_universe, i + 1)
            futures.append(future)
        
        # Check results as they complete
        for future in as_completed(futures):
            universe_id, universe_arr, sortedness, is_sorted_flag = future.result()
            
            # If we found a sorted universe, collapse immediately!
            if is_sorted_flag:
                elapsed = time.time() - start_time
                print(f"\n✨ QUANTUM COLLAPSE! Universe #{universe_id:,} has a sorted array!")
                print(f"Sorted array: {universe_arr}")
                print(f"Time to collapse: {elapsed:.3f} seconds")
                print(f"Universes explored: {universe_id:,}")
                
                # Cancel remaining futures
                for f in futures:
                    f.cancel()
                
                return universe_arr, universe_id, universe_id
            
            # Track the best universe so far
            if sortedness > best_sortedness:
                best_sortedness = sortedness
                best_universe = (universe_id, universe_arr, sortedness)
            
            # Progress update every 10% of universes
            if universe_id % (max_universes // 10) == 0:
                print(f"  Explored {universe_id:,} universes... Best sortedness: {best_sortedness:.1f}%")
    
    # If no sorted universe was found, return the best attempt
    elapsed = time.time() - start_time
    print(f"\n😔 No perfectly sorted universe found after {max_universes:,} attempts!")
    print(f"Best universe: #{best_universe[0]:,} with {best_universe[2]:.1f}% sortedness")
    print(f"Best attempt: {best_universe[1]}")
    print(f"Time elapsed: {elapsed:.3f} seconds")
    
    # Last desperate attempt: maybe we're lucky in this timeline?
    if not is_sorted(best_universe[1]):
        print("\n🎲 Making one final attempt in our current timeline...")
        current_timeline = best_universe[1].copy()
        attempts = 0
        while not is_sorted(current_timeline) and attempts < 1000:
            random.shuffle(current_timeline)
            attempts += 1
        
        if is_sorted(current_timeline):
            print(f"🎉 Success in our timeline after {attempts} more attempts!")
            return current_timeline, max_universes + attempts, max_universes + attempts
    
    return best_universe[1], best_universe[0], max_universes

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
    
    # Example 4: Visualization demo
    print("Example 4: Bogo sort with visualization")
    arr4 = [9, 3, 7, 1, 5]
    print(f"Original: {arr4}")
    sorted_arr4, attempts, history = bogo_sort_with_visualization(arr4.copy(), show_every_n=100)
    print()
    
    # Example 5: Time estimation
    print("Example 5: Time estimation for different array sizes")
    print("-" * 50)
    for size in [5, 8, 10, 12, 15, 20]:
        estimate = estimate_bogo_sort_time(size)
        print(f"Array size {size}: Expected time ≈ {estimate}")
    print("-" * 50)
    
    # Example 6: Quantum Bogo Sort
    print("\nExample 6: Quantum Bogo Sort")
    arr6 = [8, 3, 5, 1, 9, 2]
    print(f"Original: {arr6}")
    sorted_arr6, universe, total = quantum_bogo_sort(arr6.copy(), max_universes=10000)
    print(f"Final sorted array: {sorted_arr6}")
    print()
    
    # Warning about larger arrays
    print("\nWARNING: Bogo sort is extremely inefficient!")
    print("Arrays larger than 10 elements may take an impractical amount of time.")
    print("The algorithm has O((n+1)!) time complexity in the worst case!")
    print("\nNote: Even 'Quantum' Bogo Sort doesn't actually use quantum mechanics -")
    print("it's just a fun parallel simulation that's still fundamentally inefficient!")

if __name__ == "__main__":
    main()