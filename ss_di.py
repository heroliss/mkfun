"""旧di()名称兼容入口。"""
from mkfun import flatten as di

if __name__ == '__main__':
    print(di([['a', 'b'], 1, (2, 3), {'name': 'Liss'}]))
