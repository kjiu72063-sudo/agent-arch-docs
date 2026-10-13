#!/usr/bin/env node
/**
 * 端口诊断：找出"能真正被本机站点绑定"的端口。
 *
 * 为什么需要它 —— 两个都踩过的坑：
 *  1) 「端口空闲」≠「能绑定」：Windows 把部分端口段保留给 Hyper-V/WSL/Docker，
 *     落在其中的端口非管理员 bind 直接 EACCES。
 *  2) 「返回 200」≠「是我这个站点」：别人的前端 dev server 也做 SPA 兜底，
 *     任何路径都回 200。**必须比对 <title> 才能确认站点的身份。**
 *
 * 用法：
 *   node scripts/probe-ports.cjs                 # 探测默认候选列表
 *   node scripts/probe-ports.cjs 5180 5181       # 探测指定端口
 */
const net = require('net');
const http = require('http');

const DEFAULT_CANDIDATES = [4173, 4174, 4175, 5173, 5174, 5175, 5180, 8080, 8081, 8090, 3000, 9000];
const candidates = process.argv.slice(2).map(Number).filter(Boolean);
const list = candidates.length ? candidates : DEFAULT_CANDIDATES;

function tryBind(port) {
  return new Promise((resolve) => {
    const srv = net.createServer();
    srv.once('error', (e) => {
      try { srv.close(); } catch {}
      resolve({ ok: false, err: e.code });
    });
    srv.listen({ port, host: '0.0.0.0', exclusive: true }, () => {
      srv.close(() => resolve({ ok: true }));
    });
  });
}

function fetchTitle(port) {
  return new Promise((resolve) => {
    // 用 localhost（而非 127.0.0.1）：浏览器的行为就是这样，且 ::1 与 0.0.0.0 可能是两个不同进程
    const req = http.get({ host: 'localhost', port, path: '/', timeout: 1500 }, (res) => {
      let body = '';
      res.setEncoding('utf8');
      res.on('data', (c) => { body += c; if (body.length > 20000) req.destroy(); });
      res.on('end', () => {
        const m = body.match(/<title>([^<]*)<\/title>/i);
        resolve(m ? m[1].trim() : '(HTML 无 title)');
      });
    });
    req.on('timeout', () => { req.destroy(); resolve('(超时)'); });
    req.on('error', () => resolve(null)); // 无人监听
  });
}

(async () => {
  const rows = [];
  for (const port of list) {
    const bind = await tryBind(port);
    const title = bind.ok ? await fetchTitle(port) : null;
    let verdict;
    if (!bind.ok) {
      verdict = `不可绑定(${bind.err})`;
    } else if (title === null) {
      verdict = '真正空闲 ✔';
    } else {
      verdict = `被别人占用（title=${title}）✘`;
    }
    rows.push({ port, bind, title, verdict });
  }

  const pad = (s, n) => String(s).padEnd(n, ' ');
  console.log(pad('PORT', 7) + pad('BIND', 10) + 'SERVED-TITLE / VERDICT');
  for (const r of rows) {
    console.log(pad(r.port, 7) + pad(r.bind.ok ? 'ok' : 'fail', 10) + r.verdict);
  }
  const free = rows.find((r) => r.bind.ok && r.title === null);
  console.log('\nPICK=' + (free ? free.port : 'NONE（需要放宽候选列表）'));
})();
