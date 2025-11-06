import { getAssetFromKV } from "@cloudflare/kv-asset-handler";

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);

    try {
      // If user visits "/", try both index.html and hashed versions
      if (url.pathname === "/" || url.pathname.endsWith("/")) {
        try {
          // Try normal /index.html
          const asset = await getAssetFromKV(
            { request: new Request(url.origin + "/index.html", request), waitUntil: ctx.waitUntil }
          );
          return asset;
        } catch (err) {
          // Fallback to hashed version (like index.2234a815c9.html)
          const manifest = JSON.parse(env.__STATIC_CONTENT_MANIFEST);
          const hashedKey = Object.keys(manifest).find(k =>
            k.startsWith("index.") && k.endsWith(".html")
          );
          if (hashedKey) {
            const asset = await getAssetFromKV(
              { request: new Request(url.origin + "/" + hashedKey, request), waitUntil: ctx.waitUntil }
            );
            return asset;
          }
          throw err;
        }
      }

      // Normal asset serving
      const asset = await getAssetFromKV({ request, waitUntil: ctx.waitUntil });
      return asset;

    } catch (err) {
      return new Response("404 Not Found", { status: 404 });
    }
  },
};