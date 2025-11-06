export default {
  async fetch(request, env, ctx) {
    try {
      const url = new URL(request.url);

      // If root, serve index.html
      if (url.pathname === "/" || url.pathname.endsWith("/")) {
        url.pathname += "index.html";
      }

      // Serve from ASSETS binding
      const asset = await env.ASSETS.fetch(new Request(url.toString(), request));
      return asset;
    } catch (err) {
      return new Response("404 Not Found", { status: 404 });
    }
  },
};