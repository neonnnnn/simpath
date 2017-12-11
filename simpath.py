import sys
import timeit


class GridGraph(object):
    def __init__(self, N):
        self.N= N
        self.edges = []
        self.N_vertex = (N+1)*(N+1)
        vertex_counter = 1
        for i in  range(N):
            for j in range(i+1):
                self.edges.append((vertex_counter, i+vertex_counter+1))
                self.edges.append((vertex_counter, i+vertex_counter+2))
                vertex_counter += 1
        vertex_counter = (N+1)*(N+1)
        for i in range(N):
            for j in range(i+1):
                self.edges.append((vertex_counter-i-1, vertex_counter))
                self.edges.append((vertex_counter-i-2, vertex_counter))
                vertex_counter -= 1

        self.edges.sort(key=lambda x:x[1])
        self.edges.sort(key=lambda x:x[0])


class ZDDNode(object):
    def __init__(self, depth, mate, s, t):
        self.depth = depth
        self.s = s
        self.t = t
        self.mate = dict(mate)
        self.child = [None, None]
        self.counter = 0

    def update_mate(self, edge):
        p, q = edge
        if not p in self.mate:
            self.mate.update({p:p})
        if not q in self.mate:
            self.mate.update({q:q})

        end_p = self.mate[p]
        end_q = self.mate[q]
        # if p is the end of (sub) path
        if self.get_degree(p) == 1:
            self.mate[p] = 0
            self.mate[end_p] = end_q
        else:
            self.mate[p] = end_q
        # if q is the end of (sub) path
        if self.get_degree(q) == 1:
             self.mate[q] = 0
             self.mate[end_q]  = end_p
        else:
            self.mate[q] = end_p

    def to_key(self):
        key = ','.join(map(str, self.mate.keys())) + '|'
        key += ','.join(map(str, self.mate.values()))
        return key

    def get_degree(self, p):
        if not p in self.mate or self.mate[p] == p:
            return 0
        elif self.mate[p] == 0:
            return 2
        else:
            return 1

    def is_path(self, edge, x):
        if x==0 :
            return 2
        p, q = edge
        p_deg = self.get_degree(p)
        q_deg = self.get_degree(q)
        # for all node,0<=degree<=2
        if p_deg == 2 or q_deg == 2:
            return 0
        # degree of s or t must be 1
        if (p==self.s or p==self.t) and p_deg == 1:
            return 0
        if (q==self.s or q==self.t) and q_deg == 1:
            return 0

        if not q in self.mate:
            mate_q = q
        else:
            mate_q = self.mate[q]
        if not p in self.mate:
            mate_p = p
        else:
            mate_p = self.mate[p]

        # for cycle
        if mate_p == q and mate_q == p:
            return 0

        # if s and t are connected by connecting p and s,
        # mate must contain s or t or p or q and its degree must be 1
        if (mate_p==self.s and mate_q==self.t) or (mate_p==self.t and mate_q==self.s):
            for v in self.mate:
                if self.get_degree(v) == 1:
                    if not v in [self.s, self.t, p, q]:
                        return 0
            return 1
        else:
            return 2

    def del_from_mate(self, edges, p):
        is_path = True
        if len(edges) > self.depth:
            if edges[self.depth][0] != p and (p in self.mate):
                if p == self.s or p == self.t:
                    if self.get_degree(p) == 0:
                        is_path = False
                else:
                    if self.get_degree(p) == 1:
                        is_path = False
                del self.mate[p]
        return is_path


class ZDD(object):
    def __init__(self, grid_graph):
        self.grid_graph = grid_graph
        self.edges = self.grid_graph.edges
        self.max_depth = len(self.edges)
        self.s = 1
        self.t = self.edges[-1][-1]
        self.root = ZDDNode(0, {1:1}, self.s, self.t)
        self.root.counter = 1
        self.zero = ZDDNode('zero', {}, self.s, self.t)
        self.one = ZDDNode('one', {}, self.s, self.t)
        self.nodes = [[] for _ in range(self.max_depth+1)]
        self.nodes[0].append(self.root)

    def count_st_path(self):
        mate_list = {self.root.to_key():self.root}
        # for all edges
        for depth, e in enumerate(self.edges):
            sys.stdout.write('\r depth: {0}/{1}'.format(depth+1, self.max_depth))
            mate_dict = {}
            p, q = e
            # for all existing nodes
            for node in self.nodes[depth]:
                # 0-edge, 1-edge
                for x in [0, 1]:
                    type_child = node.is_path(e, x)
                    if type_child == 0:
                        node.child[x] = self.zero
                    elif type_child == 1:
                        node.child[x] = self.one
                    else:
                        ch = ZDDNode(depth+1, node.mate, self.s, self.t)
                        # if 1-edge, update mate array
                        if x:
                            ch.update_mate(e)
                        # decide delete or leave p from mate and check path
                        if not ch.del_from_mate(self.edges, p):
                            node.child[x] = self.zero
                        else:
                            key = ch.to_key()
                            # Does same node exist?
                            if key in mate_dict:
                                node.child[x] = mate_dict[key]
                            else:
                                node.child[x] = ch
                                mate_dict.update({key:ch})
                                self.nodes[depth+1].append(node.child[x])
                    node.child[x].counter += node.counter
            mate_dict.clear()
        print('\nThe number of s-t path:{0}'.format(self.one.counter))
        return self.one.counter

if __name__ == '__main__':
    N = int(sys.argv[1])
    grid_graph = GridGraph(N)
    print('Grid:{0}'.format(N))
    print('Number of Edges:{0}'.format(len(grid_graph.edges)))
    zdd = ZDD(grid_graph)
    s = timeit.default_timer()
    results = zdd.count_st_path()
    print('time:{0:5f}s'.format(timeit.default_timer() - s))
