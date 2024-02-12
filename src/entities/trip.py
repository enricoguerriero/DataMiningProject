from entities.merchandise import Merchandise


class Trip:

    def __init__(self, data):
        self.city_from = data.get('from', '')
        self.city_to = data.get('to', '')
        self.merchandise = Merchandise(data.get('merchandise', {1: 3}))

    def __str__(self):
        return f'city_from: {self.city_from}, city_to: {self.city_to}, {self.merchandise} \n'

    def __repr__(self):
        return str(self)
