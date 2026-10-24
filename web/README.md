# 静态实验台

无需 npm 安装或前端构建。`index.html`、`style.css`、`app.mjs` 和 `engine.mjs` 均使用相对路径，可整体复制到任意静态子目录或 iframe 中。

在仓库根运行 `python -m http.server 8918 --bind 127.0.0.1`，打开 `http://127.0.0.1:8918/web/`。ES module 应通过 HTTP 打开，不能直接双击 HTML 使用 file 协议。

运行 JavaScript 引擎验证：`node --test web/engine.test.mjs`。与 Python 共用 `tests/json-fixtures.json`；网页只承诺 JSON 子集，Python 另支持 tuple、set、bytes 和可哈希字典键。

数据不上传、不写 localStorage；刷新重置。原生 JSON.parse 按 JavaScript 规则处理对象属性和数字：整数必须在精确范围，数字字符串键按属性枚举顺序。需要严格顺序时用数组，样例与新数据保留相同布局与顺序。
