from resonate.task_sources.poller import Poller
from resonate.stores.remote import RemoteStore
from resonate import Resonate
import random

# Create a Resonate instance connected to the Resonate Server
resonate = Resonate(
    store=RemoteStore(url="http://localhost:8001"),
    task_source=Poller(url="http://localhost:8002"),
)


# Register the top-level function with Resonate
@resonate.register
def foo(ctx, greeting):
    print("running foo")
    greeting = yield ctx.lfc(bar, greeting)
    yield ctx.sleep(10)
    greeting = yield ctx.lfc(baz, greeting)
    return greeting


def bar(_, v):
    print("running bar")
    if random.randint(0, 100) > 50:
        raise Exception("encountered unexpected error")
    return f"{v} world"


def baz(_, v):
    print("running baz")
    if random.randint(0, 100) > 50:
        raise Exception("encountered unexpected error")
    return f"{v}!"


# Define a main function
def main():
    try:
        handle = foo.run("hello-world-greeting", greeting="hello")
        print(handle.result())
    except Exception as e:
        print(e)


# Run the main function when the script is invoked
if __name__ == "__main__":
    main()
