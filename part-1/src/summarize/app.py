from resonate import Resonate
from resonate.stores import LocalStore
import random

# Create a Resonate instance with a local store
resonate = Resonate(store=LocalStore())


# Register the top-level function with Resonate
@resonate.register
def foo(ctx, greeting):
    print("running foo")
    greeting = yield ctx.lfc(bar, greeting)
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
