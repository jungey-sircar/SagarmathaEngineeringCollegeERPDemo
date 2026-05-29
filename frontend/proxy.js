/**
 * Tiny HTTP proxy that forwards every request from port 3000 to the Django
 * ASGI app already exposed by supervisor on port 8001. Letting both supervisor
 * processes ultimately serve Django keeps the Kubernetes ingress (which routes
 * `/api/*` to 8001 and everything else to 3000) working out of the box.
 */
const http = require('http');
const httpProxy = require('http-proxy');

const TARGET = process.env.DJANGO_TARGET || 'http://127.0.0.1:8001';
const PORT = parseInt(process.env.PORT || '3000', 10);
const HOST = process.env.HOST || '0.0.0.0';

const proxy = httpProxy.createProxyServer({
  target: TARGET,
  changeOrigin: true,
  xfwd: true,
  ws: true,
  proxyTimeout: 60000,
});

proxy.on('error', (err, req, res) => {
  console.error('[proxy] error', err.message, 'for', req.method, req.url);
  if (res && !res.headersSent) {
    res.writeHead(502, { 'Content-Type': 'text/plain' });
    res.end('Bad gateway: ' + err.message);
  }
});

const server = http.createServer((req, res) => {
  proxy.web(req, res);
});

server.on('upgrade', (req, socket, head) => {
  proxy.ws(req, socket, head);
});

server.listen(PORT, HOST, () => {
  console.log(`[proxy] forwarding ${HOST}:${PORT} -> ${TARGET}`);
});
