from entities.standard_route import StandardRoute


class ActualRoute(StandardRoute):

    def __init__(self, data):
        super().__init__(data)
        self.driver = data.get('driver', '')
        self.sroute = data.get('sroute', '')
