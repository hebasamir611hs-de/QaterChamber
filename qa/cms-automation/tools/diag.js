const { get } = require("./lib/rest-client");
const paths = [
  "/o/headless-admin-user/v1.0/my-user-account",
  "/o/headless-admin-site/v1.0/sites",
  "/o/headless-delivery/v1.0/sites",
  "/o/object-admin/v1.0/object-definitions?page=1&pageSize=3",
  "/o/c/newsarticles/scopes/37246?page=1&pageSize=2"
];
(async () => {
  for (const p of paths) {
    try {
      const r = await get(p);
      console.log("\n" + p);
      console.log("  =>", r.__notFound ? "404" : JSON.stringify(r).slice(0, 400));
    } catch (e) {
      console.log("\n" + p);
      console.log("  => ERR", e.status || "", e.kind || "", String(e.message).slice(0, 160));
    }
  }
})();
