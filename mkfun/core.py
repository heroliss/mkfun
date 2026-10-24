"""编译为不可变规则树；支持的值仅为明确列出的 Python 内建类型。"""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any


class MappingError(ValueError):
    """样例、输入或输出不能满足映射契约。"""


class StructureError(MappingError):
    """布局、容器类型、规模或标量类型不符合约定。"""


class OutputError(MappingError):
    """映射后的字典键或集合元素不满足 Python 容器约束。"""


class ReverseValidationError(MappingError):
    """本次实际输入无法通过反向映射原样还原。"""


@dataclass(frozen=True)
class _Node:
    kind: str
    value: Any = None
    children: tuple[_Node, ...] = ()


_SCALARS = {type(None): "none", bool: "bool", int: "int", float: "float", str: "str", bytes: "bytes"}
_CONTAINERS = {list: "list", tuple: "tuple", dict: "dict", set: "set"}
_RANK = {"none": 0, "bool": 1, "int": 2, "float": 3, "str": 4, "bytes": 5, "tuple": 6}


def _sort_key(value: Any, depth=0):
    """集合只接受内建标量/元组，排序不调用用户定义的 repr/比较。"""
    if depth > 64:
        raise StructureError("集合元素嵌套超过 64 层。")
    kind = _SCALARS.get(type(value))
    if kind:
        if kind == "float" and not math.isfinite(value):
            raise StructureError("集合不支持 NaN 或 Infinity。")
        return (_RANK[kind], 0 if value is None else value)
    if type(value) is tuple:
        return (6, tuple(_sort_key(item, depth + 1) for item in value))
    raise StructureError(f"集合含不支持的类型：{type(value).__name__}。")


def _snapshot(value: Any, *, max_depth: int = 64, max_nodes: int = 10_000) -> _Node:
    active: set[int] = set()
    count = 0

    def visit(item, depth, path):
        nonlocal count
        count += 1
        if count > max_nodes:
            raise StructureError(f"节点超过 {max_nodes} 个，请缩小数据。")
        if depth > max_depth:
            raise StructureError(f"{path}：嵌套超过 {max_depth} 层。")
        kind = _SCALARS.get(type(item))
        if kind:
            if kind == "float" and not math.isfinite(item):
                raise StructureError(f"{path}：不支持 NaN 或 Infinity。")
            if kind == "int" and item.bit_length() > 4096:
                raise StructureError(f"{path}：整数超过 4096 bit。")
            return _Node(kind, item)
        kind = _CONTAINERS.get(type(item))
        if not kind:
            raise StructureError(f"{path}：不支持 {type(item).__name__}；请使用内建容器和标量。")
        if len(item) > max_nodes:
            raise StructureError(f"{path}：容器节点超过 {max_nodes}，请缩小数据。")
        ident = id(item)
        if ident in active:
            raise StructureError(f"{path}：检测到循环引用。")
        active.add(ident)
        try:
            if kind == "dict":
                children = []
                for index, (key, val) in enumerate(item.items()):
                    children.append(visit(key, depth + 1, f"{path}<key:{index}>"))
                    children.append(visit(val, depth + 1, f"{path}<value:{index}>"))
            else:
                ordered = sorted(item, key=_sort_key) if kind == "set" else item
                children = [visit(child, depth + 1, f"{path}[{i}]") for i, child in enumerate(ordered)]
            return _Node(kind, children=tuple(children))
        finally:
            active.remove(ident)

    return visit(value, 0, "$")


def _entries(node: _Node, path="$"):
    if node.kind in _SCALARS.values():
        yield node, path
        return
    for index, child in enumerate(node.children):
        if node.kind == "dict":
            next_path = f"{path}<{'key' if index % 2 == 0 else 'value'}:{index // 2}>"
        else:
            next_path = f"{path}[{index}]"
        yield from _entries(child, next_path)


def flatten(value: Any) -> list:
    """按嵌套顺序提取叶；字典先键后值，集合按稳定的类型/值顺序。"""
    return [leaf.value for leaf, _ in _entries(_snapshot(value))]


def _same_shape(expected: _Node, actual: _Node, path="$"):
    if expected.kind in _CONTAINERS.values():
        if actual.kind != expected.kind or len(expected.children) != len(actual.children):
            raise StructureError(f"{path}：需要 {expected.kind} 布局（{len(expected.children)} 个子节点），实际为 {actual.kind}。")
        for index, (left, right) in enumerate(zip(expected.children, actual.children)):
            _same_shape(left, right, f"{path}[{index}]")
    elif actual.kind in _CONTAINERS.values():
        raise StructureError(f"{path}：需要标量位置，实际为 {actual.kind} 容器。")


def _rebuild(node: _Node, leaves: list, budget=None):
    if budget is None:
        budget = [0]
    if node.kind == "ref":
        value = leaves[node.value]
    elif not node.children and node.kind in _SCALARS.values():
        value = node.value
    else:
        value = None
    if node.kind == "ref" or node.kind in _SCALARS.values():
        budget[0] += len(value) * 6 + 8 if type(value) in (str, bytes) else len(str(value)) + 3 if type(value) is int else 32
        if budget[0] > 2_000_000:
            raise OutputError("输出超过 2,000,000 字符的保守预算，请减少重复或缩短内容。")
        return value
    items = [_rebuild(child, leaves, budget) for child in node.children]
    if node.kind == "list":
        return items
    if node.kind == "tuple":
        return tuple(items)
    if node.kind == "set":
        try:
            return set(items)
        except TypeError as exc:
            raise OutputError("输出集合包含不可哈希的元素，请检查输入数据类型。") from exc
    if node.kind == "dict":
        result = {}
        for i in range(0, len(items), 2):
            key, value = items[i:i + 2]
            try:
                if key in result:
                    raise OutputError(f"输出字典键重复：{key!r}；请使用不同的数据。")
                result[key] = value
            except TypeError as exc:
                raise OutputError("输出字典键不可哈希，请使用标量或只含可哈希元素的元组。") from exc
        return result
    raise MappingError("未知规则节点。")


@dataclass(frozen=True)
class MappingPlan:
    """冻结的转换计划；样例后续改动不会改变规则，可重复调用。"""

    _source: _Node
    _rule: _Node
    _source_paths: tuple[str, ...]
    _reverse: MappingPlan | None = None
    warnings: tuple[str, ...] = ()

    def __call__(self, value):
        return self.apply(value)

    def _apply(self, value):
        snapshot = _snapshot(value)
        _same_shape(self._source, snapshot)
        return _rebuild(self._rule, [leaf.value for leaf, _ in _entries(snapshot)])

    def apply(self, value):
        """检查输入布局并执行规则；开启验证时比较本次输入的完整往返。"""
        result = self._apply(value)
        if self._reverse:
            try:
                restored = self._reverse._apply(result)
                if _snapshot(restored) != _snapshot(value):
                    raise ReverseValidationError("反向结果与输入不一致；该映射会丢失或替换信息。")
            except MappingError as exc:
                if isinstance(exc, ReverseValidationError):
                    raise
                raise ReverseValidationError(f"不能反向还原本次输入：{exc}") from exc
        return result

    def explain(self) -> list[dict]:
        """每个目标叶的来源或常量；仅描述规则，不构造或执行 Python 代码。"""
        rows = []

        def walk(node, path):
            if node.kind == "ref":
                rows.append({"target_path": path, "source_path": self._source_paths[node.value], "source_index": node.value})
            elif node.kind in _SCALARS.values():
                rows.append({"target_path": path, "constant": node.value})
            else:
                for i, child in enumerate(node.children):
                    suffix = f"<{'key' if i % 2 == 0 else 'value'}:{i // 2}>" if node.kind == "dict" else f"[{i}]"
                    walk(child, path + suffix)

        walk(self._rule, "$")
        return rows


def compile_mapping(source, target, *, validate: bool = False) -> MappingPlan:
    """按样例叶值编译规则；布尔与数字独立，int/float 按数值匹配。"""
    src, dst = _snapshot(source), _snapshot(target)
    leaves = list(_entries(src))
    index = {}
    warnings = []
    for i, (leaf, path) in enumerate(leaves):
        key = ("number" if leaf.kind in ("int", "float") else leaf.kind), leaf.value
        if key in index:
            warnings.append(f"{path} 与 {leaves[index[key]][1]} 示例相同，目标匹配使用首个位置。")
        else:
            index[key] = i

    def compile_node(node):
        if node.kind in _SCALARS.values():
            found = index.get((("number" if node.kind in ("int", "float") else node.kind), node.value))
            return _Node("ref", found) if found is not None else node
        return _Node(node.kind, children=tuple(compile_node(child) for child in node.children))

    reverse = compile_mapping(target, source) if validate else None
    return MappingPlan(src, compile_node(dst), tuple(path for _, path in leaves), reverse, tuple(warnings))


def mkfun(_from, _to, validate=False):
    """兼容原 mkfun(_from, _to, validate=False) 的可调用返回值。"""
    return compile_mapping(_from, _to, validate=validate)
