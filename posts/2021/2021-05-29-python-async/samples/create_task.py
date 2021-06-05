import asyncio

async def anyfunc():
     return 1

async def main():
     r = anyfunc()
     task = asyncio.create_task(r)  # Coroutine is handled to the Event Loop

     print(type(task))
     # Output: <class '_asyncio.Task'>

     print(await task)
     # Output: 1


if __name__ == "__main__":
     asyncio.run(main())
