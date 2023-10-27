from itertools import islice


def batched(iterable, n):
    # batched('ABCDEFG', 3) --> ABC DEF G
    # pode ser removido ao usar python 3.12, em favor de itertools.batched
    if n < 1:
        raise ValueError('n must be at least one')
    it = iter(iterable)
    while batch := tuple(islice(it, n)):
        yield batch
