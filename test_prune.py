from lxml import etree

def prune_tree(tree: etree._Element) -> etree._Element | None:
    children = tree.xpath('./*')
    if len(children) == 0:
        return None
    for child in children:
        if isinstance(child, etree._Element):
            replaced = prune_tree(child)
            if replaced is not None:
                tree.replace(child, replaced)
            else:
                tree.remove(child)
        elif isinstance(child, str) and len(child.strip()) == 0:
            tree.remove(child)
    return tree

if __name__ == "__main__":
    with open('whee.html', 'r') as f:
        tree = prune_tree(etree.HTML(f.read()))
        print(etree.tostring(tree).decode('utf8'))
