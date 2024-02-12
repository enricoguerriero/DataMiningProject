class Merchandise:

    def __init__(self, data: dict):
        self.item = list(data.keys())
        self.quantity = list(data.values())

    def __add__(self, other: 'Merchandise') -> 'Merchandise':
        if other is None:
            return Merchandise(dict(zip(self.item, self.quantity)))
        result_data = {}
        for item, quantity in zip(self.item, self.quantity):
            result_data[item] = result_data.get(item, 0) + quantity
        for item, quantity in zip(other.item, other.quantity):
            result_data[item] = result_data.get(item, 0) + quantity
        result_merchandise = Merchandise(result_data)
        return result_merchandise
    
    def __str__(self) -> str:
        return f'Merchandise: {dict(zip(self.item, self.quantity))}'

    def __repr__(self):
        return str(self)
