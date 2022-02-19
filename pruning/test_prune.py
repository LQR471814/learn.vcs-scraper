from lxml import etree
from utils import prune_tree

if __name__ == "__main__":
    with open('whee.html', 'r') as f:
        tree = prune_tree(etree.HTML(f.read()))
        print(etree.tostring(tree).decode('utf8'))
