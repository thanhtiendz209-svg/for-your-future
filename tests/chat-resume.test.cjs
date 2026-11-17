const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
function app(){
 const items=new Map(),sessionItems=new Map();
 const storage={getItem:key=>items.get(key)??null,setItem:(key,value)=>items.set(key,value),removeItem:key=>items.delete(key)};
 const ctx={window:{location:{hash:'#home'},addEventListener(){}},localStorage:storage,sessionStorage:{getItem:key=>sessionItems.get(key)??null,setItem:(key,value)=>sessionItems.set(key,value),removeItem:key=>sessionItems.delete(key)},console};
 vm.createContext(ctx);vm.runInContext(fs.readFileSync('apps/web/public/app.js','utf8'),ctx);
 return {items,sessionItems,run:code=>vm.runInContext(code,ctx)};
}
test('resume is allowed strictly within five minutes after departure',()=>{
 const a=app();
 a.run("saveChatResume('a','conversation-a',1000)");
 assert.equal(a.run("readChatResume('a',300999)"),'conversation-a');
 assert.equal(a.run("readChatResume('a',301000)"),null);
 assert.ok(!a.items.has('fyf_chat_resume_a'));
});
test('first entry, legacy pointers, new chats and invalid timestamps do not resume',()=>{
 const a=app();
 a.sessionItems.set('fyf_chat_active_a','old-conversation');
 assert.equal(a.run("readChatResume('a',1000)"),null);
 for(const saved of ['bad json','null','{}',JSON.stringify({sessionId:'old',leftAt:2000}),JSON.stringify({sessionId:'old',leftAt:'1000'}),JSON.stringify({sessionId:null,leftAt:1000})]){
  a.items.set('fyf_chat_resume_a',saved);
  assert.equal(a.run("readChatResume('a',1000)"),null);
 }
});
test('resume and clear remain scoped to the signed-in account',()=>{
 const a=app();
 a.run("saveChatResume('a','a-chat',1000);saveChatResume('b','b-chat',1000);clearChatResume('a')");
 assert.equal(a.run("readChatResume('a',1100)"),null);
 assert.equal(a.run("readChatResume('b',1100)"),'b-chat');
 assert.equal(a.run("readChatResume(null,1100)"),null);
});
