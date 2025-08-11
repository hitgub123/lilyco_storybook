import React from 'react';
import Link from 'next/link';
import Head from 'next/head';

const Custom404: React.FC = () => {
  return (
    <>
      {/* 设置页面标题，显示在浏览器标签页上 */}
      <Head>
        <title>页面未找到 - 404</title>
      </Head>

      {/* 页面内容，您可以根据需要进行设计和样式调整 */}
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh', // 确保内容垂直居中
        backgroundColor: '#f8f8f8',
        fontFamily: 'Arial, sans-serif',
        color: '#333',
        padding: '20px',
        boxSizing: 'border-box'
      }}>
        <h1 style={{
          fontSize: '4em',
          color: '#e74c3c',
          margin: '0 0 10px 0'
        }}>
          404
        </h1>
        <h2 style={{
          fontSize: '1.8em',
          color: '#555',
          marginBottom: '20px',
          textAlign: 'center'
        }}>
          抱歉，页面未找到
        </h2>
        <p style={{
          fontSize: '1.1em',
          lineHeight: '1.5',
          textAlign: 'center',
          maxWidth: '600px',
          marginBottom: '30px'
        }}>
          您尝试访问的页面可能已被删除、名称已更改或暂时不可用。
        </p>
        
        {/* 返回首页的链接 */}
        <Link href="/">
          <a style={{
            display: 'inline-block',
            padding: '12px 25px',
            backgroundColor: '#3498db',
            color: 'white',
            textDecoration: 'none',
            borderRadius: '5px',
            fontSize: '1.1em',
            transition: 'background-color 0.3s ease',
            boxShadow: '0 2px 5px rgba(0,0,0,0.2)'
          }}
          onMouseEnter={(e) => e.currentTarget.style.backgroundColor = '#2980b9'}
          onMouseLeave={(e) => e.currentTarget.style.backgroundColor = '#3498db'}
          >
            返回首页
          </a>
        </Link>
      </div>
    </>
  );
};

export default Custom404;
