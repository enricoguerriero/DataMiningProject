from entities.actual_route import ActualRoute
from entities.preferences import Preferences


class Driver:

    def __init__(self, id: str):
        self.id = id

    def route_for_driver(self, actual_route: ActualRoute):
        pass

    def preferences(self, driver_route: ActualRoute) -> Preferences:
        pass