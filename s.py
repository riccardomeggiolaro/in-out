class Weigher:
    def __init__(self, self_config, name):
        self.s = self_config
        self.name = name
        print(self.s.name)

class Config:
    def __init__(self):
        self.name = "kjuewfhnkojiefwqnjhl"
        self.weighers = []

    def addWeigher(self):
        w = Weigher(self_config=self, name="jewfojkln")
        self.weighers.append(w)
        
c = Config()

c.addWeigher()

c.name = "kjwefkjhewfjklnhfewdjklnh"

print(c.name)