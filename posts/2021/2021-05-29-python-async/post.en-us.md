# Python Async with real-life examples 🐍🔀

Maybe it's just me, but I hate stupid examples. I hate reading about OOP with animal examples as much as I hate reading about async with the client bare just `asyncio.sleep` statements. Mostly because (considering you won't work for a zoo 🤷‍♂️) these examples will never get any close to real life.

I want then to explore async without talking about food (although I'm hungry right now) and using examples that you can actually feel and understand.

## Intro to the problem

I don't want to start talking about the solution (i.e. async), **I want you to feel the problem first**, I want you to actually run things locally from your own computer. To create the background we want to simulate I'll be using a repo with scenarios available on [GitHub](https://github.com/guilatrova/python-async-scenarios) and I strongly recommend you to clone it so you can follow up with me.

```sh
# Clone
git clone https://github.com/guilatrova/python-async-scenarios.git
cd python-async-scenarios

# Create virtualenv
python -m virtualenv .venv
source .venv/bin/activate

# Install deps
pip install -r requirements.txt
```

From now on I'll assume you did so. Please, run the commands with me! 😁

## HTTP

### 🐌 Slow server

Please, start our silly API server:

```sh
cd API/delay_api
python manage.py runserver
```

It's fine to ignore the warnings re migrations, now open a new terminal and head to the client dir and execute the sync one:

```sh
cd API/client
python sync.py
```

If everything happens as expected, you should see some output just like:

```sh
❯ python sync.py
==========
R1: Requesting 'http://localhost:8000/delay-me?seconds=10'
R1: Request finally done! Server replied 'Done, I waited for 10 secs'
R2: Requesting 'http://localhost:8000/delay-me?seconds=2'
R2: Request finally done! Server replied 'Done, I waited for 2 secs'
R3: Requesting 'http://localhost:8000/delay-me?seconds=5'
R3: Request finally done! Server replied 'Done, I waited for 5 secs'
----------
Time elapsed: 17.042340711999998
==========
```

Well, please open the `sync.py` code and get familiar with it. Note that we got 3 "requesters" responsible for pulling data from a URL in some server, as soon as they reply we print the response and move on.

**Gui, you liar, you told me you wouldn't be using sleeps!!** There's not really a `sleep` there. Note that who's actually making our code slower is rather the server (which let's pretend we can't control) and not the client.

In other words, the server can do anything it wishes, our client is just waiting for it to respond. If it helps, **try to think about it like a long operation triggered by HTTP to some third-party API out of your control.**

Let's picture what's going on.
As you can see below, the only bottleneck is the server response. Making a request and printing its results always take the same amount of time.

![http sync](http-sync.png)

### 🐶 Slow server (but optimized)

Hopefully, you'll understand the issue. **We don't have to wait for every request to finish in order to perform further requests (in our case R2 and R3).** Again, considering we can't touch the server, thus it can't get any faster, the only option is to optimize how we perform the requests. If you bet `async` might help us, then yes, you're right.

In the same directory (`API/client`), you're about to find a file named `async.py`. Before running commands, I want to highlight some major differences:

```py
import asyncio
import aiohttp  # <-- We use this lib over "requests"

...

class Requester:
    # The method is declared as "async"
    async def pull_from_server(self, secs: int) -> NoReturn:
        ...

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                content = await resp.text()  # <-- We use await here
                ...


# The function is declared as "async"
async def main():
    ...

    await asyncio.gather(  # <-- We use asyncio.gather
        r1.pull_from_server(10),
        r2.pull_from_server(2),
        r3.pull_from_server(5)
    )

if __name__ == "__main__":
    asyncio.run(main())  # <-- We use asyncio.run to start our main function
```

Before getting into the details, let's execute and see how it performs in comparison to our first example.

```sh
❯ cd API/client
❯ python async.py
==========
R1: Requesting 'http://localhost:8000/delay-me?seconds=10'
R2: Requesting 'http://localhost:8000/delay-me?seconds=2'
R3: Requesting 'http://localhost:8000/delay-me?seconds=5'
R2: Request finally done! Server replied 'Done, I waited for 2 secs'
R3: Request finally done! Server replied 'Done, I waited for 5 secs'
R1: Request finally done! Server replied 'Done, I waited for 10 secs'
----------
Time elapsed: 10.052988270999998
==========
```

Ok, that's a huge performance bump. It took only ~10 secs, which is the time of our slowest request in comparison to ~17 secs.
Note the interesting points:

- All the requests were made right away in the order we specified in code;
- The responses were out of order (first **R2**, then **R3**, and only then **R1** finished);

Now it starts to get interesting, here is where some people mistakenly think this is actually running in parallel, but no, **it's not parallel, it's concurrent (i.e. async)**.

See the following diagram:

![http async](http-async.png)

Hopefully it's simpler to understand how python async works. **There's no code being run at the same time.**

This was me when I found out that async is not actually parallel, but concurrent:

![me surprised for not knowing async is not parallel](pikachu-meme.jpeg)

Everytime we run **`await`** (e.g. `await resp.text()`) we give control back to python (more specifically to the **event loop** as we're going to discuss later) to decide what to do in the meantime.

In other words, async works better when you have to wait for IO operations (in this case network).

### 🐌 Slow server (with a fake optimization)

Now, you might think that's quite simple: Let's just use async whenever I have to request some IO resource!

Well, it's not enough. You might have noticed we're using the `aiohttp` lib. I'm not using this lib because I prefer it over `requests`, I'm using it because I have to in order to perform async operations.

To make that clear and obvious, you can find `async_w_sync.py` where it still use `requests`.
Note how using `async def` for a method/function does not make it really async.

```sh
❯ python async_w_sync.py
==========
R1: Requesting 'http://localhost:8000/delay-me?seconds=10'
R1: Request finally done! Server replied 'Done, I waited for 10 secs'
R2: Requesting 'http://localhost:8000/delay-me?seconds=2'
R2: Request finally done! Server replied 'Done, I waited for 2 secs'
R3: Requesting 'http://localhost:8000/delay-me?seconds=5'
R3: Request finally done! Server replied 'Done, I waited for 5 secs'
----------
Time elapsed: 17.042022314999997
==========
```

**Declaring a function with `async def` does no magic trick, you need a lib that supports it.**

## 💽 Database

If you're demanding like me, you probably are still unhappy with a shady sleep commmand behind an API.

That's why we're going to use a real database now with a real query. It was tricky to make the database/query intentionally slow (e.g. poor indexes, duplicated data, terrible joins), but the point is still valid to simulate and compare sync and async code.

### 🇧🇷 Set up the database

Let's set up the slow database with terrible queries.

This script will add lots of repeated data about all Brazil cities. You might want to get some coffee while the script runs.

```bash
cd database/pgsql
docker compose up

# Switch to another terminal and
cd scripts
python generatedb.py
```

### Sync

```bash
❯ python sync.py
==========
R1: Querying '
    SELECT c.name, s.state FROM cities c
    JOIN states s ON  c.state_id = s.id
    WHERE s.state IN (
        SELECT state FROM states
    )
    ORDER BY s.long_name, c.name
'
R1: Query made! Db replied '7789600' rows
R2: Querying '
    SELECT c.name, s.state FROM cities c
    JOIN states s ON  c.state_id = s.id
    WHERE c.name like 'A%'
'
R2: Query made! Db replied '575400' rows
R3: Querying '
    SELECT c.name, s.state FROM cities c
    JOIN states s ON  c.state_id = s.id
    WHERE s.state like 'M%' OR s.state like '%P'
'
R3: Query made! Db replied '2730000' rows
----------
Time elapsed: 22.872724297999998
==========
```

Nothing really new to the overall structure except by the query/database.

### Async

Let's try the `async` version now:

```bash
❯ python async.py
==========
R1: Querying '
    SELECT c.name, s.state FROM cities c
    JOIN states s ON  c.state_id = s.id
    WHERE s.state IN (
        SELECT state FROM states
    )
    ORDER BY s.long_name, c.name
'
R2: Querying '
    SELECT c.name, s.state FROM cities c
    JOIN states s ON  c.state_id = s.id
    WHERE c.name like 'A%'
'
R3: Querying '
    SELECT c.name, s.state FROM cities c
    JOIN states s ON  c.state_id = s.id
    WHERE s.state like 'M%' OR s.state like '%P'
'
R2: Query made! Db replied '575400' rows
R3: Query made! Db replied '2730000' rows
R1: Query made! Db replied '7789600' rows
----------
Time elapsed: 18.440496856
==========
```

The first interesting thing to notice is how the 3 queries as triggered right away as we wait for the results.

Another point worth mentioning is how **async is no fix for a bottleneck.** The code is still very slow, although we could optimize a bit (dropping from 22 secs to 18 secs).

## Concurrency, Coroutines and the Event Loop

We saw and executed a lot of code without understanding what it actually does (it reminds me of my work), we're about to get deeper so we can understand it a bit better.
Now things start getting a bit more complext. I'll do my best to not make it boring, I swear :) .

So, as you could see, using async doesn't make your code parallel, it's more an **optimization of iddle time** (or concurrency as people prefer to call). We also noticed that making a function `async` when the libs/internal workings are `sync` make no effect at all!

### Coroutines

**Coroutines** are functions that can be started, paused, and resumed. Whenever you invoke an `async` function you are getting a coroutine.

```py
async def anyfunc():
    return 1

r = anyfunc()
print(type(r))
# Output: <class 'coroutine'>
```

Whenever you `await`, you're asking for the event loop to handle that coroutine and return a result to you. Note that coroutines never awaited are never executed.

You still can execute a coroutine by creating a task and getting its result later:

```py
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
```

I believe it's time to present you the **Event Loop**.

### Event Loop

Think about the event loop as a manager that decides what should happen and what should wait.
