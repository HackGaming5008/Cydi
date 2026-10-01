"""Modern browser UI for Cydonia. Run with ``python ui.py``."""

import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import main as chatbot


HOST = "127.0.0.1"
PORT = 8765
messages = [{"role": "system", "content": chatbot.build_system_prompt() + "\n\n"
            "Tool-use rules: When a user explicitly asks you to remember, save, or store a "
            "durable fact, you must call the appropriate memory tool before saying it was saved. "
            "Never claim a tool succeeded unless its result confirms success. For questions about "
            "the user's saved information, call memory_search or memory_read first."}]
conversation_lock = threading.Lock()


PAGE = r'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#111218">
<title>Cydonia — AI chat</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root{color-scheme:dark;--ink:#f6f5fb;--muted:#9b9aa8;--line:#ffffff13;--glass:#ffffff0b;--accent:#b6a0ff;--mint:#a8eed6}
*{box-sizing:border-box}body{margin:0;min-height:100vh;background:#111218;color:var(--ink);font-family:'DM Sans',sans-serif;overflow:hidden}
.aurora{position:fixed;inset:0;overflow:hidden;pointer-events:none;background:radial-gradient(ellipse at 50% -30%,#383052 0,transparent 55%),linear-gradient(145deg,#111218,#15151c 52%,#111218)}
.orb{position:absolute;border-radius:50%;filter:blur(90px);opacity:.23;animation:drift 18s ease-in-out infinite alternate}.orb.a{width:420px;height:420px;background:#805de9;top:12%;left:-220px}.orb.b{width:360px;height:360px;background:#258e88;right:-180px;bottom:7%;animation-delay:-8s}
@keyframes drift{to{transform:translate(70px,-35px) scale(1.14)}}
.app{position:relative;height:100dvh;max-width:1120px;margin:auto;display:flex;flex-direction:column;padding:0 34px}
header{height:78px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);flex:none}
.brand{display:flex;align-items:center;gap:12px}.logo{width:37px;height:37px;border-radius:13px;background:linear-gradient(145deg,#cfbaff,#8570e8);display:grid;place-items:center;box-shadow:0 5px 24px #9879ff45;color:#17131f;font-size:18px;font-weight:800}.brand-name{font:700 16px Manrope,sans-serif;letter-spacing:-.3px}.brand-sub{font-size:11px;color:var(--muted);margin-top:2px}
.header-right{display:flex;align-items:center;gap:14px}.online{display:flex;align-items:center;gap:7px;color:#c4c1ce;font-size:12px}.dot{width:7px;height:7px;border-radius:50%;background:#66d9a8;box-shadow:0 0 12px #66d9a899}.new-chat{border:1px solid var(--line);color:#dedce6;background:#ffffff08;border-radius:11px;padding:9px 13px;font:500 12px 'DM Sans';cursor:pointer;transition:.2s}.new-chat:hover{background:#ffffff12;border-color:#ffffff2c}
main{flex:1;min-height:0;overflow-y:auto;scrollbar-width:thin;scrollbar-color:#ffffff25 transparent;padding:32px 5px 24px}.welcome{min-height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:10px 0 45px}.welcome-mark{width:60px;height:60px;border:1px solid #c9b6ff39;border-radius:21px;background:linear-gradient(145deg,#cbb9ff25,#9180dc0d);display:grid;place-items:center;color:#c8b7ff;font-size:27px;box-shadow:0 12px 55px #9d80fa18;margin-bottom:23px}.welcome h1{font:700 clamp(30px,5vw,43px) Manrope,sans-serif;letter-spacing:-1.8px;margin:0 0 12px;background:linear-gradient(100deg,#fff 20%,#cfc3ff 75%);color:transparent;background-clip:text}.welcome p{color:var(--muted);font-size:14px;margin:0 0 34px;line-height:1.65}.suggestions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px;width:min(600px,100%)}.suggestion{background:#ffffff07;border:1px solid var(--line);border-radius:16px;padding:15px 16px;text-align:left;color:#dcdae5;font:500 12px 'DM Sans';cursor:pointer;transition:.2s}.suggestion:hover{background:#ffffff10;border-color:#c0a9ff44;transform:translateY(-2px)}.suggestion span{display:block;color:#a9a5b6;font-size:11px;margin-top:5px;font-weight:400}
.thread{width:min(740px,100%);margin:0 auto;display:flex;flex-direction:column;gap:25px}.message{display:flex;gap:13px;align-items:flex-start;animation:appear .25s ease-out}.message.user{justify-content:flex-end}.avatar{width:30px;height:30px;flex:none;border-radius:11px;background:linear-gradient(145deg,#bea8ff,#8071dc);display:grid;place-items:center;color:#1b1726;font-weight:800;font-size:12px}.bubble{max-width:min(82%,650px);font-size:14px;line-height:1.75;white-space:pre-wrap;overflow-wrap:anywhere}.assistant .bubble{padding:2px 0;color:#e5e3eb}.user .bubble{padding:12px 16px;border-radius:19px 19px 5px 19px;background:#ffffff10;border:1px solid #ffffff12;color:#f4f2fa}.thinking{color:#b8b4c3}.typing{display:inline-flex;gap:4px;margin-left:8px;vertical-align:middle}.typing i{width:5px;height:5px;background:#c6b3ff;border-radius:50%;animation:pulse 1s infinite}.typing i:nth-child(2){animation-delay:.15s}.typing i:nth-child(3){animation-delay:.3s}@keyframes pulse{50%{opacity:.25;transform:translateY(-3px)}}@keyframes appear{from{opacity:0;transform:translateY(7px)}to{opacity:1;transform:translateY(0)}}
.assistant .bubble{white-space:normal}.bubble p{margin:0 0 12px}.bubble p:last-child{margin-bottom:0}.bubble h1,.bubble h2,.bubble h3,.bubble h4{font-family:Manrope,sans-serif;line-height:1.35;margin:19px 0 9px;color:#f4f1fa}.bubble h1{font-size:22px}.bubble h2{font-size:19px}.bubble h3,.bubble h4{font-size:16px}.bubble ul,.bubble ol{padding-left:25px;margin:7px 0 14px}.bubble li{padding-left:3px;margin:3px 0}.bubble blockquote{border-left:2px solid #aa96f5;margin:9px 0;padding:2px 0 2px 14px;color:#c3bfce}.bubble pre{white-space:pre;overflow:auto;background:#14141b;border:1px solid #ffffff12;border-radius:12px;padding:14px 16px;margin:10px 0 14px;line-height:1.55}.bubble pre code{background:none;padding:0;border:0;color:#d8d4e2;font:12px/1.6 'Cascadia Code',Consolas,monospace}.bubble :not(pre)>code{font:12px 'Cascadia Code',Consolas,monospace;color:#d8caff;background:#ffffff0d;border:1px solid #ffffff10;padding:2px 5px;border-radius:5px}.bubble a{color:#c4b2ff;text-decoration:underline;text-decoration-color:#c4b2ff66;text-underline-offset:3px}.bubble hr{border:0;border-top:1px solid var(--line);margin:13px 0}.bubble table{border-collapse:collapse;width:100%;margin:10px 0}.bubble th,.bubble td{border:1px solid var(--line);padding:7px 10px;text-align:left}.bubble th{background:#ffffff0c}
footer{flex:none;padding:10px 0 20px}.composer-wrap{width:min(760px,100%);margin:auto}.composer{display:flex;align-items:flex-end;gap:10px;padding:12px 13px 12px 19px;border:1px solid #ffffff1b;border-radius:24px;background:#24242dcc;backdrop-filter:blur(24px);box-shadow:0 16px 50px #0004, inset 0 1px #ffffff0a;transition:border-color .2s,box-shadow .2s}.composer:focus-within{border-color:#bea8ff55;box-shadow:0 16px 50px #0004,0 0 0 3px #a48bff0d}.composer textarea{flex:1;resize:none;max-height:180px;min-height:27px;padding:5px 0;border:0;outline:0;background:transparent;color:var(--ink);font:14px/1.6 'DM Sans';caret-color:var(--accent)}textarea::placeholder{color:#898795}.send{height:38px;width:38px;flex:none;border:0;border-radius:14px;background:linear-gradient(145deg,#c4b1ff,#9884ef);color:#201a2c;font-size:20px;font-weight:700;cursor:pointer;box-shadow:0 4px 16px #a48bff33;transition:.2s}.send:hover{transform:translateY(-1px);filter:brightness(1.08)}.send:disabled{opacity:.45;cursor:default;transform:none}.hint{text-align:center;color:#777583;font-size:10px;margin-top:10px}.error{color:#ffaaa9!important}.hidden{display:none!important}
@media(max-width:600px){.app{padding:0 16px}header{height:66px}.online{display:none}main{padding-top:22px}.welcome{justify-content:center;padding-bottom:26px}.welcome h1{letter-spacing:-1.2px}.suggestions{grid-template-columns:1fr}.suggestion:nth-child(n+3){display:none}.composer{border-radius:20px;padding-left:15px}.bubble{max-width:88%}footer{padding-bottom:13px}}
</style></head>
<body><div class="aurora"><div class="orb a"></div><div class="orb b"></div></div>
<div class="app"><header><div class="brand"><div class="logo">✳</div><div><div class="brand-name">Cydonia</div><div class="brand-sub">Your personal memory assistant</div></div></div><div class="header-right"><div class="online"><i class="dot"></i> Ready to chat</div><button class="new-chat" id="newChat">＋ &nbsp;New chat</button></div></header>
<main id="main"><section class="welcome" id="welcome"><div class="welcome-mark">✳</div><h1>Good to see you.</h1><p>Your ideas, notes, and memories are all in one place.<br>What would you like to explore?</p><div class="suggestions"><button class="suggestion" data-prompt="What do you remember about me?">✧ &nbsp;What do you remember about me?<span>Get a quick look at your saved memories</span></button><button class="suggestion" data-prompt="Help me organize my thoughts">◌ &nbsp;Help me organize my thoughts<span>Turn a swirl of ideas into a clear plan</span></button><button class="suggestion" data-prompt="What should I focus on today?">☼ &nbsp;What should I focus on today?<span>Find a useful next step</span></button><button class="suggestion" data-prompt="Let's brainstorm something new">⌁ &nbsp;Let's brainstorm something new<span>Explore an idea together</span></button></div></section><section class="thread hidden" id="thread"></section></main>
<footer><div class="composer-wrap"><div class="composer"><textarea id="prompt" rows="1" placeholder="Message Cydonia…" aria-label="Message Cydonia"></textarea><button class="send" id="send" aria-label="Send message">↑</button></div><div class="hint">Enter to send · Shift + Enter for a new line</div></div></footer></div>
<script>
const input=document.querySelector('#prompt'),sendButton=document.querySelector('#send'),main=document.querySelector('#main'),welcome=document.querySelector('#welcome'),thread=document.querySelector('#thread');let busy=false;
function resize(){input.style.height='auto';input.style.height=Math.min(input.scrollHeight,180)+'px'}input.addEventListener('input',resize);input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});document.querySelectorAll('.suggestion').forEach(b=>b.addEventListener('click',()=>{input.value=b.dataset.prompt;resize();send()}));
function inlineMarkdown(parent,text){const pattern=/(`[^`]+`|\*\*[^*]+\*\*|__[^_]+__|~~[^~]+~~|\*[^*]+\*|_[^_]+_|\[[^\]]+\]\([^)]+\))/g;let cursor=0,match;while((match=pattern.exec(text))){if(match.index>cursor)parent.append(document.createTextNode(text.slice(cursor,match.index)));const token=match[0];let node,content;if(token.startsWith('`')){node=document.createElement('code');node.textContent=token.slice(1,-1)}else if(token.startsWith('**')||token.startsWith('__')){node=document.createElement('strong');node.textContent=token.slice(2,-2)}else if(token.startsWith('~~')){node=document.createElement('del');node.textContent=token.slice(2,-2)}else if(token.startsWith('*')||token.startsWith('_')){node=document.createElement('em');node.textContent=token.slice(1,-1)}else{const parts=token.match(/^\[([^\]]+)\]\(([^)]+)\)$/);node=document.createElement('a');node.textContent=parts[1];try{const url=new URL(parts[2],location.href);if(url.protocol==='https:'||url.protocol==='http:'){node.href=url.href;node.target='_blank';node.rel='noopener noreferrer'}else node.removeAttribute('href')}catch{node.removeAttribute('href')}}parent.append(node);cursor=pattern.lastIndex}if(cursor<text.length)parent.append(document.createTextNode(text.slice(cursor)))}
function renderMarkdown(root,text){root.replaceChildren();const lines=text.replace(/\r\n?/g,'\n').split('\n');let i=0;const isSpecial=line=>/^\s*(```|#{1,6}\s|[-*_]\s*[-*_]\s*[-*_]\s*$|>\s?|[-*+]\s+|\d+[.)]\s+)/.test(line);while(i<lines.length){if(!lines[i].trim()){i++;continue}let m;if((m=lines[i].match(/^\s*```\s*([\w+-]*)\s*$/))){const code=[],lang=m[1];i++;while(i<lines.length&&!/^\s*```/.test(lines[i]))code.push(lines[i++]);if(i<lines.length)i++;const pre=document.createElement('pre'),el=document.createElement('code');if(lang)el.className='language-'+lang;el.textContent=code.join('\n');pre.append(el);root.append(pre);continue}if((m=lines[i].match(/^\s*(#{1,6})\s+(.+)$/))){const h=document.createElement('h'+Math.min(m[1].length,4));inlineMarkdown(h,m[2].replace(/\s+#+\s*$/,''));root.append(h);i++;continue}if(/^\s*([-*_])\s*\1\s*\1\s*$/.test(lines[i])){root.append(document.createElement('hr'));i++;continue}if(/^\s*>/.test(lines[i])){const b=document.createElement('blockquote');while(i<lines.length&&/^\s*>/.test(lines[i])){const p=document.createElement('p');inlineMarkdown(p,lines[i++].replace(/^\s*>\s?/,''));b.append(p)}root.append(b);continue}if((m=lines[i].match(/^\s*([-*+])\s+(.+)$/))|| (m=lines[i].match(/^\s*(\d+)[.)]\s+(.+)$/))){const ordered=/^\s*\d/.test(lines[i]),list=document.createElement(ordered?'ol':'ul');while(i<lines.length){const item=lines[i].match(ordered?/^\s*\d+[.)]\s+(.+)$/:/^\s*[-*+]\s+(.+)$/);if(!item)break;const li=document.createElement('li');inlineMarkdown(li,item[1]);list.append(li);i++}root.append(list);continue}const p=document.createElement('p'),parts=[];while(i<lines.length&&lines[i].trim()&&!isSpecial(lines[i]))parts.push(lines[i++]);if(!parts.length)parts.push(lines[i++]);parts.forEach((line,n)=>{if(n)p.append(document.createElement('br'));inlineMarkdown(p,line)});root.append(p)}}
function message(role,text,extra=''){const row=document.createElement('div');row.className='message '+role+(extra?' '+extra:'');if(role==='assistant'){const avatar=document.createElement('div');avatar.className='avatar';avatar.textContent='✳';row.append(avatar)}const bubble=document.createElement('div');bubble.className='bubble';if(role==='assistant'&&!extra)renderMarkdown(bubble,text);else bubble.textContent=text;row.append(bubble);thread.append(row);main.scrollTop=main.scrollHeight;return row}
async function send(){const text=input.value.trim();if(!text||busy)return;welcome.classList.add('hidden');thread.classList.remove('hidden');message('user',text);input.value='';resize();busy=true;sendButton.disabled=true;const wait=message('assistant','Thinking','thinking');const dots=document.createElement('span');dots.className='typing';dots.innerHTML='<i></i><i></i><i></i>';wait.querySelector('.bubble').append(dots);try{const response=await fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text})});const data=await response.json();if(!response.ok)throw Error(data.error||'Something went wrong');renderMarkdown(wait.querySelector('.bubble'),data.reply||'(No response)')}catch(error){wait.classList.remove('thinking');wait.classList.add('error');wait.querySelector('.bubble').textContent='Could not get a reply: '+error.message}finally{wait.classList.remove('thinking');busy=false;sendButton.disabled=false;input.focus();main.scrollTop=main.scrollHeight}}
sendButton.addEventListener('click',send);document.querySelector('#newChat').addEventListener('click',async()=>{if(busy)return;try{await fetch('/reset',{method:'POST'})}catch{}thread.replaceChildren();thread.classList.add('hidden');welcome.classList.remove('hidden');input.value='';resize();input.focus()});
</script></body></html>'''


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return
        content = PAGE.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_POST(self):
        global messages
        if self.path not in {"/chat", "/reset"}:
            self._json(404, {"error": "Not found"})
            return
        if self.path == "/reset":
            with conversation_lock:
                messages = [{"role": "system", "content": chatbot.build_system_prompt() + "\n\n"
                            "Tool-use rules: When a user explicitly asks you to remember, save, or store a "
                            "durable fact, you must call the appropriate memory tool before saying it was saved. "
                            "Never claim a tool succeeded unless its result confirms success. For questions about "
                            "the user's saved information, call memory_search or memory_read first."}]
            self._json(200, {"ok": True})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(length))
            prompt = str(data.get("message", "")).strip()
            if not prompt:
                self._json(400, {"error": "Message cannot be empty"})
                return
            with conversation_lock:
                messages.append({"role": "user", "content": prompt})
                reply = chatbot.run_turn(messages)
            self._json(200, {"reply": reply})
        except Exception as exc:
            self._json(500, {"error": str(exc)})

    def _json(self, status, value):
        content = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, _format, *_args):
        pass


if __name__ == "__main__":
    address = f"http://{HOST}:{PORT}"
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Cydonia chat is ready at {address} (Ctrl+C to stop)")
    threading.Timer(0.7, lambda: webbrowser.open(address)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nCydonia chat stopped.")
    finally:
        server.server_close()
