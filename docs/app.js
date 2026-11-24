const $ = id => document.getElementById(id);
const teams = ['Billing','Delivery','Account access','Technical support','Product quality','Account security','Manual review'];
const examples = ['I was charged twice for demo order DEMO-1042. Please refund the duplicate payment.',
 'Where is my parcel for DEMO-2077? Please check its tracking status.',
 'My item arrived damaged. Please arrange a replacement for DEMO-3108.',
 "I need an invoice copy for DEMO-4101?",
 "My coupon expired before checkout on DEMO-4102?",
 "My reward points are missing for DEMO-4103?",
 "The courier missed my return pickup for DEMO-4104?",
 "The charging cable accessory is missing from DEMO-4105?",
 "I received the wrong size for DEMO-4106?",
 "What is the refund status for DEMO-4107?",
 "I cannot find the warranty expiry date for DEMO-4108?",
 "Please add delivery instructions to call on arrival for DEMO-4109?",
 "My download link has expired for DEMO-4110?",
 "DEMO-4111: I qualified for free delivery but paid a shipping fee.",
 "DEMO-4112: My gift card balance disappeared after checkout failed.",
 "DEMO-4113: My verified student discount was missing from the bill.",
 "DEMO-4114: My rental deposit is still held after the return.",
 "DEMO-4115: The billed price was higher than my confirmed order price.",
 "DEMO-4116: I missed the courier and need redelivery.",
 "DEMO-4117: I cannot find the collection point for my parcel.",
 "DEMO-4118: My delivery receipt is missing.",
 "DEMO-4119: Only the first box arrived. Where is the second parcel?",
 "DEMO-4120: My selected delivery slot disappeared. Please move it to the evening.",
 "DEMO-4121: I ordered blue but received the wrong colour.",
 "DEMO-4122: The quantity is short. I received two units instead of three.",
 "DEMO-4123: My appliance arrived with the wrong plug adapter.",
 "DEMO-4124: The assembly guide is missing from the box.",
 "DEMO-4125: The serial label is unreadable and I need the product number.",
 "DEMO-4126: My activation limit is full after replacing my laptop.",
 "DEMO-4127: My paid course is missing from my library.",
 "DEMO-4128: The subtitle defaults to the wrong language.",
 "DEMO-4129: I still get newsletter messages after opting out.",
 "DEMO-4130: My display name is blank. Please use Demo Learner."];
let cases = [], sample = 0, analysisId = 0;
function node(tag,text){const el=document.createElement(tag);el.textContent=text;return el}
function bind(button,action){
  button.onclick=async()=>{
    button.disabled=true;
    try{$('message').textContent='';await action()}catch(error){$('message').textContent=error.message}finally{button.disabled=false}
  };
}
async function refresh(){cases=await api('cases');render()}
function render(){
  const open=cases.filter(c=>c.status!=='Resolved');
  $('active').textContent=open.length;
  $('urgent').textContent=open.filter(c=>c.priority==='High').length;
  $('done').textContent=cases.length-open.length;
  const queue=$('queue');queue.replaceChildren();
  for(const c of cases.filter(c=>[c.text,c.team,c.status].join(' ').toLowerCase().includes($('filter').value.toLowerCase()))){
    const row=node('button','');row.className='row';
    row.append(node('small',c.team+' · '+c.priority),node('strong',c.text),node('small',c.status));
    bind(row,()=>review(c.id));queue.append(row);
  }
  if(!queue.children.length)queue.append(node('p',cases.length?'No matching cases.':'Your first case will appear here.'));
}
async function review(id,saved){
  const c=cases.find(row=>row.id===id);
  const history=saved?.history??await api('history/'+id);
  let entry=history.find(h=>h.note.includes('Automatic response: '));
  const current=cases.find(row=>row.id===id);
  const box=$('record');box.replaceChildren(node('p',c.text),node('strong',current.team+' · '+current.status),
    node('h3','Your response'),node('p',entry?entry.note.split('Automatic response: ')[1]:current.plan),node('h3','Case history'));
  history.forEach(h=>box.append(node('p',new Date(h.at).toLocaleString()+' · '+h.note)));
  const download=node('button','Download case report');
  download.onclick=()=>{
    const blob=new Blob([JSON.stringify({case:current,history},null,2)],{type:'application/json'});
    const link=document.createElement('a');link.href=URL.createObjectURL(blob);
    link.download='resolve-'+id+'.json';link.click();setTimeout(()=>URL.revokeObjectURL(link.href),1000);
  };
  box.append(download);
  if(!$('detail').open)$('detail').showModal();
}
function invalidate(){analysisId++;$('result').replaceChildren()}
$('sample').onclick=()=>{$('issue').value=examples[Number($('scenario').value)];invalidate()};
$('issue').oninput=invalidate;$('filter').oninput=render;
bind($('triage'),async()=>{
  const text=$('issue').value.trim(),request=++analysisId;
  const saved=await api('resolve',{text});
  if(request!==analysisId)return;
  if(saved.record){
    cases=[saved.record,...cases.filter(c=>c.id!==saved.id)];
    render();
  }else{
    await refresh();
  }
  await review(saved.id,saved);

});
refresh().catch(error=>{$('message').textContent='Could not load cases. '+error.message});


