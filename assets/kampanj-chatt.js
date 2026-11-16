/* Kampanjassistenten — en chatt som fyller i kampanjmotorns fält.

   Ingen AI-modell och ingen server: det besökaren skriver tolkas i webbläsaren med
   ordlistor och fasta mönster, och ingenting skickas någonstans. Varje meddelande läses
   efter allt det kan innehålla (ämne, budget, antal videor, Spark Ads), så besökaren kan
   svara i vilken ordning som helst. Priserna kommer från kalkylatorns egna konstanter i
   index.html (TIERS, SPARK, kmDiscount), så förslaget, kalkylatorn och prissidan visar
   samma priser. Kalkylatorns tre gratiskreatörer (KM_FREE) tas inte med här.
*/
(function () {
  'use strict';
  var log = document.getElementById('kchat-log');
  var form = document.getElementById('kchat-form');
  var input = document.getElementById('kchat-input');
  if (!log || !form || !window.LMKampanj || typeof TIERS === 'undefined') return;

  var M = window.LMKampanj;
  var lugn = matchMedia('(prefers-reduced-motion: reduce)').matches;
  var ctx = null;
  var BUDGETAR = [15000, 30000, 60000, 100000];
  /* undefined = inte besvarat än. cats: [] = brett. budget: null = vet inte. spark: false | 'period' | index. */
  var st;
  function nollstall() { st = { cats: undefined, budget: undefined, antal: undefined, videos: undefined, spark: undefined, miss: 0, klar: false }; }
  nollstall();

  var kr = function (n) { return Math.round(n).toLocaleString('sv-SE') + ' kr'; };
  var visn = function (n) {
    return n >= 1e6 ? (Math.round(n / 1e5) / 10).toLocaleString('sv-SE') + ' M' : Math.round(n / 1e3).toLocaleString('sv-SE') + 'K';
  };
  function el(tag, cls, text) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (text != null) e.textContent = text;
    return e;
  }
  function ner() { log.scrollTop = log.scrollHeight; }
  function laggTill(node) { log.appendChild(node); ner(); return node; }
  function user(text) { laggTill(el('div', 'kc-msg kc-user', text)); }
  function etikett(k) {
    var c = ctx.match.categories.filter(function (x) { return x.key === k; })[0];
    return c ? c.label : k;
  }
  function amnestext() { return st.cats.map(etikett).join(' och ').toLowerCase(); }

  /* Botens rader kommer med en kort paus, så att det läses som ett samtal. */
  var ko = Promise.resolve();
  function bot(text, efter) {
    ko = ko.then(function () {
      return new Promise(function (klar) {
        var visa = function () {
          laggTill(el('div', 'kc-msg kc-bot', text));   /* alltid ren text */
          if (efter) efter();
          klar();
        };
        if (lugn) return visa();
        var t = laggTill(el('div', 'kc-typing'));
        t.innerHTML = '<i></i><i></i><i></i>';
        setTimeout(function () { t.remove(); visa(); }, 520);
      });
    });
  }
  function chips(val) {
    var rad = el('div', 'kc-chips');
    val.forEach(function (v) {
      var b = el('button', v.cls || '', v.text);
      b.type = 'button';
      b.addEventListener('click', function () {
        b.classList.add('on');
        rad.classList.add('done');
        user(v.text);
        v.valj();
      });
      rad.appendChild(b);
    });
    laggTill(rad);
  }
  function stangChips() {
    log.querySelectorAll('.kc-chips:not(.done)').forEach(function (r) { r.classList.add('done'); });
  }

  /* ---------- nästa fråga: det första som saknas ---------- */
  function steg() {
    if (st.cats === undefined) return 'amne';
    if (st.budget === undefined) return 'budget';
    if (st.budget === null && st.antal === undefined) return 'antal';
    if (st.videos === undefined) return 'videor';
    if (st.spark === undefined) return 'spark';
    if (st.spark === 'period') return 'period';
    return 'klar';
  }
  function nasta(inledning) {
    var s = steg();
    var sag = function (fraga, val) {
      bot((inledning ? inledning + ' ' : '') + fraga, val ? function () { chips(val); } : null);
    };
    if (s === 'amne') return sag('Vad säljer ni?');
    if (s === 'budget') {
      return sag('Vad har ni för budget för kreatörsvideorna?', BUDGETAR.map(function (b) {
        return { text: kr(b), valj: function () { st.budget = b; nasta(); } };
      }).concat([{ text: 'Vet inte än', valj: function () { st.budget = null; nasta('Inga problem.'); } }]));
    }
    if (s === 'antal') {
      return sag('Ungefär hur många kreatörer tänker ni er?', [3, 5, 10].map(function (n) {
        return { text: n + ' kreatörer', valj: function () { st.antal = n; nasta(); } };
      }));
    }
    if (s === 'videor') {
      return sag('En eller två videor per kreatör?', [
        { text: '1 video', valj: function () { st.videos = 1; nasta(); } },
        { text: '2 videor', valj: function () { st.videos = 2; nasta(); } }
      ]);
    }
    if (s === 'spark') {
      return sag('Vill ni också kunna annonsera med videorna (Spark Ads)? Det ligger utanför budgeten, så jag ger en rekommendation ovanpå.', [
        { text: 'Ja', valj: function () { st.spark = 'period'; nasta(); } },
        { text: 'Nej', valj: function () { st.spark = false; nasta(); } },
        { text: 'Bestämmer senare', valj: function () { st.spark = false; nasta('Det går bra. Ni har 14 dagar på er efter publicering.'); } }
      ]);
    }
    if (s === 'period') {
      return sag('Hur länge vill ni kunna annonsera med videorna?', SPARK.map(function (p, i) {
        return { text: p.label, valj: function () { st.spark = i; nasta(); } };
      }));
    }
    visaForslag(inledning);
  }

  /* ---------- förslaget ---------- */
  function visaForslag(inledning) {
    var forsta = !st.klar;
    st.klar = true;
    var p = M.build({ cats: st.cats, budget: st.budget, antal: st.antal, videos: st.videos, spark: st.spark }, ctx);
    if (!p.creators.length) {
      bot((inledning ? inledning + ' ' : '') + (p.notes[0] || 'Jag fick inte ihop ett förslag med de valen.'), function () { efterVal(false); });
      return;
    }
    bot((inledning ? inledning + ' ' : '') + (forsta ? 'Här är ert förslag.' : 'Här är det nya förslaget.'), function () {
      laggTill(kort(p));
      efterVal(true);
      input.placeholder = 'Skriv en ny budget, ett annat ämne eller en fråga';
    });
  }
  function avatar(k) {
    if (k.kort) {
      var img = el('img'); img.src = 'assets/creators/' + k.handle + '.webp'; img.alt = ''; img.width = 48; img.height = 48; img.loading = 'lazy';
      return img;
    }
    return el('span', 'kc-ini', k.name.charAt(0).toUpperCase());
  }
  function kort(p) {
    var c = el('div', 'kc-card');
    c.appendChild(el('h3', '', 'Ert kampanjförslag'));
    var sum = el('p', 'kc-sum', p.creators.length + (p.creators.length === 1 ? ' kreatör' : ' kreatörer') +
      ' · ≈ ' + visn(p.views) + ' visningar');
    sum.appendChild(el('small', '', p.videoCount + ' videor' +
      (p.free ? ', varav ' + p.free.count * p.videos + ' på köpet' : '') +
      (st.cats.length ? ' · ' + st.cats.map(etikett).join(', ') : '') +
      ' · estimat på varje kreatörs medianvisningar, utan annonsering'));
    c.appendChild(sum);

    var ul = el('ul', 'kc-people');
    p.creators.forEach(function (k) {
      var li = el('li');
      li.appendChild(avatar(k));
      var who = el(k.kort ? 'a' : 'span', 'kc-who');
      if (k.kort) who.href = 'kreatorer/' + k.handle + '.html';
      who.appendChild(el('b', '', k.name));
      who.appendChild(el('small', '', M.motivering(k, p.labels)));
      li.appendChild(who);
      var num = el('span', 'kc-num');
      num.appendChild(el('b', '', '≈ ' + visn(k.views)));
      num.appendChild(el('small', '', kr(k.price) + '/video'));
      li.appendChild(num);
      ul.appendChild(li);
    });
    if (p.free) {
      var fl = el('li', 'kc-free');
      var fw = el('span', 'kc-who'); fw.appendChild(el('b', '', p.free.count + ' mindre kreatörer följer med'));
      fw.appendChild(el('small', '', 'Ingår alltid, utan kostnad'));
      fl.appendChild(fw);
      var fn = el('span', 'kc-num'); fn.appendChild(el('b', '', '0 kr')); fl.appendChild(fn);
      ul.appendChild(fl);
    }
    c.appendChild(ul);

    var lines = el('div', 'kc-lines');
    var rad = function (till, a, b, cls) { var d = el('div', cls || ''); d.appendChild(el('span', '', a)); d.appendChild(el('span', '', b)); till.appendChild(d); };
    var nv = p.creators.length * p.videos;
    rad(lines, 'Kreatörer, ' + nv + (nv === 1 ? ' video' : ' videor'), kr(p.list));
    if (p.disc) rad(lines, 'Volymrabatt −' + p.disc + ' %', '−' + kr(p.saved), 'kc-minus');
    rad(lines, 'Totalt, exklusive moms', kr(p.total), 'kc-total');
    c.appendChild(lines);

    if (p.spark) {
      var s = el('div', 'kc-spark');
      s.appendChild(el('b', 'kc-spark-h', 'Rekommenderat ovanpå: Spark Ads'));
      rad(s, 'Rättigheter, ' + p.spark.videos + (p.spark.videos === 1 ? ' video' : ' videor') + ' · ' + p.spark.period, kr(p.spark.rights));
      rad(s, 'Mediebudget i ert eget annonskonto', kr(p.spark.media));
      s.appendChild(el('p', '', 'Vänta 48 timmar efter publicering och lägg annonspengarna på ' +
        (p.spark.videos === 1 ? 'den video' : 'de ' + p.spark.videos + ' videor') + ' som gått bäst. ' +
        kr(p.spark.media) + ' räcker till ungefär ' + visn(p.spark.viewers6s) +
        ' tittare som stannar minst sex sekunder, räknat på vad det kostade i vår höstkampanj 2026. Er kostnad kan bli en annan.'));
      c.appendChild(s);
    }
    p.notes.forEach(function (n) { c.appendChild(el('p', 'kc-note', n)); });
    c.appendChild(el('p', 'kc-fine', 'Ett förslag, inte en offert. Slutgiltigt urval, datum och pris får ni inom två arbetsdagar efter ett möte. ' +
      'Kreatörerna väljs efter videor publicerade sedan augusti 2026 och godkänner själva varje samarbete.'));

    var ctas = el('div', 'kc-ctas');
    var boka = el('button', '', 'Boka 15 min →'); boka.type = 'button';
    boka.addEventListener('click', oppnaBokning);
    var mejl = el('a', 'kc-ghost', 'Mejla mig förslaget');
    mejl.href = 'mailto:hello@luminatemedia.se?subject=' + encodeURIComponent('Kampanjförslag från hemsidan') +
      '&body=' + encodeURIComponent(mejltext(p));
    ctas.appendChild(boka); ctas.appendChild(mejl);
    c.appendChild(ctas);
    return c;
  }
  function mejltext(p) {
    return 'Hej Luminate!\n\nVi har byggt ett kampanjförslag på er hemsida och vill veta mer:\n\n' +
      (st.cats.length ? 'Ämne: ' + st.cats.map(etikett).join(', ') + '\n' : '') +
      (p.budget ? 'Budget för kreatörsvideor: ' + kr(p.budget) + '\n' : '') +
      p.creators.map(function (k) { return '- ' + k.name + ' (@' + k.handle + '), ' + kr(k.price) + '/video'; }).join('\n') +
      '\n' + p.videoCount + ' videor totalt' +
      '\nEstimerade visningar: ' + visn(p.views) +
      '\nEstimat: ' + kr(p.total) + (p.disc ? ' (efter ' + p.disc + ' % volymrabatt)' : '') +
      (p.spark ? '\nSpark Ads ovanpå: rättigheter ' + p.spark.videos + ' videor i ' + p.spark.period + ' (' + kr(p.spark.rights) +
        ') och mediebudget ' + kr(p.spark.media) : '\nSpark Ads: nej') +
      '\n\nFöretag:\nKontaktperson:\nTelefon:';
  }
  function efterVal(harForslag) {
    var val = [];
    if (harForslag) {
      val.push(st.videos === 1
        ? { text: '2 videor per kreatör', valj: function () { st.videos = 2; visaForslag(); } }
        : { text: '1 video per kreatör', valj: function () { st.videos = 1; visaForslag(); } });
      val.push(st.spark === false
        ? { text: 'Lägg till Spark Ads', valj: function () { st.spark = 'period'; nasta(); } }
        : { text: 'Utan Spark Ads', valj: function () { st.spark = false; visaForslag(); } });
    }
    val.push({ text: 'Börja om', valj: function () { nollstall(); input.placeholder = 'Skriv här, till exempel: vi säljer hårvård'; nasta('Vi börjar om.'); } });
    chips(val);
  }
  function oppnaBokning() { if (typeof openBooking === 'function') openBooking(); }

  /* ---------- vanliga frågor och småprat ---------- */
  function prisspann() {
    var p = TIERS.map(function (t) { return t.price; });
    return kr(Math.min.apply(null, p)).replace(' kr', '') + ' och ' + kr(Math.max.apply(null, p));
  }
  var SVAR = [
    [/är du (en )?(ai|robot|bot|människa|manniska|riktig)|pratar jag med/, function () {
      return 'Jag är Luminates kampanjassistent, ett verktyg som räknar på nätverkets egna siffror. Vill ni prata med en människa bokar jag gärna ett möte.'; }],
    [/vad är spark|vad betyder spark|hur funkar spark|hur fungerar spark/, function () {
      return 'Spark Ads betyder att kreatörens video körs som annons från ert eget annonskonto. Ni köper rättigheterna först när ni sett vilka videor som gått bäst.'; }],
    [/vad kostar|kostar det|prislista|\bpris(er|et)?\b|hur mycket (kostar|tar)/, function () {
      return 'En video kostar mellan ' + prisspann() + ' beroende på kreatörens räckvidd, och priset per video sjunker när ni bokar fler.'; }],
    [/hur (funkar|fungerar|går det till|gör man)|vad gör ni|vad ingår/, function () {
      return 'Vi tar hela kampanjen från urval till rapport: koncept, manus, inspelning och publicering. Ni godkänner manus och video innan något publiceras.'; }],
    [/vilka (kreatörer|influencers)|hur många (kreatörer|influencers) har|ert nätverk|era kreatörer/, function () {
      return 'Vi har ' + ctx.creators.length + ' svenska TikTok-kreatörer i nätverket, flest inom mode, skönhet och livsstil. Jag väljer ut dem som passar er.'; }],
    [/kampanj|samarbet|intresse|influencer|kreatör|jobba med|komma igång|sätta igång|starta|testa|annonsera|marknadsför|synas|nå ut/, function () {
      return 'Kul att ni är intresserade!'; }],
    [/^(hej|hejsan|hallå|halla|tjena|tja|tjo|hi|hello|god (morgon|kväll|dag))\b/, function () { return 'Hej!'; }],
    [/\b(tack|tackar|perfekt|toppen|snyggt|grymt|kanon)\b/, function () { return 'Varsågod!'; }]
  ];
  function smaprat(lag) {
    for (var i = 0; i < SVAR.length; i++) if (SVAR[i][0].test(lag)) return SVAR[i][1]();
    return null;
  }

  /* ---------- allt besökaren skriver ---------- */
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var t = input.value.trim();
    if (!t || !ctx) return;
    input.value = '';
    stangChips();
    user(t);
    var lag = t.toLowerCase();
    var s = steg();

    if (/\b(boka|möte|mote|ring|ringa)\b|prata med (någon|en människa|er)/.test(lag)) {
      bot('Självklart. Jag öppnar kalendern, så väljer ni en tid som passar.');
      ko = ko.then(oppnaBokning);
      return;
    }
    if (/börja om|starta om|nollställ/.test(lag)) { nollstall(); return nasta('Vi börjar om.'); }

    /* 1. Plocka ut allt meddelandet innehåller, oavsett vilken fråga som just ställdes.
          En fråga ("vad kostar en video?") är ingen beställning: ur den läses bara ämne och budget. */
    var fraga = /\?\s*$/.test(t) || /^(vad|hur|vilka|vilken|varför|kan|är|har ni|finns|när)\b/.test(lag);
    var forstod = [], andrat = false;
    var amnen = M.tolkaAmnen(t);
    if (amnen.length) { st.cats = amnen; st.miss = 0; andrat = true; forstod.push('Då tittar jag på kreatörer inom ' + amnestext() + '.'); }

    var mA = lag.match(/(\d+)\s*(st\s*)?(kreatör|influencer)/);
    if (fraga) mA = null;
    if (mA && +mA[1] >= 1 && +mA[1] <= 40) { st.antal = +mA[1]; andrat = true; if (st.budget === undefined) st.budget = null; }
    else if (s === 'antal' && /^\d{1,2}$/.test(lag)) { st.antal = +lag; andrat = true; }

    if (fraga) { /* inget val */ }
    else if (/\b(2|två|tva)\s*(st\s*)?video/.test(lag) || (s === 'videor' && /^(2|två|tva)\b/.test(lag))) { st.videos = 2; andrat = true; }
    else if (/\b(1|en|ett)\s*(st\s*)?video/.test(lag) || (s === 'videor' && /^(1|en|ett)\b/.test(lag))) { st.videos = 1; andrat = true; }

    var belopp = M.tolkaBudget(t);
    if (belopp) { st.budget = belopp; andrat = true; forstod.push(kr(belopp) + ' i budget.'); }
    else if (s === 'budget' && /vet inte|ingen aning|osäker|osaker|ingen budget/.test(lag)) { st.budget = null; andrat = true; forstod.push('Inga problem.'); }

    if (fraga && s !== 'spark' && s !== 'period') { /* inget val */ }
    else if (/utan spark|inga annonser|inte annonsera|bara organiskt/.test(lag) || (s === 'spark' && /^(nej|nä|nix|no)\b|inte nu|senare/.test(lag))) { st.spark = false; andrat = true; }
    else if (s === 'period' || (st.spark === 'period')) {
      var per = /12|ett år|1 år/.test(lag) ? 3 : /6|halvår/.test(lag) ? 2 : /90|tre mån|3 mån/.test(lag) ? 1 : /30|en mån|1 mån/.test(lag) ? 0 : null;
      if (per !== null) { st.spark = per; andrat = true; }
    } else if ((s === 'spark' && /^(ja|japp|jajamän|yes|gärna|garna|absolut)\b/.test(lag)) || (/spark|annons/.test(lag) && !/vad är|hur f/.test(lag) && (st.spark === undefined || st.spark === false))) {
      st.spark = 'period'; andrat = true;
    }

    /* 2. Svara. */
    var prat = smaprat(lag);
    if (andrat) return nasta(forstod.join(' ') || (st.klar ? 'Jag har räknat om.' : ''));
    if (prat) {
      if (st.klar) return bot(prat);
      if (s === 'amne') return bot(prat + (/intresserade/.test(prat) ? ' Berätta mer, vad säljer ni?' : ' Vad säljer ni?'));
      return nasta(prat);
    }
    if (s === 'amne') {
      st.miss++;
      if (st.miss < 2) return bot('Det har jag ingen färdig kategori för. Vad ligger närmast: kläder, skönhet, hår, hudvård, mat, träning, livsstil eller hem? Passar inget räknar jag brett på hela nätverket.');
      st.cats = [];
      return nasta('Det har jag ingen egen kategori för, så jag räknar brett på hela nätverket. Vi finjusterar på ett möte.');
    }
    if (s === 'budget') return bot('Skriv budgeten som ett belopp i kronor, till exempel 30 000. Vet ni inte än går det också bra.');
    if (s !== 'klar') return nasta('Det förstod jag inte riktigt.');
    bot('Jag kan räkna om förslaget efter ämne, budget, antal videor och Spark Ads. Allt annat tar vi gärna på ett möte.', function () {
      chips([{ text: 'Boka 15 min →', cls: 'kc-go', valj: oppnaBokning }]);
    });
  });

  /* ---------- start ---------- */
  function hamta(url) { return fetch(url, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error(url); return r.json(); }); }

  Promise.all([hamta('data/stats.json'), hamta('data/views.json'), hamta('data/match.json')]).then(function (d) {
    /* Namn och bild finns för kreatörer med kort på sajten; övriga i nätverket har namn och följare i match.json. */
    var kort = {};
    document.querySelectorAll('.ccard[data-handle]').forEach(function (c) {
      var b = c.querySelector('.cc-info b');
      kort[c.dataset.handle] = b ? b.textContent : null;
    });
    var alla = {};
    Object.keys(kort).concat(Object.keys(d[2].creators)).forEach(function (h) { alla[h] = 1; });
    var creators = Object.keys(alla).map(function (h) {
      var m = d[2].creators[h] || {};
      return { handle: h, name: kort[h] || m.name, kort: !!kort[h],
               followers: (d[0].creators[h] || {}).followers || m.followers || 0,
               median: (d[1].creators[h] || {}).median || m.own || 0 };
    }).filter(function (c) { return c.name; });
    /* Inga gratiskreatörer i förslag (Willem 31 okt 2026), även om kalkylatorn har KM_FREE. */
    ctx = { tiers: TIERS, spark: SPARK, discount: kmDiscount, free: { count: 0, views: 0 },
            creators: creators, match: d[2] };
    bot('Hej! Berätta vad ni säljer, så bygger jag ett kampanjförslag med kreatörer, pris och estimerade visningar.');
  }).catch(function () {
    var m = el('div', 'kc-msg kc-bot', 'Jag kunde inte läsa in nätverkets siffror just nu. ');
    var a = el('a', '', 'Räkna i kalkylatorn');
    a.href = '#';
    a.addEventListener('click', function (e) { e.preventDefault(); if (typeof openProposal === 'function') openProposal(); });
    m.appendChild(a);
    m.appendChild(document.createTextNode(' eller boka ett möte, så hjälper vi er direkt.'));
    log.appendChild(m);
    form.hidden = true;
  });
})();
