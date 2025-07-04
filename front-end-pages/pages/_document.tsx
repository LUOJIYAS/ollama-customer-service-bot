import { Html, Head, Main, NextScript } from 'next/document'

export default function Document() {
  return (
    <Html lang="zh-CN">
      <Head>
        <meta charSet="utf-8" />
        <meta name="description" content="智能客服机器人 - 基于Ollama和ChromaDB的智能客服系统" />
        <meta name="keywords" content="智能客服,AI,客服机器人,Ollama,ChromaDB" />
        <meta name="author" content="AI Assistant" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      <body>
        <Main />
        <NextScript />
      </body>
    </Html>
  )
} 