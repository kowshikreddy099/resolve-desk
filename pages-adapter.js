function classify(text) {
  const weights = new Map();
  for (const word of text.toLowerCase().match(/[a-z0-9]+/g) || []) {
    if (!model.stop.includes(word)) weights.set(word,(weights.get(word)||0)+(model.idf[word]||1));
  }
  const norm = Math.hypot(...weights.values()) || 1;
  const scores = new Map();
  for (const [team,doc] of model.index) {
    let score=0;
    for(const [word,weight] of weights) score+=(doc[word]||0)*weight/norm;
    scores.set(team,Math.max(scores.get(team)||0,score));
  }
  const [first,second]=[...scores].sort((a,b)=>b[1]-a[1]);
  return first[1]>=0.21 && first[1]-second[1]>=0.07 ? first[0] : 'Manual review';
}
async function api(path,body) {
  const key='resolve-desk-pages-v1';
  const items=JSON.parse(localStorage.getItem(key)||'[]');
  if(path==='cases') return items.map(item=>item.record);
  if(path.startsWith('history/')) return items.find(item=>item.id===path.slice(8))?.history||[];
  if(path!=='resolve') throw Error('Unknown request');
  const text=body.text.trim();
  if(text.length<10||text.length>3000) throw Error('Enter 10 to 3000 characters.');
  const normalize=value=>value.toLowerCase().replace(/\s+/g,' ').trim();
  const prior=items.find(item=>normalize(item.record.text)===normalize(text));
  if(prior) return prior;
  let team=classify(text),status='In progress',reply=model.guidance[team];
  const priority=/\b(unauthori[sz]ed|fraud|hacked|stolen|outage)\b/i.test(text)?'High':'Normal';
  const orders=[...new Set(text.toUpperCase().match(/\bDEMO-\d+\b/g)||[])];
  const rule=orders.length===1 && model.orders[orders[0]];
  if(rule && priority==='Normal' && new RegExp(rule[1],'i').test(text) && !/\b(no|not|never|cancel|don't|do not)\b/i.test(text)){
    team=rule[0];status='Resolved';
    reply=rule[3]+' Action reference: '+rule[2].toUpperCase().split(' ')[0]+'-'+orders[0]+'.';
  }
  const id=crypto.randomUUID(),at=new Date().toISOString();
  const item={id,record:{id,text,team,status,priority,plan:reply,version:2},history:[{at,note:'Case opened'},{at,note:'Automatic response: '+reply}]};
  localStorage.setItem(key,JSON.stringify([item,...items]));
  return item;
}
