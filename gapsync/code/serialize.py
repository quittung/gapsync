import os, json

INDENTATION = 4

def dump_json(obj: object, fname: str) -> None:
    """Dumps an object to a json file.

    Args:
        obj (Any): Object to encode.
        fname (str): Filename of json file.
    """   
    dirname = os.path.dirname(fname)
    if dirname != "" and not os.path.exists(dirname): os.makedirs(dirname)
    
    with open(fname, 'w') as fobj:
        json.dump(obj, fobj, indent = INDENTATION)

def load_json(fname: str) -> object:
    """Loads a json file and returns the encoded object.

    Args:
        fname (str): Path to json file.

    Returns:
        Any: Object encoded in json file.
    """    
    with open(fname, 'r') as fobj:
        return json.loads(fobj.read())

def print_json(obj: object) -> None:
    print(json.dumps(obj, indent = INDENTATION))