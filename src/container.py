from contextlib import contextmanager

# The maximum width of a line of text in chat with default settings in in-game pixels.
CHAT = 320
# The maximum width of a line of text in a book in in-game pixels.
BOOK = 114

# The maximum width of a line of text in the container in in-game pixels. Defaults to
#  `CHAT` when not set by `container`.
container_width = CHAT


@contextmanager
def container(width: float):
    global container_width

    initial_container_width = container_width

    try:
        container_width = width
        yield
    finally:
        container_width = initial_container_width
