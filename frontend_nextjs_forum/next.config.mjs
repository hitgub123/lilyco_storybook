/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // output: 'export',
  output: process.env.NODE_ENV === 'production' ? 'export' : undefined,
  async rewrites() {
    return [
      {
        // source: '/workers-api{/}?',
        source: '/workers-api{/}?',
        destination: 'http://localhost:8788/api/',
      },
    ];
  },
};

export default nextConfig;
