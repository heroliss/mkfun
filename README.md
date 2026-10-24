# mkfun · 结构映射

用两份嵌套样例描述数据重组：源样例中的叶值标记输入位置，目标样例用相同值选择来源，未出现的值保留为常量。规则编译一次，可以反复应用到新数据。

```python
from mkfun import mkfun

convert = mkfun(
    ["姓名", "城市", "技能"],
    {"profile": {"name": "姓名", "city": "城市"}, "skills": ["技能"], "active": True},
    validate=True,
)
print(convert(["Liss", "上海", "Unity"]))
# {'profile': {'name': 'Liss', 'city': '上海'}, 'skills': ['Unity'], 'active': True}
```

这是一项源自 2016 年 mkfun 4.5 的结构实验。5.0 保留按样例编译转换的想法，提供 Python 库、JSON CLI 与暗色浏览器实验台。它做结构重排、重命名、常量填充和重复引用，不执行任意计算表达式，也不是机器学习模型。

## 开始使用

需要 Python 3.10 或更新版本；核心没有第三方运行依赖。在仓库根可直接导入，或运行 `python -m pip install .`。

```sh
python -m mkfun --explain
python -m mkfun --from '["x","y"]' --to '["y","x"]' --input '[10,20]' --validate
```

第二行在支持单引号传参的终端中输出 `[20, 10]`。Windows PowerShell 也可使用第一行内置示例，或在 Python 中直接调用 API。CLI 只解析 JSON，不接受 Python 表达式。

运行网页：

```sh
python -m http.server 8918 --bind 127.0.0.1
```

打开 [本地实验台](http://127.0.0.1:8918/web/)。可编辑源样例、目标样例和新数据，观察来源路径、常量及本次往返验证。Ctrl+Enter 执行；示例包含档案重组、矩阵转置和字典键值交换。HTML/CSS/JavaScript ES modules 无 CDN、无 npm 构建步骤，整体复制 `web/` 即可部署到任意静态子目录。

## 规则怎样工作

- **布局按位置匹配。** 新数据保持源样例的容器类型、层次与长度，标量内容可以替换。Python 字典按插入顺序先键后值遍历，键也参与映射。不要调换同形字段的顺序后期待按键名自动匹配。
- **样例值是占位符。** 数字按数值匹配，`1` 和 `1.0` 相同；布尔、数字、字符串分别识别。重复源值匹配首个位置，并在 `plan.warnings` 和网页中提示。占位符尽量使用不同且不会与固定字段名重合的词。
- **不是所有映射都可逆。** `validate=True` 检查本次输入的完整往返，丢掉字段、合并集合或键值替换造成的信息丢失会报错。通过一次输入不证明规则对所有数据都可逆。
- **支持明确的内建类型。** Python 支持 `list`、`tuple`、`dict`、`set` 以及 `None/bool/int/float/str/bytes`；集合按类型与值稳定排序。拒绝自定义对象、循环、非有限浮点数和不可匹配的结构；输出字典键碰撞会明确失败。
- **限制工作规模。** 每个结构最多 10,000 节点、64 层，Python 整数最多 4096 bit；CLI 与网页每份 JSON 最多 200,000 字符。输出设有 2,000,000 字符预算，Python 使用保守估算，避免重复引用放大结果。

Python 示例中的 `tuple/set/bytes` 不是 JSON 类型。网页使用原生 JavaScript 的 JSON 语义，对象键必须为字符串，整数必须处于精确范围；数字字符串键遵循 JavaScript 属性枚举顺序。有序数据推荐数组，不应把网页当作 Python 容器解释器。

## 查看编译计划

```python
from mkfun import compile_mapping

plan = compile_mapping(["甲", "乙"], {"first": "乙", "second": "甲"})
print(plan([3, 7]))        # {'first': 7, 'second': 3}
print(plan.explain())      # 每个目标叶的来源路径或常量
```

`MappingPlan` 保存样例的不可变快照。修改原样例或前一次输出不会改动规则。编译使用叶值索引和结构树，避免对所有源、目标叶逐对搜索；执行按结构重建数据，不生成或执行字符串代码。集合排序另需排序成本。

异常均继承 `MappingError`：`StructureError` 表示输入或样例不合约定，`OutputError` 表示输出键或规模受限，`ReverseValidationError` 表示本次往返不能还原。旧的 `from ss import mkfun` 与 `from ss_di import di` 仍是兼容入口。

## 验证

```sh
python -m unittest discover -s tests -v
node --test web/engine.test.mjs
```

Python 与网页共用 JSON 测试夹具，覆盖嵌套重组、转置、常量、类型区分、危险字符串作为纯数据、原型名称、结构不符、键碰撞与反向丢失；另测循环、深度、规模、样例冻结与重复调用。Node.js 只用于网页引擎测试，不是部署必需服务。

当前实测 Python 3.14 / Node.js 24，浏览器在 Windows Chrome 验证桌面与窄屏。测试不代表任意自定义对象、生产数据迁移或大规模 ETL 的支持承诺。

## 原始版本与目录

- `legacy/v4.5/`：来自手动备份的两份原始源码，和原 GitHub 源码字节一致；含校验摘要，不参与运行时导入。原实现使用正则与 `eval`，仅作历史查看。
- `mkfun/`：现代 Python 核心与 CLI。
- `ss.py`、`ss_di.py`：旧导入名兼容层。
- `web/`：独立静态实验台与 JavaScript 引擎。
- `tests/`：Python 测试及跨语言 JSON 夹具。

原始备份未被修改，Git 历史也保留早期实现。新版没有替换或加入新的许可证。
