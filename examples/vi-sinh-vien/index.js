import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.dirname(fileURLToPath(import.meta.url));
const HOST = process.env.HOST || "127.0.0.1";
const PORT = Number.parseInt(process.env.PORT || "5500", 10);
const TYPES = { ".html": "text/html; charset=utf-8", ".css": "text/css; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".json": "application/json; charset=utf-8", ".svg": "image/svg+xml" };

function send(res, code, body, contentType = "text/plain; charset=utf-8") {
  res.writeHead(code, { "Content-Type": contentType, "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store" });
  res.end(body);
}
const server = http.createServer((req, res) => {
  if (!["GET", "HEAD"].includes(req.method || "GET")) { res.setHeader("Allow", "GET, HEAD"); send(res, 405, "Method Not Allowed"); return; }
  let pathname;
  try { pathname = decodeURIComponent(new URL(req.url || "/", "http://" + HOST + ":" + PORT).pathname); }
  catch { send(res, 400, "Bad Request"); return; }
  if (pathname === "/") pathname = "/index.html";
  const filePath = path.resolve(ROOT, "." + pathname);
  const relative = path.relative(ROOT, filePath);
  if (relative.startsWith("..") || path.isAbsolute(relative)) { send(res, 403, "Forbidden"); return; }
  fs.stat(filePath, (error, stat) => {
    if (error || !stat.isFile()) { send(res, 404, "Không tìm thấy tệp."); return; }
    const mime = TYPES[path.extname(filePath).toLowerCase()] || "application/octet-stream";
    res.writeHead(200, { "Content-Type": mime, "X-Content-Type-Options": "nosniff", "Cache-Control": "no-store" });
    if (req.method === "HEAD") { res.end(); return; }
    const stream = fs.createReadStream(filePath);
    stream.on("error", () => { if (!res.headersSent) send(res, 500, "Internal Server Error"); else res.destroy(); });
    stream.pipe(res);
  });
});
server.on("error", error => {
  if (error.code === "EADDRINUSE") console.error("Cổng " + PORT + " đang được sử dụng. Hãy dừng máy chủ cũ hoặc đặt PORT=5501.");
  else console.error("Không thể khởi động máy chủ:", error.message);
  process.exitCode = 1;
});
server.listen(PORT, HOST, () => {
  console.log("Ví Sinh Viên đang chạy!");
  console.log("Mở trình duyệt: http://" + HOST + ":" + PORT);
  console.log("Nhấn Ctrl+C để dừng máy chủ.");
});
