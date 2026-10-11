# heroliss/mkfun

## 项目用途

根据两个嵌套容器结构生成映射规则函数。ss_di.py 深度遍历 list、set、dict、tuple 并提取叶元素；ss.py 的 mkfun 根据 _from 和 _to 结构生成转换函数，并可反向验证。

## 当前状态

- 建议分类：Python 嵌套容器映射工具
- 生命周期：Dormant
- 最近 push：2016-08-07T08:19:50Z
- README 扫描状态：Missing

最新 push 为 2016-08-07，单次提交，长期冻结。适合标为个人工具脚本。

## 实际运行方式

在仓库根执行 python ss_di.py 查看遍历示例；在 Python REPL 中 from ss import mkfun，随后用 f=mkfun(from_obj,to_obj) 生成转换函数并调用。输入结构需要由使用者提供。

## 依赖与构建线索

Python 标准库，无 requirements、测试或许可证。

## 目录与证据

仓库只有 ss.py 和 ss_di.py；mkfun 使用正则和 eval 生成表达式，set 无序且输入不可信时存在风险。

顶层目录/文件线索：

- `ss_di.py`
- `ss.py`

## 已知限制

- 本文档只依据 GitHub 元数据、README、构建文件、入口文件和目录证据整理，未进行完整构建或端到端运行验证。
- 不确定的运行环境、密码、服务器地址和兼容版本不在此处臆测。

## 需要确认

是否还记得典型 from/to 示例？补一个示例会显著提高 README 可用性。

## 后续维护建议

1. 先确认“继续维护、完成冻结、历史保留、归档候选”中的一种状态。
2. 若继续保留，再补充一条可复现的运行验证记录和截图/输出。
3. 若确认完成或废弃，只保留简短历史说明，不需要改代码。

## 证据链接

- 仓库：[heroliss/mkfun](https://github.com/heroliss/mkfun)
- 默认分支：master
- 主要语言：Python
- stars / forks：0 / 0
- 扫描时间：2026-10-11T05:10:08Z
## 本地验证记录

在 Python 3.14 临时副本中运行 `python ss_di.py` 成功打印嵌套结构的叶元素序列；`ss.py` 的 `eval` 映射函数尚未用完整样例验证。
