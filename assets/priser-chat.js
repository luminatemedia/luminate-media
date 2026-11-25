/* Prissidans chatt: ett regelstyrt beslutssystem som alltid landar i ett upplägg.
   Den läser inte besökarens hemsida. Den tolkar orden (och domännamnet) i det besökaren skriver,
   frågar efter det som saknas och väljer paket ur window.LM_PRIS, som byggs av scripts/build_pricing.py.
   Inga priser står i den här filen. */
(function () {
  'use strict';
  var D = window.LM_PRIS;
  var ask = document.getElementById('px-ask');
  if (!D || !ask) return;
  var input = document.getElementById('px-q'), chat = document.getElementById('px-chat'),
      log = document.getElementById('px-log'), say = document.getElementById('px-say'),
      sayIn = document.getElementById('px-say-in');
  var PK = {}; D.paket.forEach(function (p) { PK[p.id] = p; });
  var ORDER = D.paket.map(function (p) { return p.id; });           /* minst → störst */
  var kr = function (n) { return Math.round(n).toLocaleString('sv-SE').replace(/ /g, ' ') + ' kr'; };
  var kviews = function (n) { return n >= 1e6 ? (Math.round(n / 1e5) / 10).toLocaleString('sv-SE') + ' M' : Math.round(n / 1e3) + 'K'; };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };

  /* ---- kategorier: vad säljer de? product = kan en kreatör få hem och använda det ---- */
  var CATS = [
    { id: 'mode', namn: 'mode och kläder', product: true, format: 'try-on, outfits och "vad jag köpte"-videor',
      ord: ['kläd', 'klader', 'mode ', 'modebut', 'modemärke', 'fashion', 'wear', 'skor', 'shoes', 'sneaker', 'smycke', 'jewel', 'väsk', 'vask', 'bags', 'outfit', 'streetwear', 'jeans', 'underkläd', 'accessoar', 'apparel', 'boutique', 'butik'] },
    { id: 'skonhet', namn: 'skönhet och hudvård', product: true, format: 'rutiner, före och efter och "get ready with me"',
      ord: ['skönhet', 'skonhet', 'beauty', 'smink', 'makeup', 'hudvård', 'hudvard', 'skin', 'hår ', 'hårvård', 'hårprodukt', 'hair', 'parfym', 'nagel', 'nail', 'kosmetik', 'cosmetic', 'serum', 'spa ', 'salong'] },
    { id: 'mat', namn: 'mat och dryck', product: true, format: 'smaktest, recept och vardagsvideor där produkten är med',
      ord: ['mat ', 'matvar', 'livsmedel', 'dryck', 'kaffe', 'coffee', 'te ', 'tea', 'snacks', 'godis', 'candy', 'energidryck', 'drink', 'food', 'restaurang', 'café', 'cafe', 'bryggeri', 'bageri', 'choklad', 'läsk', 'lask', 'bar '] },
    { id: 'halsa', namn: 'träning och hälsa', product: true, format: 'träningsvardag, rutiner och ärliga tester över tid',
      ord: ['träning', 'traning', 'gym', 'fitness', 'kosttillskott', 'protein', 'hälsa', 'halsa', 'health', 'vitamin', 'sport', 'yoga', 'löpning', 'running', 'supplement', 'wellness'] },
    { id: 'hem', namn: 'hem och inredning', product: true, format: 'före och efter, "room tour" och uppackning hemma',
      ord: ['inredning', 'möbel', 'mobel', 'furniture', 'interior', 'kök', 'säng', 'lampa', 'textil', 'hemma', 'home', 'doftljus', 'porslin', 'heminredning'] },
    { id: 'barn', namn: 'barn och familj', product: true, format: 'vardag med familjen där produkten används på riktigt',
      ord: ['barn', 'baby', 'kids', 'leksak', 'toy', 'familj', 'förälder', 'foralder'] },
    { id: 'tech', namn: 'teknik och appar', product: false, format: 'skärminspelning med kreatören i bild: "så här använder jag den"',
      ord: ['app ', 'appen', 'saas', 'mjukvara', 'software', 'plattform', 'platform', 'tech', 'teknik', 'elektronik', 'gadget', 'mobil', 'hörlur', 'horlur', 'spel', 'game'] },
    { id: 'tjanst', namn: 'tjänster', product: false, format: 'kreatören berättar om sin egen upplevelse av tjänsten',
      ord: ['tjänst', 'tjanst', 'byrå', 'konsult', 'försäkring', 'forsakring', 'bank', 'utbildning', 'kurs', 'resa', 'resor', 'travel', 'hotell', 'hotel', 'event ', 'evenemang', 'bokning', 'abonnemang', 'prenumeration', 'klinik', 'mäklar'] }
  ];
  var ALLM = { id: 'ovrigt', namn: 'ert erbjudande', product: null, format: 'en kort, ärlig video där kreatören visar hur hon själv använder det' };
  var SIZES = [
    { id: 'ny', label: 'Nystartat', ord: ['nystart', 'startup', 'start-up', 'precis startat', 'ny butik', 'nytt företag', 'nytt bolag', 'lanserar snart'] },
    { id: 'liten', label: 'Litet, 1–10 anställda', ord: ['litet', 'liten', 'småföretag', 'smaforetag', 'enmans', 'familjeföretag'] },
    { id: 'mellan', label: 'Mellanstort, 10–50', ord: ['mellanstor', 'medelstor', 'växande', 'scaleup', 'scale-up'] },
    { id: 'stor', label: 'Stort, över 50', ord: ['stort företag', 'storbolag', 'koncern', 'kedja', 'klädkedja', 'butikskedja', 'butiker i hela', 'börsnoterad', 'enterprise', 'marknadsledande'] }
  ];
  var GOALS = [
    { id: 'testa', label: 'Testa TikTok', ord: ['testa', 'prova', 'pilot', 'första gången', 'forsta gangen', 'nyfiken'] },
    { id: 'salja', label: 'Sälja mer', ord: ['sälja', 'salja', 'försäljning', 'forsaljning', 'konvert', 'omsättning'] },
    { id: 'lansera', label: 'Lansera något nytt', ord: ['lansera', 'lansering', 'launch', 'ny produkt', 'ny kollektion', 'släpp'] },
    { id: 'varumarke', label: 'Bygga varumärket', ord: ['varumärke', 'varumarke', 'brand', 'kännedom', 'kannedom', 'synas', 'räckvidd', 'rackvidd'] }
  ];

  var st, busy = false;
  function fresh() { st = { text: '', cat: null, size: null, goal: null, product: null, step: null, done: false }; }
  fresh();

  /* ord matchas i början av ett ord ("kläd" träffar "klädbutik" men "mat " inte "format");
     i ett domännamn räcker det att ordet finns med, eftersom domäner skrivs ihop */
  function has(t, ord, dom) {
    for (var i = 0; i < ord.length; i++) {
      var w = ord[i], k = w.trim();
      if (new RegExp('(^|[^a-zåäö0-9])' + w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).test(t)) return true;
      if (dom && k.length >= 4 && dom.indexOf(k) > -1) return true;
    }
    return false;
  }
  function pick(list, t, dom) { for (var i = 0; i < list.length; i++) if (has(t, list[i].ord, dom)) return list[i]; return null; }
  function domain(t) { var m = t.match(/(?:https?:\/\/)?(?:www\.)?([a-z0-9åäö-]+(?:\.[a-z0-9åäö-]+)*\.[a-z]{2,})(?:\/\S*)?/i); return m ? m[1].toLowerCase() : null; }

  /* plockar ut allt som går att förstå ur en fritext, utan att skriva över det vi redan vet */
  function absorb(raw) {
    var t = ' ' + raw.toLowerCase() + ' ';
    var c = pick(CATS, t, domain(raw)); if (c && !st.cat) { st.cat = c; if (st.product === null && c.product === false) st.product = false; }
    var s = pick(SIZES, t);
    var n = t.match(/(\d+)\s*(?:anställda|anstallda|personer|pers|medarbetare)/);
    if (n) { var v = +n[1]; s = SIZES[v <= 1 ? 0 : v <= 10 ? 1 : v <= 50 ? 2 : 3]; }
    if (s && !st.size) st.size = s;
    var g = pick(GOALS, t); if (g && !st.goal) st.goal = g;
  }

  /* ---- beslutet: storlek ger nivå, målet flyttar ett steg, affiliate när produkten kan vara betalningen ---- */
  function decide() {
    var base = { ny: 0, liten: 0, mellan: 1, stor: 2 }[st.size ? st.size.id : 'liten'];
    var g = st.goal ? st.goal.id : 'salja';
    if (g === 'testa') base = Math.max(base - 1, 0);
    if ((g === 'lansera' || g === 'varumarke') && st.size && st.size.id === 'liten') base = 1;
    var p = PK[ORDER[Math.min(base, ORDER.length - 1)]];
    var aff = st.product === true ? (st.size && st.size.id === 'ny' ? 'forst' : 'ocksa') : null;
    return { p: p, aff: aff };
  }
  function why(r) {
    var s = st.size ? st.size.id : null, g = st.goal ? st.goal.id : null, a = [];
    if (r.p.id === ORDER[0]) a.push(s === 'ny' || s === 'liten' ? 'Ni är ett mindre bolag, så börja med ett upplägg som går att utvärdera utan stor insats.' : 'Ni vill testa först, så börja i liten skala och väx när ni sett siffrorna.');
    else if (r.p.id === ORDER[ORDER.length - 1]) a.push('Ni är stora nog för att behöva bredd: många kreatörer samtidigt, så att samma publik ser er flera gånger.');
    else a.push(g === 'lansera' ? 'En lansering behöver synas på flera konton samma veckor, och då räcker inte en pilot.' : 'Ni är stora nog för att gå förbi teststadiet, men behöver inte hela nätverket.');
    return a.join(' ');
  }

  /* ---- rendering ---- */
  function scroll() { log.scrollTop = log.scrollHeight; }
  function add(cls, html) { var d = document.createElement('div'); d.className = cls; d.innerHTML = html; log.appendChild(d); scroll(); return d; }
  function me(t) { add('px-msg me', esc(t)); }
  function bot(html, then) {
    busy = true;
    var ty = add('px-typing', '<i></i><i></i><i></i>');
    setTimeout(function () { ty.remove(); add('px-msg bot', html); busy = false; if (then) then(); }, 520);
  }
  function opts(list, cb) {
    var w = add('px-opts', '');
    list.forEach(function (o) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'px-chip'; b.textContent = o.label;
      b.onclick = function () { if (busy) return; w.remove(); me(o.label); cb(o); };
      w.appendChild(b);
    });
    scroll();
  }
  function clearOpts() { [].forEach.call(log.querySelectorAll('.px-opts'), function (n) { n.remove(); }); }

  function next() {
    clearOpts();
    if (!st.cat) {
      st.step = 'cat';
      return bot('Vad är det ni säljer?', function () {
        opts(CATS.map(function (c) { return { label: c.namn.charAt(0).toUpperCase() + c.namn.slice(1), c: c }; }).concat([{ label: 'Något annat', c: ALLM }]),
          function (o) { st.cat = o.c; if (o.c.product === false) st.product = false; next(); });
      });
    }
    if (!st.size) {
      st.step = 'size';
      return bot('Hur stort är företaget ungefär?', function () { opts(SIZES, function (o) { st.size = o; next(); }); });
    }
    if (!st.goal) {
      st.step = 'goal';
      return bot('Vad vill ni främst få ut av kreatörerna?', function () { opts(GOALS, function (o) { st.goal = o; next(); }); });
    }
    if (st.product === null) {
      st.step = 'product';
      return bot('Sista frågan: är det en produkt som kreatörerna kan få hem och använda själva?', function () {
        opts([{ label: 'Ja, det är det', v: true }, { label: 'Nej, inte riktigt', v: false }], function (o) { st.product = o.v; next(); });
      });
    }
    recommend();
  }

  function recommend() {
    st.step = 'done'; st.done = true;
    var r = decide(), p = r.p;
    var mix = p.mixtext;
    var mail = 'Hej Luminate!\n\nVi har fått ett förslag på er prissida och vill veta mer.\n\n' +
      'Vi säljer: ' + st.cat.namn + '\nFöretag: ' + st.size.label + '\nMål: ' + st.goal.label +
      '\nFörslag: ' + p.name + ', ' + p.paid + ' videor, ' + kr(p.final) + ' exkl. moms' +
      (r.aff ? '\nVi vill också höra mer om affiliateprogrammet.' : '') +
      '\n\nDet vi skrev: ' + st.text + '\n\nFöretag:\nKontaktperson:\nTelefon:';
    var affHtml = '';
    if (r.aff === 'forst') affHtml = '<p class="aff"><b>Börja hellre med affiliate.</b> För ett nystartat bolag med en produkt kreatörerna vill ha är vårt affiliateprogram ofta ett bättre första steg: från ' + kr(D.affiliate.from) + '/mån, och kreatörerna får produkten och provision på det de säljer. <a href="/affiliate.html">Läs om affiliateprogrammet</a></p>';
    if (r.aff === 'ocksa') affHtml = '<p class="aff"><b>Ni passar också för affiliate.</b> Har ni en produkt kreatörerna vill ha kan ni ha löpande videor varje månad från ' + kr(D.affiliate.from) + '/mån, vid sidan av kampanjen. <a href="/affiliate.html">Läs om affiliateprogrammet</a></p>';
    bot('Då har jag det jag behöver. Det här är upplägget jag skulle börja med för ' + esc(st.cat.namn) + ':', function () {
      var c = add('px-rec',
        '<span class="tag">Förslag för er</span><h3>' + esc(p.name) + '</h3>' +
        '<div class="price">' + kr(p.final) + '<small>exkl. moms</small></div>' +
        '<ul><li><b>' + p.paid + ' videor</b> från ' + p.paid + ' kreatörer: ' + esc(mix) + '</li>' +
        (p.free ? '<li><b>' + p.free + ' mindre kreatörer ingår</b> utan kostnad, så ni får ' + p.videos + ' videor</li>' : '') +
        '<li>Uppskattningsvis <b>' + kviews(p.views) + ' visningar</b> organiskt, räknat på kreatörernas medianvisningar</li>' +
        '<li>Format vi skulle föreslå: ' + esc(st.cat.format) + '</li></ul>' +
        '<p>' + esc(why(r)) + '</p>' + affHtml +
        '<div class="px-acts"><button type="button" class="px-btn" data-open="' + p.id + '">Läs mer om ' + esc(p.name) + '</button>' +
        '<a class="px-btn alt" href="' + D.boka + '" target="_blank" rel="noopener">Boka möte</a>' +
        '<a class="px-btn alt" href="mailto:hello@luminatemedia.se?subject=' + encodeURIComponent('Förslag från prissidan: ' + p.name) + '&body=' + encodeURIComponent(mail) + '">Mejla förslaget till oss</a></div>');
      c.querySelector('[data-open]').onclick = function () { openPk(p.id); };
      setTimeout(function () {
        add('px-msg bot', 'Förslaget är en utgångspunkt, inte en offert. Vilka kreatörer det blir bestämmer vi tillsammans. Fråga gärna vidare, till exempel om Spark Ads eller de andra paketen.');
      }, 500);
    });
  }

  /* ---- frågor mitt i samtalet ---- */
  var FAQ = [
    { ord: ['spark', 'annonser', 'annons', 'boosta'], svar: function () { return 'Spark Ads-rättigheter köper ni efter publicering, när ni sett vad videon gjorde organiskt. Påslaget är +' + D.spark[0].up + ' % av kreatörens grundpris för ' + D.spark[0].label + ', upp till +' + D.spark[D.spark.length - 1].up + ' % för ' + D.spark[D.spark.length - 1].label + '.'; } },
    { ord: ['moms'], svar: function () { return 'Alla priser är exklusive moms.'; } },
    { ord: ['affiliate', 'provision'], svar: function () { return 'I affiliateprogrammet gör kreatörerna löpande videor varje månad och får produkten och provision på det de säljer. Det kostar från ' + kr(D.affiliate.from) + '/mån. <a href="/affiliate.html">Läs mer här</a>.'; } },
    { ord: ['minsta', 'minimum', 'en video', 'bara en'], svar: function () { return 'Det finns ingen minsta beställning. Ni kan boka en enskild video från ' + kr(D.min) + '.'; } },
    { ord: ['rabatt', 'volym'], svar: function () { return 'Priset per video sjunker med volymen: från −' + D.ladder[0][1] + ' % vid ' + D.ladder[0][0] + ' videor till −' + D.ladder[D.ladder.length - 1][1] + ' % vid ' + D.ladder[D.ladder.length - 1][0] + ' eller fler.'; } },
    { ord: ['paket', 'andra', 'alternativ', 'billigare', 'större', 'storre', 'mindre'], svar: function () { return 'Vi har tre paket: ' + D.paket.map(function (p) { return '<b>' + esc(p.name) + '</b> ' + kr(p.final); }).join(', ') + '. Korten under chatten visar vad som ingår i vart och ett.'; } },
    { ord: ['pris', 'kosta', 'kostar', 'budget', 'dyrt'], svar: function () { return 'En video kostar ' + kr(D.min) + '–' + kr(D.max) + ' beroende på kreatörens räckvidd. Paketen börjar på ' + kr(D.paket[0].final) + '. Hela prislistan står längre ner på sidan.'; } },
    { ord: ['kontakt', 'ringa', 'möte', 'mote', 'prata', 'mejl', 'mail'], svar: function () { return 'Boka ett möte <a href="' + D.boka + '" target="_blank" rel="noopener">här</a> eller mejla <a href="mailto:hello@luminatemedia.se">hello@luminatemedia.se</a>.'; } }
  ];

  function handle(raw) {
    raw = raw.trim(); if (!raw || busy) return;
    me(raw);
    var t = ' ' + raw.toLowerCase() + ' ';
    var isQ = raw.indexOf('?') > -1 || /^(vad|hur|kan|har|finns|ingår|ingar|vilka|varför)\b/i.test(raw);
    if (isQ || st.done) {
      var f = pick(FAQ, t);
      if (f) return bot(f.svar(), st.done ? null : next);
      if (st.done) return bot('Det tar vi bäst på ett kort möte, så får ni ett rakt svar. <a href="' + D.boka + '" target="_blank" rel="noopener">Boka en tid här</a> eller mejla <a href="mailto:hello@luminatemedia.se">hello@luminatemedia.se</a>.');
    }
    var before = [st.cat, st.size, st.goal];
    absorb(raw);
    if (st.step === 'product' && st.product === null) {
      if (/\b(ja|japp|absolut|visst|yes)\b/.test(t)) st.product = true;
      else if (/\b(nej|nope|no|inte)\b/.test(t)) st.product = false;
    }
    /* förstod vi inget nytt tar vi svaret som det är och går vidare, så att samtalet aldrig fastnar */
    if (st.step === 'cat' && !st.cat) st.cat = { id: 'ovrigt', namn: raw.length < 40 ? raw.toLowerCase() : 'ert erbjudande', product: null, format: ALLM.format };
    else if (st.step === 'size' && !st.size) st.size = SIZES[1];
    else if (st.step === 'goal' && !st.goal) st.goal = GOALS[1];
    else if (st.step === 'product' && st.product === null) st.product = false;
    next();
  }

  function start(raw) {
    raw = raw.trim(); if (!raw) { input.focus(); return; }
    fresh(); st.text = raw; log.innerHTML = '';
    chat.hidden = false;
    me(raw); absorb(raw);
    var dom = domain(raw), intro;
    if (st.cat && dom) intro = 'Tack! Av <b>' + esc(dom) + '</b> att döma handlar det om ' + esc(st.cat.namn) + '. Jag ställer ett par snabba frågor och föreslår sedan ett upplägg.';
    else if (st.cat) intro = 'Tack! ' + esc(st.cat.namn.charAt(0).toUpperCase() + st.cat.namn.slice(1)) + ' alltså. Ett par snabba frågor, sedan får ni ett förslag.';
    else if (dom) intro = 'Tack! Jag kan inte läsa <b>' + esc(dom) + '</b> härifrån, så jag frågar i stället. Det tar en halv minut.';
    else intro = 'Tack! Jag ställer ett par snabba frågor och föreslår sedan ett upplägg med pris.';
    bot(intro, next);
    input.value = ''; input.style.height = '';
    setTimeout(function () { chat.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }, 80);
  }

  ask.addEventListener('submit', function (e) { e.preventDefault(); start(input.value); });
  input.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); start(input.value); } });
  input.addEventListener('input', function () { input.style.height = 'auto'; input.style.height = Math.min(input.scrollHeight, 160) + 'px'; });
  [].forEach.call(document.querySelectorAll('[data-ex]'), function (b) { b.onclick = function () { start(b.getAttribute('data-ex')); }; });
  say.addEventListener('submit', function (e) { e.preventDefault(); var v = sayIn.value; sayIn.value = ''; handle(v); });
  document.getElementById('px-reset').onclick = function () { fresh(); log.innerHTML = ''; chat.hidden = true; input.focus(); };

  /* ---- läs mer-rutorna ---- */
  function openPk(id) { var d = document.getElementById('pk-' + id); if (d && d.showModal) d.showModal(); }
  [].forEach.call(document.querySelectorAll('[data-pk]'), function (b) { b.onclick = function () { openPk(b.getAttribute('data-pk')); }; });
  [].forEach.call(document.querySelectorAll('.px-dlg'), function (d) {
    d.addEventListener('click', function (e) { if (e.target === d || e.target.hasAttribute('data-close')) d.close(); });
  });
  window.LM_CHAT = { start: start, handle: handle, state: function () { return st; }, decide: decide };
})();
