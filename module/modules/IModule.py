from events.Events import Event


class IModule:
    @staticmethod
    def process(event: Event) -> None: ...
