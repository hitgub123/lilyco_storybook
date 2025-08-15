const fs = require('fs');
const path = require('path');

// --- 配置 ---
// CSV 文件路径 (相对于项目根目录)
const csvFilePath = path.join(__dirname, '..', 'asset', 'task.csv');
// 目标 API 地址
const apiUrl = 'http://127.0.0.1:8787/api/story'; // 假设您的本地服务运行在 8787 端口

/**
 * 将 ID 补零到指定长度
 * @param {string | number} id - 输入的 ID
 * @param {number} length - 目标长度
 * @returns {string} - 补零后的字符串
 */
function padId(id, length = 4) {
  return String(id).padStart(length, '0');
}

/**
 * 主函数
 */
async function main() {
  try {
    // 1. 读取 CSV 文件
    console.log(`正在读取 CSV 文件: ${csvFilePath}`);
    const fileContent = fs.readFileSync(csvFilePath, 'utf8');

    // 2. 解析 CSV 内容
    const lines = fileContent.trim().split('\n');
    const header = lines.shift().split(','); // 获取标题行

    // 找到 'id' 和 'text' 列的索引，这样更灵活
    const idIndex = header.indexOf('id');
    const textIndex = header.indexOf('text');

    if (idIndex === -1 || textIndex === -1) {
      console.error('错误: CSV 文件中必须包含 "id" 和 "text" 列。');
      return;
    }

    const jsonData = lines.map(line => {
      const values = line.split(','); // 注意：如果 text 列中包含逗号，这里会出错
      const id = values[idIndex];
      const text = values[textIndex];
      return {
        title: text,
        index: padId(id)
      };
    });

    console.log('成功生成 JSON 数据:');
    console.log(JSON.stringify(jsonData, null, 2));

    // 3. 发送 POST 请求
    console.log(`\n正在发送 POST 请求到 ${apiUrl}...`);
    const response = await fetch(apiUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(jsonData),
    });

    // 4. 处理响应
    if (response.ok) {
      const result = await response.json();
      console.log('请求成功! 服务器响应:');
      console.log(result);
    } else {
      console.error(`请求失败! 状态码: ${response.status}`);
      const errorText = await response.text();
      console.error('服务器错误信息:', errorText);
    }

  } catch (error) {
    console.error('执行脚本时发生错误:', error);
  }
}

// 运行主函数
main();
