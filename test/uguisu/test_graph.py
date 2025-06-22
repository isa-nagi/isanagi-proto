import os
from uguisu.graph import TextNode, Edge, Graph


def main():
    a = TextNode(data="Aaa")
    b = TextNode(data="Bbbbb\nBbbbb")
    c = TextNode(data="Ccc")
    d = TextNode(data="Ddd")
    e = TextNode(data="Eee")
    f = TextNode(data="Fffff")
    g = TextNode(data="Ggg")
    h = TextNode(data="Hhh")
    i = TextNode(data="Iii")
    nodes = [a, b, c, d, e, f, g, h, i]
    edges = [
        Edge(a, b),
        Edge(a, c),
        Edge(b, d),
        Edge(c, f),
        Edge(c, e),
        Edge(e, e),
        Edge(f, g),
        Edge(f, h),
        Edge(g, h),
        Edge(h, i),
        Edge(i, h),
        Edge(i, f),
    ]
    graph = Graph()
    for node in nodes:
        graph.add_node(node)
    for edge in edges:
        graph.add_edge(edge)

    graph.arrange()

    for node in graph.nodes_by_rank:
        print(node.rank, node.data, node.rect)

    current_dir = os.path.dirname(__file__)
    out_fname = os.path.join(current_dir, "out", "graph.svg.html")
    with open(out_fname, "w") as fout:
        print(graph.to_svg(html=True), file=fout)


if __name__ == "__main__":
    main()
