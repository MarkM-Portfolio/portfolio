import { getAssetFromKV } from "@cloudflare/kv-asset-handler";

export default {
  async fetch(request, env, ctx) {
    try {
      // Map / and directories to /index.html
      const url = new URL(request.url);
      if (url.pathname.endsWith("/")) {
        url.pathname += "index.html";
        request = new Request(url.toString(), request);
      }

      const asset = await getAssetFromKV(
        { request, waitUntil: ctx.waitUntil },
        { mapRequestToAsset: (req) => req }
      );

      const headers = new Headers(asset.headers);
      headers.set("Cache-Control", "public, max-age=3600");

      return new Response(asset.body, { ...asset, headers });
    } catch (e) {
      return new Response("404 Not Found", { status: 404 });
    }
  },
};