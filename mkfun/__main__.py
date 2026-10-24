"""JSON 命令行，不接收 Python 表达式或外部代码。"""
import argparse
import json
import sys
from . import MappingError, compile_mapping, __version__


def read_json(text):
    if len(text) > 200_000:
        raise ValueError("JSON 超过 200,000 字符，请缩小输入。")
    return json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"不支持 {value}")))


def main(argv=None):
    # CLI 作为管道数据源时也使用 UTF-8，避免 Windows 旧代码页改变 JSON 字节。
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="mkfun：用两份嵌套样例生成数据重组规则。")
    parser.add_argument("--version", action="version", version=__version__)
    parser.add_argument("--from", dest="source", help="源样例 JSON")
    parser.add_argument("--to", dest="target", help="目标样例 JSON")
    parser.add_argument("--input", dest="data", help="新数据 JSON")
    parser.add_argument("--validate", action="store_true", help="校验本次输入能否反向还原")
    parser.add_argument("--explain", action="store_true", help="同时输出各目标叶的来源")
    args = parser.parse_args(argv)
    if all(v is None for v in (args.source, args.target, args.data)):
        source, target, data = ["姓名", "城市", "技能"], {"profile": {"name": "姓名", "city": "城市"}, "skills": ["技能"], "active": True}, ["Liss", "上海", "Unity"]
    elif any(v is None for v in (args.source, args.target, args.data)):
        parser.error("请同时提供 --from、--to 与 --input，或不带参数运行示例。")
    else:
        try:
            source, target, data = map(read_json, (args.source, args.target, args.data))
        except (ValueError, RecursionError) as exc:
            parser.exit(2, f"JSON 输入无效：{exc}\n")
    try:
        plan = compile_mapping(source, target, validate=args.validate)
        result = plan(data)
        output = {"result": result, "rules": plan.explain(), "warnings": plan.warnings} if args.explain else result
        print(json.dumps(output, ensure_ascii=False, indent=2, allow_nan=False))
    except MappingError as exc:
        parser.exit(2, f"映射失败：{exc}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
