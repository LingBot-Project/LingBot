from events.Events import Event


class IModule:
    def process(self, event: Event) -> None: ...


if __name__ == "__main__":
    raise Exception("This is a library and you should not run it directly!")
