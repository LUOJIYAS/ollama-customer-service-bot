import { ConfigProvider } from 'antd'
import type { AppProps } from 'next/app'
import zhCN from 'antd/locale/zh_CN'
import 'antd/dist/reset.css'
import '../styles/globals.css'

export default function App({ Component, pageProps }: AppProps) {
  return (
    <ConfigProvider locale={zhCN}>
      <Component {...pageProps} />
    </ConfigProvider>
  )
} 