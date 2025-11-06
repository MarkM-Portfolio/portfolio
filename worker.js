import { getAssetFromKV } from "@cloudflare/kv-asset-handler";

export default {
  async fetch(request, env, ctx) {
    try {
      return await getAssetFromKV(
        { request, waitUntil: ctx.waitUntil },
        { mapRequestToAsset: req => new Request(req.url, req) }
      );
    } catch (err) {
      return new Response("Not found", { status: 404 });
    }
  },
};
