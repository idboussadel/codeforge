import path from "path";
import { loadEnvConfig } from "@next/env";
import type { NextConfig } from "next";

// ponytail: load monorepo root .env — one file for web + api
loadEnvConfig(path.join(__dirname, "../.."));

const nextConfig: NextConfig = {
  reactCompiler: true,
};

export default nextConfig;
