/* Kampanjassistenten — en styrd chatt som fyller i kampanjmotorns fält.

   Ingen AI-modell och ingen server: svaren tolkas med en ordlista i webbläsaren
   (LMKampanj.tolkaAmnen / tolkaBelopp) och ingenting besökaren skriver skickas någonstans.
   Priserna kommer från kalkylatorns egna konstanter i index.html (TIERS, SPARK, kmDiscount,
   KM_FREE), så förslaget, kalkylatorn och prissidan visar alltid samma siffror.
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
  var st = { steg: 'amne', cats: [], budget: null, videos: 1, spark: false };
  var BUDGETAR = [15000, 30000, 60000, 100000];

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

  /* Botens rader kommer med en kort paus, så att det läses som ett samtal. */
  var ko = Promise.resolve();
  function bot(text, efter) {
    ko = ko.then(function () {
      return new Promise(function (klar) {
        var visa = function () {
          var m = el('div', 'kc-msg kc-bot');
          m.innerHTML = text;               /* bara egna, fasta texter — aldrig besökarens */
          laggTill(m);
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
  function chips(val, opts) {
    opts = opts || {};
    var rad = el('div', 'kc-chips');
    val.forEach(function (v) {
      var b = el('button', v.cls || '', v.text);
      b.type = 'button';
      b.addEventListener('click', function () {
        if (opts.flera && !v.klar) { b.classList.toggle('on'); if (v.byt) v.byt(b.classList.contains('on')); return; }
        b.classList.add('on');
        rad.classList.add('done');
        v.valj();
      });
      rad.appendChild(b);
    });
    laggTill(rad);
    return rad;
  }
  function stangChips() {
    log.querySelectorAll('.kc-chips:not(.done)').forEach(function (r) { r.classList.add('done'); });
  }

  /* ---------- stegen ---------- */
  function fragaAmne() {
    st.steg = 'amne';
    var valda = [];
    bot('Vad säljer ni? Välj upp till tre, eller skriv det med egna ord.', function () {
      var val = ctx.match.categories.map(function (c) {
        return { text: c.label, byt: function (pa) {
          if (pa) valda.push(c.key); else valda = valda.filter(function (k) { return k !== c.key; });
        } };
      });
      val.push({ text: 'Klar →', cls: 'kc-go', klar: true, valj: function () {
        if (!valda.length) { bot('Välj minst ett ämne, eller skriv vad ni säljer.'); fragaAmne(); return; }
        valda = valda.slice(0, 3);
        user(valda.map(function (k) { return etikett(k); }).join(', '));
        st.cats = valda; fragaBudget();
      } });
      chips(val, { flera: true });
    });
  }
  function etikett(k) {
    var c = ctx.match.categories.filter(function (x) { return x.key === k; })[0];
    return c ? c.label : k;
  }
  function fragaBudget() {
    st.steg = 'budget';
    bot('Vilken budget utgår ni från? Skriv ett belopp eller välj ett.', function () {
      var val = BUDGETAR.map(function (b) {
        return { text: kr(b), valj: function () { user(kr(b)); st.budget = b; fragaVideor(); } };
      });
      val.push({ text: 'Vet inte än', valj: function () { user('Vet inte än'); st.budget = null; fragaVideor(); } });
      chips(val);
    });
  }
  function fragaVideor() {
    st.steg = 'videor';
    bot('En eller två videor per kreatör? Två ger större volymrabatt och fler chanser att en video slår igenom.', function () {
      chips([
        { text: '1 video', valj: function () { user('1 video'); st.videos = 1; fragaSpark(); } },
        { text: '2 videor', valj: function () { user('2 videor'); st.videos = 2; fragaSpark(); } }
      ]);
    });
  }
  function fragaSpark() {
    st.steg = 'spark';
    bot('Vill ni kunna annonsera med videorna (Spark Ads)? Då körs kreatörens video som annons från ert eget konto.', function () {
      chips([
        { text: 'Ja', valj: function () { user('Ja'); fragaPeriod(); } },
        { text: 'Nej, bara organiskt', valj: function () { user('Nej, bara organiskt'); st.spark = false; visaForslag(); } },
        { text: 'Bestämmer senare', valj: function () {
          user('Bestämmer senare'); st.spark = false;
          bot('Det går bra. Ni har 14 dagar på er efter publicering, med de organiska siffrorna framför er.');
          visaForslag();
        } }
      ]);
    });
  }
  function fragaPeriod() {
    st.steg = 'period';
    bot('Hur länge vill ni kunna annonsera med videorna?', function () {
      chips(SPARK.map(function (s, i) {
        return { text: s.label, valj: function () { user(s.label); st.spark = i; visaForslag(); } };
      }));
    });
  }

  /* ---------- förslaget ---------- */
  function visaForslag() {
    st.steg = 'klar';
    var p = M.build({ cats: st.cats, budget: st.budget, videos: st.videos, spark: st.spark }, ctx);
    if (!p.creators.length) {
      bot(p.notes[0] || 'Jag fick inte ihop ett förslag med de valen.', function () { efterVal(false); });
      return;
    }
    bot('Här är ert förslag. Det bygger på vad varje kreatör faktiskt har gjort och hur hennes videor brukar gå.', function () {
      laggTill(kort(p));
      efterVal(true);
    });
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
      var img = el('img'); img.src = 'assets/creators/' + k.handle + '.webp'; img.alt = ''; img.width = 48; img.height = 48; img.loading = 'lazy';
      li.appendChild(img);
      var who = el('a', 'kc-who'); who.href = 'kreatorer/' + k.handle + '.html';
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
    function rad(a, b, cls) { var d = el('div', cls || ''); d.appendChild(el('span', '', a)); d.appendChild(el('span', '', b)); lines.appendChild(d); }
    rad('Kreatörer, ' + p.creators.length * p.videos + (p.creators.length * p.videos === 1 ? ' video' : ' videor'), kr(p.list));
    if (p.disc) rad('Volymrabatt −' + p.disc + ' %', '−' + kr(p.saved), 'kc-minus');
    if (p.spark) {
      rad('Spark Ads-rättigheter, ' + p.spark.videos + (p.spark.videos === 1 ? ' video' : ' videor') + ' · ' + p.spark.period, kr(p.spark.rights));
      if (p.spark.media) rad('Mediebudget i ert eget annonskonto', kr(p.spark.media));
    }
    rad('Totalt, exklusive moms', kr(p.total), 'kc-total');
    c.appendChild(lines);

    if (p.spark) {
      var s = el('p', 'kc-spark');
      s.innerHTML = '<b>Så använder ni Spark Ads:</b> vänta 48 timmar efter publicering och lägg annonspengarna på ' +
        (p.spark.videos === 1 ? 'den video' : 'de ' + p.spark.videos + ' videor') + ' som gått bäst organiskt. ' +
        (p.spark.viewers6s ? 'Med ' + kr(p.spark.media) + ' i mediebudget räcker det till ungefär ' + visn(p.spark.viewers6s) +
          ' tittare som stannar minst sex sekunder, räknat på vad det kostade i vår höstkampanj 2026. Er kostnad kan bli en annan. '
          : 'Mediebudgeten bestämmer ni själva i ert eget annonskonto. ') +
        'Vill ni att vi sköter annonseringen tar vi 15 % av mediebudgeten.';
      c.appendChild(s);
    }
    p.notes.forEach(function (n) { c.appendChild(el('p', 'kc-note', n)); });
    c.appendChild(el('p', 'kc-fine', 'Ett förslag, inte en offert. Slutgiltigt urval, datum och pris får ni inom två arbetsdagar efter ett möte. ' +
      'Kreatörerna väljs efter videor publicerade sedan augusti 2026 och godkänner själva varje samarbete.'));

    var ctas = el('div', 'kc-ctas');
    var boka = el('button', '', 'Boka 15 min →'); boka.type = 'button';
    boka.addEventListener('click', function () { if (typeof openBooking === 'function') openBooking(); });
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
      (p.budget ? 'Budget: ' + kr(p.budget) + '\n' : '') +
      p.creators.map(function (k) { return '- ' + k.name + ' (@' + k.handle + '), ' + kr(k.price) + '/video'; }).join('\n') +
      '\n- ' + p.free.count + ' mindre kreatörer på köpet\n' + p.videoCount + ' videor totalt' +
      '\nRättigheter: ' + (p.spark ? 'Spark Ads ' + p.spark.period + ', ' + p.spark.videos + ' videor' : 'Bara organiskt') +
      '\nEstimerade visningar: ' + visn(p.views) +
      '\nEstimat: ' + kr(p.total) + (p.disc ? ' (efter ' + p.disc + ' % volymrabatt)' : '') +
      '\n\nFöretag:\nKontaktperson:\nTelefon:';
  }
  function efterVal(harForslag) {
    var val = [
      { text: 'Ändra budget', valj: function () { user('Ändra budget'); fragaBudgetIgen(); } },
      { text: 'Byt ämne', valj: function () { user('Byt ämne'); fragaAmneIgen(); } }
    ];
    if (harForslag) {
      val.push(st.videos === 1
        ? { text: '2 videor per kreatör', valj: function () { user('2 videor per kreatör'); st.videos = 2; visaForslag(); } }
        : { text: '1 video per kreatör', valj: function () { user('1 video per kreatör'); st.videos = 1; visaForslag(); } });
      val.push(st.spark === false
        ? { text: 'Lägg till Spark Ads', valj: function () { user('Lägg till Spark Ads'); fragaPeriod(); } }
        : { text: 'Utan Spark Ads', valj: function () { user('Utan Spark Ads'); st.spark = false; visaForslag(); } });
    }
    val.push({ text: 'Börja om', valj: function () { user('Börja om'); st = { steg: 'amne', cats: [], budget: null, videos: 1, spark: false }; fragaAmne(); } });
    chips(val);
  }
  function fragaBudgetIgen() { fragaBudget(); st.steg = 'budget2'; }
  function fragaAmneIgen() { fragaAmne(); st.steg = 'amne2'; }

  /* Efter en ändring hoppar vi direkt till ett nytt förslag i stället för att fråga allt igen. */
  var _fragaVideor = fragaVideor, _fragaBudget = fragaBudget;
  fragaVideor = function () { if (st.steg === 'budget2') return visaForslag(); _fragaVideor(); };
  fragaBudget = function () { if (st.steg === 'amne2') return visaForslag(); _fragaBudget(); };

  /* ---------- fritext ---------- */
  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var t = input.value.trim();
    if (!t || !ctx) return;
    input.value = '';
    stangChips();
    user(t);
    var lag = t.toLowerCase();

    if (/\b(boka|möte|mote|ring|prata med|människa|manniska|kontakt)\b/.test(lag)) {
      bot('Självklart. Jag öppnar kalendern, så väljer ni en tid som passar.');
      ko = ko.then(function () { if (typeof openBooking === 'function') openBooking(); });
      return;
    }
    var steg = st.steg.replace('2', '');
    var belopp = M.tolkaBelopp(t);
    var amnen = M.tolkaAmnen(t);

    if (steg === 'amne') {
      if (amnen.length) { st.cats = amnen; bot('Då räknar jag på <b>' + amnen.map(etikett).join(', ').toLowerCase() + '</b>.'); return fragaBudget(); }
      bot('Jag hittar ingen kategori som passar det. Välj den som ligger närmast, så tar vi detaljerna på ett möte.');
      return fragaAmne();
    }
    if (steg === 'budget') {
      if (/vet inte|ingen aning|osäker|osaker/.test(lag)) { st.budget = null; return fragaVideor(); }
      if (belopp && belopp >= 2000) { st.budget = belopp; bot('Då utgår jag från <b>' + kr(belopp) + '</b>.'); return fragaVideor(); }
      bot('Skriv budgeten som ett belopp i kronor, till exempel 30 000.');
      return _fragaBudget();
    }
    if (steg === 'videor') {
      st.videos = /2|två|tva/.test(lag) ? 2 : 1;
      return fragaSpark();
    }
    if (steg === 'spark') {
      if (/^(ja|japp|yes|gärna|garna)\b/.test(lag) || /spark|annons/.test(lag) && !/nej|inte|utan/.test(lag)) return fragaPeriod();
      st.spark = false; return visaForslag();
    }
    if (steg === 'period') {
      var i = /12|år|ar\b/.test(lag) ? 3 : /6/.test(lag) ? 2 : /90|tre/.test(lag) ? 1 : 0;
      st.spark = i; return visaForslag();
    }
    /* efter förslaget: ändra det som går att känna igen */
    var andrat = false;
    if (belopp && belopp >= 2000) { st.budget = belopp; andrat = true; }
    if (amnen.length) { st.cats = amnen; andrat = true; }
    if (/utan spark|inga annonser|bara organiskt/.test(lag)) { st.spark = false; andrat = true; }
    else if (/spark|annons/.test(lag) && st.spark === false) { return fragaPeriod(); }
    if (/\b(2|två|tva) video/.test(lag)) { st.videos = 2; andrat = true; }
    else if (/\b(1|en) video/.test(lag)) { st.videos = 1; andrat = true; }
    if (andrat) return visaForslag();
    bot('Jag kan räkna om förslaget efter ämne, budget, antal videor och Spark Ads. Allt annat tar vi gärna på ett möte.', function () {
      chips([{ text: 'Boka 15 min →', cls: 'kc-go', valj: function () { if (typeof openBooking === 'function') openBooking(); } }]);
    });
  });

  /* ---------- start ---------- */
  function namnOchKonton() {
    var kort = {};
    document.querySelectorAll('.ccard[data-handle]').forEach(function (c) {
      var b = c.querySelector('.cc-info b');
      kort[c.dataset.handle] = b ? b.textContent : c.dataset.handle;
    });
    return kort;
  }
  function hamta(url) { return fetch(url, { cache: 'no-cache' }).then(function (r) { if (!r.ok) throw new Error(url); return r.json(); }); }

  Promise.all([hamta('data/stats.json'), hamta('data/views.json'), hamta('data/match.json')]).then(function (d) {
    var namn = namnOchKonton();
    var creators = Object.keys(namn).map(function (h) {
      return { handle: h, name: namn[h],
               followers: (d[0].creators[h] || {}).followers || 0,
               median: (d[1].creators[h] || {}).median || 0 };
    });
    ctx = { tiers: TIERS, spark: SPARK, discount: kmDiscount, free: { count: KM_FREE.count, views: KM_FREE.views },
            creators: creators, match: d[2] };
    bot('Hej! Jag bygger ett kampanjförslag åt er med namngivna kreatörer, pris och estimerade visningar. Det tar ungefär en minut.');
    fragaAmne();
  }).catch(function () {
    var m = el('div', 'kc-msg kc-bot');
    m.innerHTML = 'Jag kunde inte läsa in nätverkets siffror just nu. Räkna i <a href="#" class="js-proposal-inline">kalkylatorn</a> eller boka ett möte, så hjälper vi er direkt.';
    log.appendChild(m);
    var a = m.querySelector('a');
    a.addEventListener('click', function (e) { e.preventDefault(); if (typeof openProposal === 'function') openProposal(); });
    form.hidden = true;
  });
})();
