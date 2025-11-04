class Scene():
    def __init__(self, number, header, description, location, time):
        self.number = number
        self.header = header
        self.description = description
        self.location = location
        self.time = time

    def __eq__(self, other):
        if not isinstance(other, Scene):
            return False
        return (
                self.number == other.number and
                self.header == other.header and
                self.description == other.description and
                self.location == other.location and
                self.time == other.time
        )