'use strict';
// Tokens are kept only in memory; reloading requires login. Use textContent for API content.
let token = null, principal = null, activeThread = null;
const $ = id => document.getElementById(id);
const el = (tag, text, cls) => {const node=document.createElement(tag); if(text!==undefined)node.textContent=String(text); if(cls)node.className=cls;return node;};
const clear = node => node.replaceChildren();
async function api(path, options={}) {
  const headers={'Content-Type':'application/json',...(token?{'Authorization':'Bearer '+token}:{})};
  let response;
  try {response=await fetch(path,{...options,headers:{...headers,...options.headers},cache:'no-store'});} catch(e){throw new Error('Network unavailable. Check the server.');}
  let data;try{data=await response.json();}catch(e){throw new Error('Invalid server response');}
  if(!response.ok){if(response.status===401 && token) logout();throw new Error(typeof data.detail==='string'?data.detail:`Request failed (${response.status})`);}
  return data;
}
function status(text){$('status').textContent=text;}
function logout(){token=null;principal=null;activeThread=null;$('appPanel').classList.add('hidden');$('loginPanel').classList.remove('hidden');$('logout').classList.add('hidden');$('userLabel').textContent='';$('password').value='';}
$('logout').addEventListener('click',logout);
$('loginForm').addEventListener('submit',async e=>{e.preventDefault();$('loginError').textContent='';try{
 const result=await api('/login',{method:'POST',body:JSON.stringify({username:$('username').value,password:$('password').value})});token=result.access_token;
 principal=await api('/me');$('loginPanel').classList.add('hidden');$('appPanel').classList.remove('hidden');$('logout').classList.remove('hidden');$('userLabel').textContent=`${principal.user_id} · ${principal.role}`;
 const canWrite=['agent','admin'].includes(principal.role);$('ticketForm').classList.toggle('hidden',!canWrite);$('refreshDrafts').classList.toggle('hidden',!canWrite);
 await Promise.all([loadThreads(),loadDrafts(),loadTickets()]);
}catch(err){$('loginError').textContent=err.message;}});
async function loadThreads(){const items=await api('/threads');clear($('threadList'));items.forEach(t=>{const b=el('button',t.title,'thread'+(t.thread_id===activeThread?' active':''));b.addEventListener('click',()=>selectThread(t));$('threadList').append(b);});}
function selectThread(t){activeThread=t.thread_id;$('chatTitle').textContent=t.title;clear($('messages'));clear($('sources'));clear($('activity'));status('Thread selected.');loadThreads().catch(err=>status(err.message));}
$('newThread').addEventListener('click',async()=>{try{const title=prompt('Thread title?','New support conversation');if(!title)return;const t=await api('/threads',{method:'POST',body:JSON.stringify({title})});selectThread(t);}catch(err){status(err.message);}});
function renderItems(target,items,empty){clear($(target));if(!Array.isArray(items)||!items.length){$(target).append(el('p',empty,'muted'));return;}items.forEach(item=>$(target).append(el('div',typeof item==='string'?item:JSON.stringify(item),'card')));}
$('chatForm').addEventListener('submit',async e=>{e.preventDefault();if(!activeThread){status('Create or select a thread first.');return;}const message=$('chatInput').value.trim();if(!message)return;$('sendBtn').disabled=true;status('Waiting for agent response…');$('messages').append(el('div',message,'message user'));$('chatInput').value='';try{const r=await api('/chat',{method:'POST',body:JSON.stringify({thread_id:activeThread,message})});$('messages').append(el('div',r.answer||'No answer returned','message assistant'));renderItems('sources',r.citations||r.sources||[],'No citations returned by this handler.');renderItems('activity',r.tool_activity||r.tools||[],'No tool activity returned by this handler.');status(r.configured===false?'Demo backend: live AI chat is not configured.':'Response received.');}catch(err){$('messages').append(el('div',err.message,'message error'));status('Request failed.');}finally{$('sendBtn').disabled=false;$('messages').scrollTop=$('messages').scrollHeight;}});
$('ticketForm').addEventListener('submit',async e=>{e.preventDefault();try{const result=await api('/tickets',{method:'POST',body:JSON.stringify({customer_id:$('customer').value,subject:$('subject').value,description:$('description').value})});status(`Draft ${result.draft_id} staged. No ticket created yet.`);await loadDrafts();}catch(err){status(err.message);}});
async function loadDrafts(){if(!principal||!['agent','admin'].includes(principal.role)){clear($('drafts'));return;}try{const drafts=await api('/ticket-drafts');clear($('drafts'));if(!drafts.length){$('drafts').append(el('p','No pending drafts','muted'));return;}drafts.forEach(d=>{const card=el('div',undefined,'card');card.append(el('strong',d.draft_id),el('p',d.args.subject));const btn=el('button','Confirm ticket');btn.addEventListener('click',async()=>{if(!confirm(`Confirm ticket draft ${d.draft_id}? This creates a ticket.`))return;btn.disabled=true;try{await api(`/ticket-drafts/${encodeURIComponent(d.draft_id)}/confirm`,{method:'POST',body:JSON.stringify({token:d.token})});status('Ticket confirmed.');await Promise.all([loadDrafts(),loadTickets()]);}catch(err){status(err.message);btn.disabled=false;}});card.append(btn);$('drafts').append(card);});}catch(err){status(err.message);}}
async function loadTickets(){try{const items=await api('/tickets');renderItems('tickets',items,'No confirmed tickets.');}catch(err){status(err.message);}}
$('refreshDrafts').addEventListener('click',()=>loadDrafts());
