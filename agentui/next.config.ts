import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  output: 'standalone',
  devIndicators: false,
  compress: true,
  poweredByHeader: false,
}

export default nextConfig