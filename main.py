from scipy.stats import entropy


def load(filename, binary=False):
    if not binary:
        with open(filename) as file:
            text = file.readlines()
        return [c.lower() for line in text for c in line
                if c.isalnum() and c.isascii()]
    else:
        with open(filename, 'rb') as file:
            text = list(file.read())
            return ''.join([f'{i:08b}' for i in text])


class DirectedAdjacency:
    def __init__(self):
        self.outgoing = {}
        self.incoming = {}

    def step(self, a, b):
        self.outgoing[a][b] = self.outgoing.setdefault(a, {}).setdefault(b, 0) + 1
        self.incoming[b][a] = self.incoming.setdefault(b, {}).setdefault(a, 0) + 1

    def entropy_out(self, x):
        return entropy(list(self.outgoing[x].values()), base=2)

    def entropies_out(self):
        return {x: self.entropy_out(x) for x in self.outgoing}

    def entropy_in(self, x):
        return entropy(list(self.incoming[x].values()), base=2)

    def entropies_in(self):
        return {x: self.entropy_in(x) for x in self.incoming}


class Level:
    def __init__(self):
        self.map = DirectedAdjacency()
        self.segments = []
        self.ongoing = []

    def step(self, prev, curr):
        self.map.step(prev, curr)

    def cache(self):
        e_in = self.map.entropies_in()
        e_out = self.map.entropies_out()
        return e_in, e_out

    def segment(self, prev, curr, e_in, e_out):
        if self.is_boundary(prev, curr, e_in, e_out):
            self.segments += [self.ongoing]
            self.ongoing = []
        self.ongoing += [curr]

    def is_boundary(self, a, b, e_in, e_out):
        return e_in.get(a, 0) < e_in.get(b, 0) or e_out.get(a, 0) < e_out.get(b, 0)

    def process(self, data):
        pairs = list(zip(data, data[1:]))
        for pair in pairs:
            self.step(*pair)
        entropies = self.cache()
        self.ongoing += [data[0]]
        for pair in pairs:
            self.segment(*pair, *entropies)

    def symbols(self):
        if len(self.segments) > 0:
            return [''.join(segment) for segment in self.segments]
        else:
            return [''.join(self.ongoing)]


def segmentation(filename, max=25, binary=False):
    data = load(filename, binary)
    print(data[:100])
    for i in range(max):
        level = Level()
        level.process(data)
        data = level.symbols()
        print("Stage:", i, sep='\t')
        print("Symbols:", len(level.map.incoming), sep='\t')
        print("Sequence:", len(data), sep='\t')
        if len(data) == 1:
            break


if __name__ == '__main__':
    file = 'data/ensemble.txt'
    segmentation(file)
