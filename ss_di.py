__a = [['a', 'b'], 1, 2, (3, 4, [5, 6], 7, 8), 9, 10, {7, 6, 5}, {(2, 5): (6, 7), (3, 4): (2, 1, [4, 5, 6])}]  # 示例数组
all_types = (list, set, dict, tuple)  # 需要进去看的类型


def di(container):
    """按序取出多层嵌套数组结构里的元素(注意set类型中的元素无序）"""
    r = []
    if isinstance(container, dict):
        for i, j in container.items():
            r.extend(di(i))
            r.extend(di(j))
    elif isinstance(container, all_types):
        for i in container:
            r.extend(di(i))
    else:
        r.append(container)  # 此时container不是容器而是一个基本元素

    return r


if __name__ == '__main__':
    print(di(__a))
