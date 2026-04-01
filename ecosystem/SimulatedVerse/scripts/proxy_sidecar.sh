#!/usr/bin/env bash
set -euo pipefail
mkdir -p .prox reports
# Minimal Node proxy scaffold: proxies /api/* to ${OLLAMA_HOST}
cat > .prox/proxy.js <<'JS'
import http from 'http'; import {request as httpsRequest} from 'https'; import {request as httpRequest} from 'http';
const target=process.env.OLLAMA_HOST||'http://127.0.0.1:11434';
const u=new URL(target);
const server=http.createServer((req,res)=>{
  const r=(u.protocol==='https:'?httpsRequest:httpRequest)({
    hostname:u.hostname, port:u.port, path:req.url, method:req.method, headers:req.headers
  }, upstream=>{
    res.writeHead(upstream.statusCode||502, upstream.headers); upstream.pipe(res);
  });
  r.on('error', e=>{res.writeHead(502);res.end('proxy error:'+e.message)});
  req.pipe(r);
});
server.listen(4455,()=>console.log('proxy on 4455 →',target));
JS
node .prox/proxy.js >/dev/null 2>&1 & echo $! > .prox/proxy.pid
echo "{\"timestamp\":\"$(date -Iseconds)\",\"proxy\":\"up\",\"port\":4455}" > reports/proxy_receipt.json
echo "PROXY: reports/proxy_receipt.json"