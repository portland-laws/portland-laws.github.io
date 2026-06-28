#!/usr/bin/env node
import http from 'node:http';
import handler from '../api/openrouter/chat/completions.js';

const port = Number(process.env.PORT || process.env.OPENROUTER_PROXY_PORT || 8787);
const host = process.env.HOST || process.env.OPENROUTER_PROXY_HOST || '0.0.0.0';

function createResponseAdapter(res) {
  return {
    statusCode: 200,
    setHeader: (...args) => res.setHeader(...args),
    status(code) {
      this.statusCode = code;
      res.statusCode = code;
      return this;
    },
    json(payload) {
      if (!res.hasHeader('Content-Type')) {
        res.setHeader('Content-Type', 'application/json; charset=utf-8');
      }
      res.end(JSON.stringify(payload));
    },
    send(payload) {
      res.end(payload);
    },
    end(payload) {
      res.end(payload);
    },
  };
}

const server = http.createServer(async (req, res) => {
  if (req.url === '/health' || req.url === '/api/openrouter/health') {
    res.writeHead(200, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({
      ok: true,
      service: 'openrouter-proxy',
      configured: Boolean(process.env.OPENROUTER_API_KEY),
    }));
    return;
  }

  const pathname = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`).pathname;
  if (pathname !== '/api/openrouter/chat/completions' && pathname !== '/chat/completions') {
    res.writeHead(404, { 'Content-Type': 'application/json; charset=utf-8' });
    res.end(JSON.stringify({ error: 'Not found' }));
    return;
  }

  try {
    await handler(req, createResponseAdapter(res));
  } catch (error) {
    if (!res.headersSent) {
      res.writeHead(500, { 'Content-Type': 'application/json; charset=utf-8' });
    }
    res.end(JSON.stringify({
      error: 'OpenRouter proxy crashed',
      message: error instanceof Error ? error.message : String(error),
    }));
  }
});

server.listen(port, host, () => {
  console.log(`OpenRouter proxy listening on http://${host}:${port}`);
  console.log(`Chat endpoint: /api/openrouter/chat/completions`);
  console.log(`Allowed origins: ${process.env.OPENROUTER_PROXY_ALLOWED_ORIGINS || 'default'}`);
});
