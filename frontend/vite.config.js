import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // 환경 변수 로드
  const env = loadEnv(mode, process.cwd(), '')
  
  // 환경별 설정
  const isProduction = mode === 'prod' || mode === 'production'
  const isDev = mode === 'dev' || mode === 'development'
  
  console.log(`[Vite] 빌드 모드: ${mode}`)
  console.log(`[Vite] 환경 파일: .env.${mode}`)
  
  return {
    base: '/dollkongbot/',
    plugins: [react()],
    server: {
      port: 3005,
      proxy: isDev ? {
        // 개발 환경에서만 프록시 사용
        '/api/dollkongbot/': {
          target: env.VITE_PROXY_TARGET || 'http://127.0.0.1:5000/',
          changeOrigin: true,
          secure: false,
          configure: (proxy, _options) => {
            proxy.on('error', (err, _req, _res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, _res) => {
              console.log('Sending Request to the Target:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, _res) => {
              console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
            });
          },
        }
      } : undefined,
      allowedHosts: ['www.yncsmart.com', 'yncsmart.com', 'localhost']
    },
    build: {
      outDir: 'dist',
      sourcemap: !isProduction, // 운영 환경에서는 소스맵 비활성화 (선택사항)
      minify: isProduction ? 'esbuild' : false, // 로컬 빌드 시 디버깅 용이
      emptyOutDir: true,
      rollupOptions: {
        output: {
          manualChunks: isProduction ? {
            // 운영 환경에서만 코드 스플리팅 최적화
            vendor: ['react', 'react-dom', 'react-router-dom'],
            ui: ['react-select', 'react-dropzone', 'react-toastify'],
          } : undefined
        }
      }
    },
    define: {
      // 빌드 시점의 환경 정보를 전역 상수로 주입
      '__BUILD_MODE__': JSON.stringify(mode),
      '__IS_PRODUCTION__': JSON.stringify(isProduction),
      '__IS_DEV__': JSON.stringify(isDev),
    }
  }
})
