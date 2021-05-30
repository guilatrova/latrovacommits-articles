# Python Async with real-life examples

Maybe it's just me, but I hate stupid examples. I hate reading about OOP with animal examples as much as I hate reading about async with the client using just sleep statements. Mostly because (considering you won't work for a zoo 🤷‍♂️) these examples will never get any close to real life.

I want then to explore async without talking about food (although I'm hungry right now) and using examples that you can actually feel and understand.

## Intro to the problem

I don't want to start talking about solution (i.e. async), I want you to feel the problem first, I want you to actually run things locally from your own computer. To create the background we want to simulate I'll be using a repo for this located on [GitHub](https://github.com/guilatrova/python-async-scenarios) and I strongly recommend you to clone it so you can follow up with me.

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

From now on I'll assume your did so.

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

**Gui, you liar, you told me you wouldn't be using sleeps!!**. There's not really a `sleep` there. Note that who's actually making our code slower is rather the server (which let's pretend we can't control) and not the client.

In other words, the server can do anything it wishes, our client is just waiting for it to respond. If it helps, **try to think about it like a long operation triggered by HTTP to some third-party API out of your control.**

Let's picture what's going on.
As you can see below, the only bottleneck is the server response. Making a request and printing its results always take the same amount of time.

(!PUT IMAGE HERE!)

### Slow server (but optimized)

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

Now it starts to get interesting, here is where some people mistakenly think this is actually running in parallel, but no **it's not parallel, it's optimized (or async)**.

See the following diagram:



### Slow server (with a fake optimization)
