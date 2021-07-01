import asyncio

async def anyfunc():
     return 1

async def main():
     anyfunc()


if __name__ == "__main__":
     asyncio.run(main())
     # Output: RuntimeWarning: coroutine 'anyfunc' was never awaited
