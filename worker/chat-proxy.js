/**
 * 茗视智农 · DeepSeek 聊天代理 Worker
 *
 * 部署到 Cloudflare Workers，把前端的聊天请求转发到 DeepSeek API。
 * API key 通过环境变量 DEEPSEEK_API_KEY 注入，不出现在代码里。
 *
 * 部署步骤：
 *   1. cloudflare.com → Workers & Pages → Create application → Create Worker
 *   2. 起名 mingshi-chat → Deploy → 在线编辑器粘贴本文件全部内容 → Save and Deploy
 *   3. 进 Worker 的 Settings → Variables and Secrets → Add variable
 *      - Type: Secret, Name: DEEPSEEK_API_KEY, Value: 你的 DeepSeek API key
 *   4. 拿到 Worker URL（类似 https://mingshi-chat.<用户名>.workers.dev）
 *   5. 把 URL 填到 index.html 的 WORKER_URL 常量
 *
 * 防护策略：
 *   - Origin 白名单只允许从 GitHub Pages / localhost 调用
 *   - 单条消息最长 2000 字
 *   - 整个对话历史最多 20 条
 */

const ALLOWED_ORIGINS = [
  'https://nadiaxx602.github.io',   // GitHub Pages
  'http://localhost:8000',           // 本地开发
  'http://127.0.0.1:8000',
];

const SYSTEM_PROMPT = '你是"茗视智农"演示系统中的 AI 助手。该系统是面向山地茶园场景的多 Agent 协同决策平台。' +
  '你扮演一个友好的智能植保顾问角色，但可以回答任何问题。' +
  '回答用简洁中文，控制在 200 字以内；如果用户问茶叶 / 种植 / 病虫害 / 农药 / 合规相关问题，可以更专业一些。';

function corsHeaders(origin) {
  const allowed = ALLOWED_ORIGINS.includes(origin) ? origin : ALLOWED_ORIGINS[0];
  return {
    'Access-Control-Allow-Origin': allowed,
    'Access-Control-Allow-Methods': 'POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
    'Access-Control-Max-Age': '86400',
  };
}

export default {
  async fetch(request, env) {
    const origin = request.headers.get('Origin') || '';

    // CORS 预检
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders(origin) });
    }

    if (request.method !== 'POST') {
      return new Response('Method not allowed', { status: 405, headers: corsHeaders(origin) });
    }

    // Origin 白名单防护（防止别人偷用你的 Worker 烧 token）
    if (!ALLOWED_ORIGINS.includes(origin)) {
      return new Response(JSON.stringify({ error: 'Origin not allowed' }), {
        status: 403,
        headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
      });
    }

    try {
      const body = await request.json();
      const messages = Array.isArray(body.messages) ? body.messages : [];

      // 限制对话历史长度
      if (messages.length > 20) {
        return new Response(JSON.stringify({ error: '对话历史过长（最多 20 条）' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
        });
      }

      // 限制单条消息长度
      for (const m of messages) {
        if (typeof m.content !== 'string' || m.content.length > 2000) {
          return new Response(JSON.stringify({ error: '消息内容过长（单条最多 2000 字）' }), {
            status: 400,
            headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
          });
        }
      }

      // 拼接 system prompt + 用户对话历史
      const fullMessages = [
        { role: 'system', content: SYSTEM_PROMPT },
        ...messages.filter((m) => m.role === 'user' || m.role === 'assistant'),
      ];

      // 调 DeepSeek API
      const upstream = await fetch('https://api.deepseek.com/v1/chat/completions', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${env.DEEPSEEK_API_KEY}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          model: 'deepseek-v4-flash',
          messages: fullMessages,
          temperature: 0.7,
          max_tokens: 600,
        }),
      });

      if (!upstream.ok) {
        const errText = await upstream.text();
        return new Response(JSON.stringify({
          error: `DeepSeek API ${upstream.status}: ${errText.slice(0, 200)}`,
        }), {
          status: 502,
          headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
        });
      }

      const data = await upstream.json();
      const reply = data.choices?.[0]?.message?.content?.trim()
        || '抱歉，我刚才没听清，请再说一遍。';
      const usage = data.usage || {};

      return new Response(JSON.stringify({
        reply,
        tokens: {
          prompt: usage.prompt_tokens || 0,
          completion: usage.completion_tokens || 0,
          total: usage.total_tokens || 0,
        },
      }), {
        headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
      });
    } catch (e) {
      return new Response(JSON.stringify({ error: String(e.message || e) }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', ...corsHeaders(origin) },
      });
    }
  },
};
