#!/usr/bin/env python3
"""
Async/Await Demo

A small script that shows how Python's asyncio lets you run
I/O-bound work concurrently without threads.

Run:
    python asynchronous/async_demo.py
"""

import asyncio
import time


async def fetch_data(name: str, delay: float) -> str:
    """Simulate a slow network or database call."""
    print(f"  [{name}] starting (will take {delay}s)")
    await asyncio.sleep(delay)
    print(f"  [{name}] finished")
    return f"data from {name}"


async def run_sequential() -> list[str]:
    """Await each task one after another."""
    print("\n--- Sequential (one at a time) ---")
    results = []
    for name, delay in [("task-a", 1.0), ("task-b", 1.0), ("task-c", 1.0)]:
        result = await fetch_data(name, delay)
        results.append(result)
    return results


async def run_concurrent() -> list[str]:
    """Start all tasks at once and await them together."""
    print("\n--- Concurrent (all at once with gather) ---")
    tasks = [
        fetch_data("task-a", 1.0),
        fetch_data("task-b", 1.0),
        fetch_data("task-c", 1.0),
    ]
    return await asyncio.gather(*tasks)


async def run_with_timeout() -> str:
    """Use wait_for to cap how long you wait for a slow task."""
    print("\n--- Timeout (cancel slow work after 0.5s) ---")
    try:
        return await asyncio.wait_for(fetch_data("slow-task", 2.0), timeout=0.5)
    except asyncio.TimeoutError:
        print("  [slow-task] timed out — moving on without blocking forever")
        return "timed out"


async def main() -> None:
    print("Python async/await demo")
    print("=" * 40)

    start = time.perf_counter()
    await run_sequential()
    sequential_elapsed = time.perf_counter() - start
    print(f"Sequential total: ~{sequential_elapsed:.1f}s (tasks ran back-to-back)")

    start = time.perf_counter()
    results = await run_concurrent()
    concurrent_elapsed = time.perf_counter() - start
    print(f"Concurrent total: ~{concurrent_elapsed:.1f}s")
    print(f"Results: {results}")

    await run_with_timeout()

    print("\nKey idea: `await` pauses *this* coroutine, but the event loop")
    print("can run other coroutines while one is waiting on I/O (or sleep).")


if __name__ == "__main__":
    asyncio.run(main())
