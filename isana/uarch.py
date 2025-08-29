class Processor():
    def __init__(self, **kwargs):
        self.isa = None
        for k, v in kwargs.items():
            setattr(self, k, v)
