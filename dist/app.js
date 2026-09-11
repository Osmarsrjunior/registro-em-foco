'use strict';
const D = window.REGISTRO_DATA;
const $ = id => document.getElementById(id);
const fmt = (n, digits = 2) => new Intl.NumberFormat('pt-BR', { minimumFractionDigits: digits, maximumFractionDigits: digits }).format(n);
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const territories = D.records.filter(x => x.year === 2024 && ['country','state'].includes(x.level));
$('territory').innerHTML = territories.map(x => `<option value="${esc(x.code)}">${esc(x.name)}</option>`).join('');

function lineChart(series, labels, maximum, scenarioMode = false) {
  const w = 560, h = 255, left = 45, right = 25, top = 30, bottom = 35;
  const max = maximum || Math.max(...series.flatMap(s => s.values)) * 1.15 || 1;
  const x = i => left + i * (w-left-right) / Math.max(1,labels.length-1);
  const y = v => h-bottom-v/max*(h-top-bottom);
  let svg = `<svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(series.map(s=>s.name+': '+s.values.map((v,i)=>labels[i]+' '+fmt(v)+'%').join(', ')).join('; '))}">`;
  for(let i=0;i<=4;i++) {const value=max*i/4;svg+=`<line x1="${left}" x2="${w-right}" y1="${y(value)}" y2="${y(value)}" stroke="#e2e9ef"/><text x="${left-9}" y="${y(value)+4}" text-anchor="end" fill="#627487" font-size="12">${fmt(value,1)}</text>`;}
  labels.forEach((l,i)=>{svg+=`<text x="${x(i)}" y="${h-10}" text-anchor="middle" font-size="12" fill="#627487">${l}</text>`;});
  series.forEach((s,j)=>{const color=j?'#92a4b5':'#007b73';svg+=`<polyline points="${s.values.map((v,i)=>x(i)+','+y(v)).join(' ')}" fill="none" stroke="${color}" stroke-width="${j?2:3}" ${scenarioMode?'stroke-dasharray="7 5"':''}/>`;s.values.forEach((v,i)=>{svg+=`<circle cx="${x(i)}" cy="${y(v)}" r="4" fill="${color}"/>`;if(!j&&(labels.length<6||i===0||i===labels.length-1))svg+=`<text x="${x(i)}" y="${y(v)-12}" text-anchor="middle" font-size="13" font-weight="600" fill="#172d45">${fmt(v)}%</text>`;});});
  return svg+'</svg>';
}
function selected(){return D.records.find(x=>x.code===$('territory').value&&x.year===Number($('year').value));}
function scenarioValues(base,reduction,years){return Array.from({length:years+1},(_,i)=>base*(1-reduction/100)**i);}
function updateScenario(){
 const r=selected(), reduction=Number($('reduction').value), years=Number($('horizon').value);
 const values=scenarioValues(r.rate,reduction,years);
 $('reduction-label').textContent=fmt(reduction,0)+'%';
 $('scenario-result').innerHTML=`<strong>${fmt(values.at(-1))}%</strong> em ${r.year+years}<br><span>Partindo de ${fmt(r.rate)}% em ${r.year} · ${esc(r.name)}</span>`;
 $('scenario-chart').innerHTML=lineChart([{name:'Cenário hipotético',values}],values.map((_,i)=>r.year+i),null,true);
}
function render(){
 const r=selected(), br=D.records.find(x=>x.code==='BR'&&x.year===r.year);
 const delta=r.rate-br.rate;
 const cards=[['Sub-registro estimado',fmt(r.rate)+'%','Taxa publicada · '+r.year],['Nascimentos estimados',fmt(r.estimated_births,0),'Denominador estimado pelo IBGE'],['Volume aproximado',fmt(r.estimated_missing,0),'Eventos · total × taxa ÷ 100'],['Diferença para o Brasil',(delta>0?'+':'')+fmt(delta)+' p.p.','Brasil: '+fmt(br.rate)+'% no mesmo ano']];
 $('kpis').innerHTML=cards.map(([title,value,note])=>`<article class="kpi"><p>${title}</p><strong>${value}</strong><small>${note}</small></article>`).join('');
 const rows=D.records.filter(x=>x.code===r.code).sort((a,b)=>a.year-b.year), national=D.records.filter(x=>x.code==='BR').sort((a,b)=>a.year-b.year);
 const series=[{name:r.name,values:rows.map(x=>x.rate)}];if(r.code!=='BR')series.push({name:'Brasil',values:national.map(x=>x.rate)});
 $('trend-title').textContent=r.name+' · 2022–2024';
 $('trend').innerHTML=lineChart(series,[2022,2023,2024]);
 $('trend-caption').textContent='Verde: '+r.name+(r.code!=='BR'?' · Cinza: Brasil. ':'. ')+'Variação entre 2022 e 2024: '+fmt(rows[2].rate-rows[0].rate)+' pontos percentuais. Série curta, sem inferência causal.';
 const metric=$('metric').value;
 const states=D.records.filter(x=>x.year===r.year&&x.level==='state').sort((a,b)=>b[metric]-a[metric]);
 const top=states.slice(0,8), max=top[0][metric];
 $('ranking').innerHTML=top.map(x=>`<div class="rank-row ${x.code===r.code?'selected':''}"><button data-state="${x.code}" aria-label="Selecionar ${esc(x.name)}">${esc(x.name)}</button><div class="track"><div class="bar" style="width:${x[metric]/max*100}%"></div></div><strong>${fmt(x[metric],metric==='rate'?2:0)}${metric==='rate'?'%':''}</strong></div>`).join('');
 $('ranking').querySelectorAll('button').forEach(b=>b.addEventListener('click',()=>{$('territory').value=b.dataset.state;render();}));
 $('table-caption').textContent='Ano '+r.year+' · ordenação por '+(metric==='rate'?'taxa':'volume aproximado');
 $('state-table').innerHTML=states.map(x=>`<tr><td>${esc(x.name)}</td><td>${esc(x.region)}</td><td>${fmt(x.estimated_births,0)}</td><td>${fmt(x.rate)}</td><td>${fmt(x.estimated_missing,0)}</td></tr>`).join('');
 updateScenario();
}
['territory','year','metric'].forEach(id=>$(id).addEventListener('change',render));
['reduction','horizon'].forEach(id=>$(id).addEventListener('input',updateScenario));
$('export').addEventListener('click',()=>{const r=selected();const rows=D.records.filter(x=>x.code===r.code);const columns=['year','code','name','estimated_births','rate','estimated_missing'];const csv=columns.join(',')+'\n'+rows.map(x=>columns.map(c=>JSON.stringify(x[c])).join(',')).join('\n');const url=URL.createObjectURL(new Blob(['\uFEFF'+csv],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='registro-em-foco-'+r.code+'-2022-2024.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);});
render();
