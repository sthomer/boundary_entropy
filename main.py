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
        self.keys = set()
        self.counts_out = {}
        self.counts_in = {}
        self.total_out = {}
        self.total_in = {}
        self.entropy_out = {}
        self.entropy_in = {}

    def step(self, a, b):
        self.counts_out[a][b] = self.counts_out.setdefault(a, {}).setdefault(b, 0) + 1
        self.total_out[a] = self.total_out.setdefault(a, 0) + 1
        self.counts_in[b][a] = self.counts_in.setdefault(b, {}).setdefault(a, 0) + 1
        self.total_in[b] = self.total_in.setdefault(b, 0) + 1
        self.keys.update([a,b])

    def cache_entropy(self):
        self.entropy_out = {x: entropy(list(self.counts_out[x].values()), base=2)
                            for x in self.counts_out}
        self.entropy_in = {x: entropy(list(self.counts_in[x].values()), base=2)
                           for x in self.counts_in}


class Level:
    def __init__(self):
        self.map = DirectedAdjacency()
        self.segments = []
        self.ongoing = []

    def step(self, prev, curr):
        self.map.step(prev, curr)

    def segment(self, prev, curr):
        if self.is_boundary(prev, curr):
            self.segments += [self.ongoing]
            self.ongoing = []
        self.ongoing += [curr]

    def is_boundary(self, a, b):
        return self.map.entropy_in.get(a, 0) < self.map.entropy_in.get(b, 0) or \
               self.map.entropy_out.get(a, 0) < self.map.entropy_out.get(b, 0)

    def process(self, data):
        pairs = list(zip(data, data[1:]))
        for pair in pairs:
            self.step(*pair)
        self.map.cache_entropy()
        self.ongoing += [data[0]]
        for pair in pairs:
            self.segment(*pair)

    def predict(self, data, levels):
        self.map = levels.levels[0].map
        pairs = list(zip(data, data[1:]))
        self.ongoing += [data[0]]
        matches = 0
        for pair in pairs:
            guess = levels.predict(self.ongoing)
            matches += 1 if guess == pair[1] else 0
            self.segment(*pair)
        return matches

    def segmented(self):
        if len(self.segments) > 0:
            return [''.join(segment) for segment in self.segments]
        else:
            return [''.join(self.ongoing)]

    def symbols(self):
        return self.map.keys

    def count(self, k):
        return self.map.total_in[k]


class Hierarchy:
    def __init__(self):
        self.levels = []

    def push(self, level):
        self.levels += [level]

    def predict(self, ongoing):
        level = self.levels[1]
        ongoing = ''.join(ongoing)
        counts = {k[len(ongoing)]: level.count(k)
                  for k in level.symbols() if is_proper_prefix(ongoing, k)}
        if ongoing in level.symbols():
            base = level.count(ongoing)
            next = level.map.counts_out[ongoing]
            total = level.map.total_out[ongoing]
            nexts = {k: next[k] * base / total for k in next}
            for k in nexts:
                if k[0] in counts:
                    counts[k[0]] += nexts[k]
                else:
                    counts[k[0]] = nexts[k]
        return max(counts, key=lambda k: counts[k]) if len(counts) > 0 else None


def is_proper_prefix(x, y):
    return len(x) < len(y) and x == y[:len(x)]


def segmentation(filename, max_depth=25, binary=False):
    levels = Hierarchy()
    data = load(filename, binary)
    for i in range(max_depth):
        level = Level()
        level.process(data)
        data = level.segmented()
        levels.push(level)

        print("Stage:", i, sep='\t')
        print("Symbols:", len(level.symbols()), sep='\t')
        print("Sequence:", len(data), sep='\t')
        if len(data) == 1:
            break
    return levels


def prediction(filename, levels, max_depth=25, binary=False):
    data = load(filename, binary)[:int(1e5)]
    matches = Level().predict(data, levels)
    print("Matches:", matches)
    print("Proportion:", matches / len(data))


if __name__ == '__main__':
    file = 'data/moby-dick.txt'
    hierarchy = segmentation(file, max_depth=2)
    prediction(file, hierarchy)
