import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow local devices (e.g., phone/tablet on same Wi-Fi) to load dev assets.
  allowedDevOrigins: ["http://192.168.1.30:3000"],
};

export default nextConfig;
