import html as html_module
import math


class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ",".join(str(x) for x in (self.x, self.y))
        )


class Rect():
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def __repr__(self):
        return "{}({})".format(
            self.__class__.__name__,
            ",".join(str(x) for x in (self.x, self.y, self.w, self.h))
        )

    @property
    def x0(self):
        return self.x

    @property
    def y0(self):
        return self.y

    @property
    def x1(self):
        return self.x + self.w

    @property
    def y1(self):
        return self.y + self.h

    @property
    def p0(self):
        return Point(self.x, self.y)

    @property
    def p1(self):
        return Point(self.x1, self.y1)

    @property
    def cx(self):
        return self.x + self.w / 2

    @property
    def cy(self):
        return self.y + self.h / 2

    @cx.setter
    def cx(self, value):
        self.x += value - self.cx

    @cy.setter
    def cy(self, value):
        self.y += value - self.cy


class Node():
    def __init__(self, **kwargs):
        self.rect = Rect(0, 0, 0, 0)
        self.data = kwargs.get('data')
        self.rank = -1
        self._srcs = list()
        self._dsts = list()
        self._cyclic_srcs = list()
        self._cyclic_dsts = list()
        self._outer_srcs = list()
        self._outer_dsts = list()
        self.margin = Point(20, 10)

    @property
    def x(self):
        return self.rect.x

    def _walk_dsts_by_depth(self):
        def _walk(node, visited):
            visited.append(node)
            yield node, True  # go foward
            for child in node._dsts:
                if child not in visited:
                    for _ in _walk(child, visited): yield _  # noqa
            yield node, False  # go back

        rest = [self]
        visited = []
        while len(rest) > 0:
            first = rest[0]
            for _ in _walk(first, visited): yield _  # noqa
            for node in visited:
                if node in rest:
                    rest.remove(node)

    @property
    def dsts_by_depth(self):
        return [n for n, g in self._walk_dsts_by_depth() if g]

    def dsts_except_relay(self):
        dsts = self._dsts[:]
        for i in range(len(dsts)):
            while isinstance(dsts[i], RelayNode):
                dsts[i] = dsts[i]._dsts[0]
        c_srcs = self._cyclic_srcs[:]
        for i in range(len(c_srcs)):
            while isinstance(c_srcs[i], RelayNode):
                c_srcs[i] = c_srcs[i]._cyclic_srcs[0]
        return dsts + c_srcs

    def srcs_except_relay(self):
        srcs = self._srcs[:]
        for i in range(len(srcs)):
            while isinstance(srcs[i], RelayNode):
                srcs[i] = srcs[i]._srcs[0]
        c_dsts = self._cyclic_dsts[:]
        for i in range(len(c_dsts)):
            while isinstance(c_dsts[i], RelayNode):
                c_dsts[i] = c_dsts[i]._cyclic_dsts[0]
        return srcs + c_dsts


class RelayNode(Node):
    def __init__(self):
        super().__init__()
        self.data = "<relay>"
        self.rect = Rect(0, 0, 4, 2)
        self.margin = Point(10, 10)


class TextNode(Node):
    def __init__(self, data):
        super().__init__(data=data)
        self.lineheight = 22
        self.fontsize = Point(10, 16)
        self.padding = Point(8, 8)
        self._init_size()

    def _init_size(self):
        lines = self.data.split('\n')
        self.rect.w = max(len(x) for x in lines) * self.fontsize.x + self.padding.x * 2
        self.rect.h = len(lines) * self.lineheight + self.padding.y * 2

    def to_svg(self):
        ss = list()
        ss.append('<g font-family="mono" fill="black" font-size="16">')
        for i, line in enumerate(self.data.split('\n')):
            s = '<text x="{}" y="{}">{}</text>'.format(
                self.rect.x + self.padding.x,
                self.rect.y + self.padding.y + 16 + i * self.lineheight,
                html_module.escape(line)
            )
            ss.append(s)
        ss.append('</g>')
        return '\n'.join(ss)


class Edge():
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst
        src._dsts.append(dst)
        dst._srcs.append(src)
        self._relays: list[Node] = list()


class Graph():
    DEFAULT_CONFIG = {
        'margin': 10,
        'path': "curve",
        'short-cyclic': True,
        'edge-dy': 10,
        'marker-size': 6,
    }

    def __init__(self):
        self.nodes: list[Node] = list()
        self.edges: list[Edge] = list()
        self.config = dict(Graph.DEFAULT_CONFIG.items())

    @property
    def x(self):
        if len(self.nodes) > 0:
            return min(n.rect.x for n in self.nodes)
        return 0

    @property
    def y(self):
        if len(self.nodes) > 0:
            return min(n.rect.y for n in self.nodes)
        return 0

    @property
    def w(self):
        if len(self.nodes) > 0:
            n1 = self.nodes[0]
            for n in self.nodes:
                if n.rect.x1 > n1.rect.x1:
                    n1 = n
            return n1.rect.x1 + n1.margin.x + self.config['margin'] * 2
        return 0

    @property
    def h(self):
        if len(self.nodes) > 0:
            n1 = self.nodes[0]
            for n in self.nodes:
                if n.rect.y1 > n1.rect.y1:
                    n1 = n
            return n1.rect.y1 + n1.margin.y + self.config['margin'] * 2
        return 0

    def set_config(self, config):
        self.config.update(config)

    def add_node(self, obj):
        if isinstance(obj, Node):
            self.nodes.append(obj)
            return
        raise ValueError("Unknown obj type: {}".format(type(obj)))

    def add_edge(self, *args):
        if len(args) == 1 and isinstance(args[0], Edge):
            self.edges.append(args[0])
            return
        elif len(args) == 2 and all([isinstance(x, Node) for x in args]):
            edge = Edge(*args)
            self.edges.append(edge)
            return
        raise ValueError()

    def arrange(self):
        self._build_first_graph()
        self._add_relay_nodes()
        self._move_node_vertically()
        self._move_node_horizontally()

    @property
    def nodes_by_rank(self):
        nodes = sorted(self.nodes, key=lambda n: n.rank)
        return nodes

    @property
    def _nodes_by_depth(self):
        nodes = list()
        firsts = [n for n in self.nodes if len(n._srcs) == 0]
        for first in firsts:
            nodes += first.dsts_by_depth
        return nodes

    def _build_first_graph(self):
        # separate cyclic edges
        rests = self.nodes[:]
        while len(rests) > 0:
            for node in rests[0].dsts_by_depth:
                if node in rests:
                    rests.remove(node)
                cyc_srcs = list()
                for n in node.dsts_by_depth:
                    if node in n._dsts:
                        cyc_srcs.append(n)
                for src in cyc_srcs:
                    node._srcs.remove(src)
                    node._cyclic_srcs.append(src)
                    src._dsts.remove(node)
                    src._cyclic_dsts.append(node)
        # compute rank of nodes
        rests = self._nodes_by_depth
        for node in rests[:]:
            srcs = [n for n in node._srcs if n in self.nodes]
            if len(srcs) == 0:
                if node == self.nodes[0]:
                    node.rank = 0
                else:
                    node.rank = 1
                rests.remove(node)
        while len(rests) > 0:
            for node in rests[:]:
                srcs = [n for n in node._srcs if n in self.nodes]
                if all([n.rank >= 0 for n in srcs]):
                    node.rank = max([n.rank for n in node._srcs if n in self.nodes]) + 1
                    rests.remove(node)
        # separate outer edges
        for node in self.nodes:
            tgts = list()
            for n in node._dsts:
                if n not in self.nodes:
                    tgts.append(n)
            for tgt in tgts:
                node._dsts.remove(tgt)
                node._outer_dsts.append(tgt)
                tgt._srcs.remove(node)
                tgt._outer_srcs.append(node)

    def _nodes_split_by_rank(self):
        nodes = sorted(self.nodes, key=lambda n: n.rank)
        ranks = [list()]
        rank = 0
        for node in nodes:
            if node.rank != rank:
                ranks.append(list())
                rank = node.rank
            ranks[node.rank].append(node)
        return ranks

    def _add_relay_nodes(self):
        rests = self.nodes[:]
        for node in rests:
            for dst in node._dsts[:]:
                diff_rank = dst.rank - node.rank
                if diff_rank > 1:
                    relays = list()
                    for i in range(diff_rank - 1):
                        relay = RelayNode()
                        relays.append(relay)
                    relays[0]._srcs.append(node)
                    relays[0].rank = node.rank + 1
                    node._dsts.remove(dst)
                    node._dsts.append(relays[0])
                    for i in range(1, len(relays)):
                        relays[i]._srcs.append(relays[i - 1])
                        relays[i].rank = relays[i - 1].rank + 1
                    for i in range(0, len(relays) - 1):
                        relays[i]._dsts.append(relays[i + 1])
                    relays[-1]._dsts.append(dst)
                    dst._srcs.remove(node)
                    dst._srcs.append(relays[-1])
                    for relay in relays:
                        self.add_node(relay)
                    edge = self.__find_edge(node, dst)
                    edge._relays = relays[:]
            for dst in node._cyclic_dsts[:]:
                diff_rank = node.rank - dst.rank
                if diff_rank > 1:
                    relays = list()
                    for i in range(diff_rank - 1):
                        relay = RelayNode()
                        relays.append(relay)
                    relays[0]._cyclic_srcs.append(node)
                    relays[0].rank = node.rank - 1
                    node._cyclic_dsts.remove(dst)
                    node._cyclic_dsts.append(relays[0])
                    for i in range(1, len(relays)):
                        relays[i]._cyclic_srcs.append(relays[i - 1])
                        relays[i].rank = relays[i - 1].rank - 1
                    for i in range(0, len(relays) - 1):
                        relays[i]._cyclic_dsts.append(relays[i + 1])
                    relays[-1]._cyclic_dsts.append(dst)
                    dst._cyclic_srcs.remove(node)
                    dst._cyclic_srcs.append(relays[-1])
                    for relay in relays:
                        self.add_node(relay)
                    edge = self.__find_edge(node, dst)
                    edge._relays = list(reversed(relays[:]))

    def _move_node_vertically(self):
        sum_h = self.config['margin']
        for nodes in self._nodes_split_by_rank():
            max_h = max(n.rect.h for n in nodes)
            max_margin = max(n.margin.y for n in nodes)
            for node in nodes:
                if isinstance(node, RelayNode):
                    node.rect.h = max_h
                node.rect.y = sum_h
                node.rect.y += (max_h - node.rect.h) / 2
                node.rect.y += max_margin - node.margin.y
            sum_h += max_h + max_margin * 2

    def _move_node_horizontally(self):
        self._sort_to_avoid_cross_edge()
        self._arrange_nodes_to_avoid_overlap()
        for i in range(2):
            self._move_nodes_based_on_dependency()
            self._arrange_nodes_to_avoid_overlap()
        self._move_relays()
        self._move_to_fit_within_area()

    def _sort_to_avoid_cross_edge(self):
        new_nodes = list()
        for nodes in self._nodes_split_by_rank():
            # Set x [0..100]
            for i, node in enumerate(nodes):
                node.rect.cx = (i + 1) / (len(nodes) + 1) * 100
            # Set x based on srcs position
            if len(new_nodes) > 1:
                for node in nodes:
                    # srcs = node._srcs
                    srcs = node._srcs + node._cyclic_dsts
                    if len(srcs) > 0:
                        center = sum(n.rect.cx for n in srcs) / len(srcs)
                        node.rect.cx = center
            # update node order in same rank
            new_nodes = nodes[:]
            for node in new_nodes:
                self.nodes.remove(node)
            new_nodes.sort(key=lambda n: n.rect.cx)
            for node in new_nodes:
                self.nodes.append(node)
            # reset x [0..100]
            for i, node in enumerate(new_nodes):
                node.rect.cx = (i + 1) / (len(new_nodes) + 1) * 100

    def _arrange_nodes_to_avoid_overlap(self):
        for nodes in self._nodes_split_by_rank():
            nodes_sorted = sorted(nodes, key=lambda n: n.rect.cx)
            for i in range(20):
                # left to right
                n = nodes_sorted[0]
                next_x = n.rect.cx - n.rect.w / 2 - n.margin.x
                for ni, n in enumerate(nodes_sorted):
                    if (n.rect.cx - n.rect.w / 2 - n.margin.x) < next_x:
                        if isinstance(n, RelayNode):
                            n.rect.cx = next_x + n.rect.w / 2 + n.margin.x
                        else:
                            for nn in nodes_sorted[ni:]:
                                nn.rect.cx += (n.rect.w / 2 + n.margin.x) * 0.1
                    next_x = n.rect.cx + n.rect.w / 2 + n.margin.x
                # right to left
                n = nodes_sorted[-1]
                next_x = n.rect.cx + n.rect.w / 2 + n.margin.x
                for ni, n in enumerate(reversed(nodes_sorted)):
                    if (n.rect.cx + n.rect.w / 2 + n.margin.x) > next_x:
                        if isinstance(n, RelayNode):
                            n.rect.cx = next_x - n.rect.w / 2 - n.margin.x
                        else:
                            for nn in list(reversed(nodes_sorted))[ni:]:
                                nn.rect.cx -= (n.rect.w / 2 + n.margin.x) * 0.1
                    next_x = n.rect.cx - n.rect.w / 2 - n.margin.x

    def _move_nodes_based_on_dependency(self):
        new_x = {}
        for nodes in self._nodes_split_by_rank():
            for node in nodes:
                if isinstance(node, RelayNode):
                    continue
                deps = []
                for src in node._srcs:
                    src_dsts = src.dsts_except_relay()
                    deps.append({'x': src.rect.cx, 'n': len(src_dsts)})
                for dst in node._dsts:
                    dst_srcs = dst.srcs_except_relay()
                    deps.append({'x': dst.rect.cx, 'n': len(dst_srcs)})
                c = 1
                for d in deps:
                    c *= d['n']
                sum_c_ci_xi = sum_c_ci = 0
                for d in deps:
                    if d['n']:
                        sum_c_ci_xi += c / d['n'] * d['x']
                        sum_c_ci += c / d['n']
                new_x[node] = sum_c_ci_xi / sum_c_ci if sum_c_ci else node.rect.cx
        for nodes in self._nodes_split_by_rank():
            for node in nodes:
                if isinstance(node, RelayNode):
                    continue
                node.rect.cx = new_x[node]

    def __move_until_hit(self, node, dx, ranks):
        ranks = [n for n in ranks if n == node or not isinstance(n, RelayNode)]
        nodes = sorted(ranks, key=lambda n: n.rect.cx)
        i = nodes.index(node)
        if dx < 0 and i > 0:
            left = nodes[i - 1].rect.x1 + nodes[i - 1].margin.x
            dx = max(dx, left - (node.rect.x - node.margin.x))
        elif dx > 0 and i < len(nodes) - 1:
            right = nodes[i + 1].rect.x - nodes[i + 1].margin.x
            dx = min(dx, right - (node.rect.x1 + node.margin.x))
        node.rect.cx += dx

    def __has_cross_edge(self, node0, node1, ranks0, ranks1):
        for n0 in ranks0:
            for n1 in ranks1:
                if node0.rect.cx > n0.rect.cx and node1.rect.cx < n1.rect.cx:
                    return True
                if node0.rect.cx < n0.rect.cx and node1.rect.cx > n1.rect.cx:
                    return True
        return False

    def _move_relays(self):
        ranknodes = list()
        for nodes in self._nodes_split_by_rank():
            ranknodes.append(nodes)
        for edge in self.edges:
            if len(edge._relays) == 0:
                continue
            pass
            avg = sum(r.rect.cx for r in edge._relays) / len(edge._relays)
            for relay in edge._relays:
                # ranks = ranknodes[relay.rank]
                # self.__move_until_hit(relay, avg - relay.rect.cx, ranks)
                relay.rect.cx = avg
        pass

    def _move_to_fit_within_area(self):
        min_x = min(n.rect.x - n.margin.x for n in self.nodes)
        for node in self.nodes:
            node.rect.x -= min_x

    def __find_edge(self, src, dst):
        for e in self.edges:
            if e.src == src and e.dst == dst:
                return e
        raise ValueError()

    def __index_down_edge(self, node, tgt):
        edges = [e for e in self.edges if node in (e.src, e.dst)]
        edges = [e for e in edges if node.rank < max(e.src.rank, e.dst.rank)]

        def sortkey(edge):
            if len(edge._relays) > 0:
                return edge._relays[0].rect.cx
            else:
                return edge.dst.rect.cx

        tgts = sorted(edges, key=sortkey)
        src, dst = tgt
        for idx, n in enumerate(tgts):
            if src == n.src and dst == n.dst:
                return (idx, len(tgts))
        raise ValueError()

    def __index_up_edge(self, node, tgt):
        edges = [e for e in self.edges if node in (e.src, e.dst)]
        edges = [e for e in edges if node.rank > min(e.src.rank, e.dst.rank)]

        def sortkey(edge):
            if len(edge._relays) == 0:
                return edge.dst.rect.cx
            else:
                return edge._relays[-1].rect.cx

        tgts = sorted(edges, key=sortkey)
        src, dst = tgt
        for idx, n in enumerate(tgts):
            if src == n.src and dst == n.dst:
                return (idx, len(tgts))
        raise ValueError()

    def __draw_line(self, points):
        s = '<path class="g_arrow" d="{}{}" marker-end="url(#arrow)" />'.format(
            'M{},{}'.format(points[0].x, points[0].y),
            ''.join('L{},{}'.format(pt.x, pt.y) for pt in points[1:]),
        )
        return s

    def __draw_curve(self, points):
        c_strs = list()
        for ci in range(1, len(points), 3):
            c_pt_strs = ' '.join('{},{}'.format(pt.x, pt.y) for pt in points[ci:ci + 3])
            c_str = 'C{}'.format(c_pt_strs)
            c_strs.append(c_str)
        s = '<path class="g_arrow" d="{}{}" marker-end="url(#arrow)" />'.format(
            'M{},{}'.format(points[0].x, points[0].y),
            ' '.join(c_strs),
        )
        return s

    def __mid_point(self, pt0, pt1, ratio):
        return Point(
            pt0.x + (pt1.x - pt0.x) * ratio,
            pt0.y + (pt1.y - pt0.y) * ratio,
        )

    def __ctrl_point(self, points, number):
        rad1 = math.atan2((points[1].y - points[0].y), (points[1].x - points[0].x + 0.01))
        rad2 = math.atan2((points[1].y - points[2].y), (points[1].x - points[2].x + 0.01))
        rad = (rad1 + rad2) / 2 + math.pi / 2
        dx = 10
        if number == 0:
            rad += math.pi
            d = math.sqrt(
                (points[1].y - points[0].y) ** 2 + min(dx, points[1].x - points[0].x) ** 2
            )
            return Point(
                points[1].x + math.cos(rad) * d * 0.2,
                points[1].y + math.sin(rad) * d * 0.2,
            )
        else:
            d = math.sqrt(
                (points[1].y - points[2].y) ** 2 + min(dx, points[1].x - points[2].x) ** 2
            )
            return Point(
                points[1].x + math.cos(rad) * d * 0.2,
                points[1].y + math.sin(rad) * d * 0.2,
            )

    def to_svg(self, html=False, title='Untitled Graph'):
        linetype = self.config['path']
        # short_cyclic = self.config['short-cyclic']
        # edge_dy = self.config['edge-dy']
        marker_size = self.config['marker-size']

        ss = list()
        if html:
            ss += (
                '<html>',
                '<head>',
                '<meta charset="utf-8" />',
                '<title>{}</title>'.format(title),
                '<style>',
                'a.g_arrow {',
                '  stroke: black;',
                '  stroke-width: 1.5;',
                '  fill: none;',
                '  pointer-events: stroke;',
                '}',
                'a.g_arrow:hover, a.g_arrow:focus {',
                '  stroke: red;',
                '}',
                '</style>',
                '</head>',
                '<body>',
                '<div>',
            )
        s = {
            'x': self.x,
            'y': self.y,
            'width': self.w,
            'height': self.h,
            'xmlns': "http://www.w3.org/2000/svg",
            'xmlns:xlink': "http://www.w3.org/1999/xlink",
            'version': "1.1",
        }
        s = " ".join(f'{k}="{v}"' for k, v in s.items())

        ss.append(f"<svg {s}>")
        if linetype == 'line':
            ss.append('\n'.join((
                '<defs>',
                '<marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5"',
                ' markerUnits="strokeWidth" markerWidth="{0}" markerHeight="{0}" orient="auto">'.format(marker_size),
                '  <polygon points="0,0 0,10 10,5" fill="#000" id="arrow"/>',
                '</marker>',
                '<marker id="circle-arrow" viewBox="0 0 10 10" refX="10" refY="5"',
                ' markerUnits="strokeWidth" markerWidth="{0}" markerHeight="{0}" orient="auto">'.format(marker_size),
                '  <polygon points="0,0 0,10 10,5" fill="#000" id="arrow"/>',
                '</marker>',
                '</defs>',
            )))
        elif linetype == 'curve':
            ss.append('\n'.join((
                '<defs>',
                # '<marker id="arrow" viewBox="0 0 10 10" refX="2" refY="5"',
                '<marker id="arrow" viewBox="0 0 10 10" refX="10" refY="5"',
                ' markerUnits="strokeWidth" markerWidth="6" markerHeight="6" orient="auto">',
                '  <polygon points="0,0 0,10 10,5" fill="#000" id="arrow"/>',
                '</marker>',
                '<marker id="circle-arrow" viewBox="0 0 10 10" refX="10" refY="5"',
                ' markerUnits="strokeWidth" markerWidth="6" markerHeight="6" orient="auto">',
                '  <polygon points="0,0 0,10 10,5" fill="#000" id="arrow"/>',
                '</marker>',
                '</defs>',
            )))

        for node in self.nodes:
            if isinstance(node, RelayNode):
                continue
            s = {
                'x': node.rect.x,
                'y': node.rect.y,
                'width': node.rect.w,
                'height': node.rect.h,
                'stroke': '#000',
                'fill': '#fff',
                'stroke-width': 1,
            }
            s = " ".join(f'{k}="{v}"' for k, v in s.items())
            s = f"<rect {s} />"
            ss.append(s)
            if isinstance(node, TextNode):
                s = node.to_svg()
                ss.append(s)
        for node in self.nodes:
            if isinstance(node, RelayNode):
                continue
            for dst in node._dsts:
                ss.append('<a class="g_arrow" xlink:href="#0">')
                points = list()
                if isinstance(dst, RelayNode):
                    path = list()
                    path.append(node)
                    while isinstance(dst, RelayNode):
                        path.append(dst)
                        dst = dst._dsts[0]
                    path.append(dst)
                    dwn_idx, dwn_len = self.__index_down_edge(node, (node, dst))
                    upr_idx, upr_len = self.__index_up_edge(dst, (node, dst))
                    x0_offset = (dwn_idx + 1) / (dwn_len + 1) * node.rect.w
                    xN_offset = (upr_idx + 1) / (upr_len + 1) * dst.rect.w
                    # compute relay points
                    points = list()
                    points.append(Point(
                        path[0].rect.x + x0_offset,
                        path[0].rect.y1,
                    ))
                    for i in range(1, len(path) - 1):
                        points.append(Point(
                            path[i].rect.cx,
                            path[i].rect.y,
                        ))
                        points.append(Point(
                            path[i].rect.cx,
                            path[i].rect.y1,
                        ))
                    points.append(Point(
                        path[-1].rect.x + xN_offset,
                        path[-1].rect.y,
                    ))
                    # compute control points
                    if linetype == 'line':
                        pass
                    elif linetype == 'curve':
                        points2 = list()
                        points2.append(points[0])
                        # points2.append(Point(
                        #     points[0].x,
                        #     points[0].y + edge_dy,
                        # ))
                        points2.append(self.__mid_point(points[0], points[1], 0.2))
                        for i in range(1, len(points) - 1):
                            points2.append(self.__ctrl_point(points[i - 1: i + 2], 0))
                            points2.append(points[i])
                            points2.append(self.__ctrl_point(points[i - 1: i + 2], 1))
                        # points2.append(Point(
                        #     points[-1].x,
                        #     points[-1].y - edge_dy,
                        # ))
                        points2.append(self.__mid_point(points[-1], points[-2], 0.2))
                        points2.append(points[-1])
                        points = points2
                    # arrange points to fit int
                    for pi in range(len(points)):
                        points[pi].x = int(points[pi].x)
                        points[pi].y = int(points[pi].y)
                else:
                    dwn_idx, dwn_len = self.__index_down_edge(node, (node, dst))
                    upr_idx, upr_len = self.__index_up_edge(dst, (node, dst))
                    x0_offset = (dwn_idx + 1) / (dwn_len + 1) * node.rect.w
                    xN_offset = (upr_idx + 1) / (upr_len + 1) * dst.rect.w
                    points = list()
                    points.append(Point(
                        node.rect.x + x0_offset,
                        node.rect.y1,
                    ))
                    points.append(Point(
                        dst.rect.x + xN_offset,
                        dst.rect.y,
                    ))
                    if linetype == 'line':
                        pass
                    elif linetype == 'curve':
                        points.insert(-1, self.__mid_point(points[0], points[-1], 0.2))
                        points.insert(-1, self.__mid_point(points[-1], points[0], 0.2))
                        # points.insert(-1, Point(
                        #     node.rect.x + x0_offset,
                        #     node.rect.y1 + edge_dy,
                        # ))
                        # points.insert(-1, Point(
                        #     dst.rect.x + xN_offset,
                        #     dst.rect.y - edge_dy,
                        # ))
                if linetype == 'line':
                    ss.append(self.__draw_line(points))
                elif linetype == 'curve':
                    ss.append(self.__draw_curve(points))
                ss.append('</a>')
            for dst in node._cyclic_dsts:
                ss.append('<a class="g_arrow" xlink:href="#0">')
                if dst.rank == node.rank:
                    s = '<path class="g_arrow" d="M{},{}a{}" marker-end="url(#circle-arrow)" />'
                    s = s.format(
                        node.rect.x1,
                        node.rect.cy + 5,
                        ','.join(str(x) for x in [
                            12, 7,
                            0, 1, 0,
                            0, -10,
                        ]),
                    )
                    ss.append(s)
                elif isinstance(dst, RelayNode):
                    path = list()
                    path.append(node)
                    while isinstance(dst, RelayNode):
                        path.append(dst)
                        dst = dst._cyclic_dsts[0]
                    path.append(dst)
                    dwn_idx, dwn_len = self.__index_down_edge(dst, (node, dst))
                    upr_idx, upr_len = self.__index_up_edge(node, (node, dst))
                    x0_offset = (upr_idx + 1) / (upr_len + 1) * node.rect.w
                    xN_offset = (dwn_idx + 1) / (dwn_len + 1) * dst.rect.w
                    # compute relay points
                    points = list()
                    points.append(Point(
                        path[0].rect.x + x0_offset,
                        path[0].rect.y,
                    ))
                    for i in range(1, len(path) - 1):
                        points.append(Point(
                            path[i].rect.cx,
                            path[i].rect.y1,
                        ))
                        points.append(Point(
                            path[i].rect.cx,
                            path[i].rect.y,
                        ))
                    points.append(Point(
                        path[-1].rect.x + xN_offset,
                        path[-1].rect.y1,
                    ))
                    # compute control points
                    if linetype == 'line':
                        pass
                    elif linetype == 'curve':
                        points2 = list()
                        points2.append(points[0])
                        # points2.append(Point(
                        #     points[0].x,
                        #     points[0].y - edge_dy,
                        # ))
                        points2.append(self.__mid_point(points[0], points[1], 0.2))
                        for i in range(1, len(points) - 1):
                            points2.append(self.__ctrl_point(points[i - 1: i + 2], 1))
                            points2.append(points[i])
                            points2.append(self.__ctrl_point(points[i - 1: i + 2], 0))
                        # points2.append(Point(
                        #     points[-1].x,
                        #     points[-1].y + edge_dy,
                        # ))
                        points2.append(self.__mid_point(points[-1], points[-2], 0.2))
                        points2.append(points[-1])
                        points = points2
                    # arrange points to fit int
                    for pi in range(len(points)):
                        points[pi].x = int(points[pi].x)
                        points[pi].y = int(points[pi].y)
                else:
                    dwn_idx, dwn_len = self.__index_down_edge(dst, (node, dst))
                    upr_idx, upr_len = self.__index_up_edge(node, (node, dst))
                    x0_offset = (upr_idx + 1) / (upr_len + 1) * node.rect.w
                    xN_offset = (dwn_idx + 1) / (dwn_len + 1) * dst.rect.w
                    points = list()
                    points.append(Point(
                        node.rect.x + x0_offset,
                        node.rect.y,
                    ))
                    points.append(Point(
                        dst.rect.x + xN_offset,
                        dst.rect.y1,
                    ))
                    if linetype == 'line':
                        pass
                    elif linetype == 'curve':
                        # points.insert(-1, Point(
                        #     node.rect.x + x0_offset,
                        #     node.rect.y - edge_dy,
                        # ))
                        # points.insert(-1, Point(
                        #     dst.rect.x + xN_offset,
                        #     dst.rect.y1 + edge_dy,
                        # ))
                        points.insert(-1, self.__mid_point(points[0], points[-1], 0.2))
                        points.insert(-1, self.__mid_point(points[-1], points[0], 0.2))
                if dst.rank == node.rank:
                    pass
                elif linetype == 'line':
                    ss.append(self.__draw_line(points))
                elif linetype == 'curve':
                    ss.append(self.__draw_curve(points))
                ss.append('</a>')
        # ss.append('</g>')
        ss.append("</svg>")
        ss.append("</div>")
        if html:
            ss += (
                '</body>',
                '</html>',
            )
        s = "\n".join(ss)
        return s
