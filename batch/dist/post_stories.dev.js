"use strict";

var fs = require('fs');

var path = require('path'); // --- 配置 ---
// CSV 文件路径 (相对于项目根目录)


var csvFilePath = path.join(__dirname, '..', 'asset', 'task.csv'); // 目标 API 地址

var apiUrl = 'http://127.0.0.1:8788/api/story'; // 假设您的本地服务运行在 8787 端口

/**
 * 将 ID 补零到指定长度
 * @param {string | number} id - 输入的 ID
 * @param {number} length - 目标长度
 * @returns {string} - 补零后的字符串
 */

function padId(id) {
  var length = arguments.length > 1 && arguments[1] !== undefined ? arguments[1] : 4;
  return String(id).padStart(length, '0');
}
/**
 * 主函数
 */


function main() {
  var fileContent, lines, header, idIndex, textIndex, jsonData, response, result, errorText;
  return regeneratorRuntime.async(function main$(_context) {
    while (1) {
      switch (_context.prev = _context.next) {
        case 0:
          _context.prev = 0;
          // 1. 读取 CSV 文件
          console.log("\u6B63\u5728\u8BFB\u53D6 CSV \u6587\u4EF6: ".concat(csvFilePath));
          fileContent = fs.readFileSync(csvFilePath, 'utf8'); // 2. 解析 CSV 内容

          lines = fileContent.trim().split('\n');
          header = lines.shift().split(','); // 获取标题行
          // 找到 'id' 和 'text' 列的索引，这样更灵活

          idIndex = header.indexOf('id');
          textIndex = header.indexOf('text');

          if (!(idIndex === -1 || textIndex === -1)) {
            _context.next = 10;
            break;
          }

          console.error('错误: CSV 文件中必须包含 "id" 和 "text" 列。');
          return _context.abrupt("return");

        case 10:
          jsonData = lines.map(function (line) {
            var values = line.split(','); // 注意：如果 text 列中包含逗号，这里会出错

            var id = values[idIndex];
            var text = values[textIndex];
            return {
              title: text,
              index: padId(id)
            };
          });
          console.log('成功生成 JSON 数据:');
          console.log(JSON.stringify(jsonData, null, 2)); // 3. 发送 POST 请求

          console.log("\n\u6B63\u5728\u53D1\u9001 POST \u8BF7\u6C42\u5230 ".concat(apiUrl, "..."));
          _context.next = 16;
          return regeneratorRuntime.awrap(fetch(apiUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(jsonData)
          }));

        case 16:
          response = _context.sent;

          if (!response.ok) {
            _context.next = 25;
            break;
          }

          _context.next = 20;
          return regeneratorRuntime.awrap(response.json());

        case 20:
          result = _context.sent;
          console.log('请求成功! 服务器响应:');
          console.log(result);
          _context.next = 30;
          break;

        case 25:
          console.error("\u8BF7\u6C42\u5931\u8D25! \u72B6\u6001\u7801: ".concat(response.status));
          _context.next = 28;
          return regeneratorRuntime.awrap(response.text());

        case 28:
          errorText = _context.sent;
          console.error('服务器错误信息:', errorText);

        case 30:
          _context.next = 35;
          break;

        case 32:
          _context.prev = 32;
          _context.t0 = _context["catch"](0);
          console.error('执行脚本时发生错误:', _context.t0);

        case 35:
        case "end":
          return _context.stop();
      }
    }
  }, null, null, [[0, 32]]);
} // 运行主函数


main();