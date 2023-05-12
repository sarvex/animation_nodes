import functools
from collections import defaultdict
from .. algorithms.hashing import strToEnumItemID

def enumItemsFromList(itemData):
    items = [
        (element, element, "", "NONE", strToEnumItemID(element))
        for element in itemData
    ]
    if not items:
        items = [("NONE", "NONE", "")]
    return items

cachedItemTuplesByHash = defaultdict(list)

def cacheEnumItems(itemsCB):

    @functools.wraps(itemsCB)
    def wrapper(self, context):
        itemTuples = tuple(itemsCB(self, context))
        itemTuplesHash = hash(itemTuples)

        for cachedItemTuple in cachedItemTuplesByHash[itemTuplesHash]:
            if cachedItemTuple == itemTuples:
                return cachedItemTuple
        else:
            cachedItemTuplesByHash[itemTuplesHash].append(itemTuples)
            return itemTuples

    return wrapper
