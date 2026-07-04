import asyncio, time
from rate_limiter import RateLimiter

async def test():
    rl = RateLimiter({"slow.com": 3.0, "fast.com": 0.5})
    t0 = time.time()
    await rl.wait("slow.com")
    t1 = time.time()
    assert t1 - t0 < 0.1, "first call should not wait"
    await rl.wait("slow.com")
    t2 = time.time()
    assert t2 - t1 >= 2.9, "second call should wait ~3s"
    t3 = time.time()
    await rl.wait("fast.com")
    t4 = time.time()
    assert t4 - t3 < 0.1, "different domain should not wait"
    print("ALL PASS")

asyncio.run(test())
