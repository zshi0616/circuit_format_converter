from re import X


class UnionFind(object):
    """并查集类"""
    def __init__(self, n):
        """长度为n的并查集"""
        self.uf = []
        for i in range(n):
            self.uf.append(i)
        self.sets_count = n                     # 判断并查集里共有几个集合, 初始化默认互相独立

    def find(self, p):
        if self.uf[p] == p:
            return p
        else:
            return self.find(self.uf[p])

    def union(self, p, q):
        """连通p,q 让q指向p"""
        proot = self.find(p)
        qroot = self.find(q)
        self.uf[proot] = qroot

    def is_connected(self, p, q):
        """判断pq是否已经连通"""
        return self.find(p) == self.find(q)     # 即判断两个结点是否是属于同一个祖先