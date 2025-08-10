/** @type {import('next').NextConfig} */
const nextConfig = {
  output: process.env.NODE_ENV === 'production' ? 'export' : undefined,
  // output: 'export',
  images: {
    unoptimized: true,
    domains: ['res.cloudinary.com'],
  },
};

module.exports = nextConfig;