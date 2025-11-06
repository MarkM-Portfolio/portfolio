import { getAssetFromKV } from "@cloudflare/kv-asset-handler";

export default {
  async fetch(request, env, ctx) {
    try {
      // Handle requests like / → /index.html
      const asset = await getAssetFromKV(
        { request, waitUntil: ctx.waitUntil },
        {
          mapRequestToAsset: (req) => {
            const url = new URL(req.url);
            if (url.pathname.endsWith("/")) {
              url.pathname += "index.html";
            } else if (!url.pathname.includes(".")) {
              // If it has no file extension (e.g. /about), treat as folder
              url.pathname += "/index.html";
            }
            return new Request(url.toString(), req);
          },
        }
      );

      return asset;
    } catch (e) {
      return new Response("404 Not Found", { status: 404 });
    }
  },
};