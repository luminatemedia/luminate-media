/* Kampanjmotorn — räknar fram ett namngivet kampanjförslag ur ämne och budget.

   Ren logik utan DOM, så att samma kod körs i webbläsaren (kampanj-chatt.js)
   och i Node (scripts/test_kampanjmotor.mjs). Priser, rabattrappa och Spark-påslag
   skickas in från index.html (TIERS, SPARK, kmDiscount) — motorn har inga egna priser,
   så prissidan och förslaget kan aldrig visa olika siffror.

   Reglerna i korthet:
   1. En kreatör föreslås för ett ämne bara om hon har gjort videor i ämnet
      (data/match.json) eller har det i sin profil. Annars föreslås hon inte.
   2. Estimerade visningar är hennes median, aldrig ett snitt eller en toppvideo.
   3. Kreatörerna ryms alltid i budgeten. Räcker budgeten inte står det i klartext.
   4. Spark Ads är en rekommendation ovanpå budgeten och räknas aldrig in i den.
*/
(function (root, factory) {
  if (typeof module === 'object' && module.exports) module.exports = factory();
  else root.LMKampanj = factory();
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  /* Tröskel för att ett ämne räknas som bevisat hos en kreatör. */
  var MIN_BEVISAD = 3;
  /* Hur mycket svagare underlag väger i rankningen. */
  var VIKT = { bevisad: 1, gjort: 0.8, profil: 0.6, bred: 0.5 };
  /* Ämnesmedianen får inte lyfta estimatet mer än så här över hennes vanliga nivå:
     tre videor kan råka innehålla en toppvideo. Nedåt finns ingen spärr. */
  var MAX_LYFT = 1.5;
  /* Spark Ads läggs ovanpå kreatörsbudgeten och räknas aldrig in i den (Love 16 nov 2026).
     Rekommenderad nivå: rättigheter för ungefär var tredje video och en mediebudget
     som är en fjärdedel av kreatörskostnaden. Förslagsvärden — ändras här. */
  var SPARK_VIDEOANDEL = 0.3;
  var SPARK_MEDIAANDEL = 0.25;
  var SPARK_MEDIA_MIN = 2000;
  /* Kostnad per tittare som stannade minst sex sekunder i höstkampanjen 2026.
     Samma siffra som står på prissidan. */
  var KR_PER_6S = 0.06;
  var STANDARD_ANTAL = 5;
  /* Prislistan börjar vid 5 000 följare. Mindre konton har inget pris och föreslås inte. */
  var MIN_FOLJARE = 5000;
  /* En kreatör föreslås inte om hennes estimerade visningar är färre än priset i kronor
     (under en visning per krona): det är ett dåligt köp hur väl ämnet än passar. */
  var MIN_VISN_PER_KR = 1;

  function tierFor(tiers, followers) {
    /* Klasserna följer följarintervallen på prissidan. */
    var grans = [190000, 90000, 60000, 20000];
    for (var i = 0; i < grans.length; i++) if (followers >= grans[i]) return i;
    return tiers.length - 1;
  }

  /* Underlaget för en kreatör i de valda ämnena. */
  function underlag(m, cats, own) {
    if (!cats.length) return { niva: 'bred', n: 0, views: own, basta: null };
    var n = 0, vikt = 0, summa = 0, basta = null;
    cats.forEach(function (c) {
      var d = m && m.cats && m.cats[c];
      if (!d) return;
      n += d.n;
      if (!basta || d.n > basta.n) basta = { key: c, n: d.n, med: d.med };
      if (d.n >= MIN_BEVISAD) { vikt += d.n; summa += d.n * d.med; }
    });
    if (vikt) {
      var catMed = summa / vikt;
      return { niva: 'bevisad', n: n, views: own ? Math.min(catMed, own * MAX_LYFT) : catMed, basta: basta };
    }
    if (n) return { niva: 'gjort', n: n, views: own, basta: basta };
    var iProfil = m && m.profil && cats.some(function (c) { return m.profil.indexOf(c) >= 0; });
    if (iProfil) return { niva: 'profil', n: 0, views: own, basta: null };
    return null;
  }

  function kostnad(valda, v, ctx) {
    var list = valda.reduce(function (s, k) { return s + k.price; }, 0) * v;
    var disc = ctx.discount(valda.length * v);
    return { list: list, disc: disc, saved: list * disc / 100, net: list * (1 - disc / 100) };
  }

  /* ctx: { tiers, spark:[{label,up}], discount(videos), free:{count,views},
            creators:[{handle,name,followers,median}], match:{creators:{}, categories:[]} }
     inp: { cats:[], budget:number|null, videos:1|2, spark:false|periodIndex, antal:number|null } */
  function build(inp, ctx) {
    var cats = (inp.cats || []).slice(0, 3);
    var v = inp.videos === 2 ? 2 : 1;
    var sparkOn = inp.spark !== false && inp.spark != null;
    var period = sparkOn ? ctx.spark[inp.spark] : null;
    var budget = inp.budget && inp.budget > 0 ? inp.budget : null;
    var notes = [];
    var labels = {};
    (ctx.match.categories || []).forEach(function (c) { labels[c.key] = c.label; });

    /* ctx.free.count konton (de minsta) kan följa med utan kostnad och prissätts då aldrig.
       Chatten skickar 0: inga gratiskreatörer i förslag (Willem 31 okt 2026). */
    var roster = ctx.creators.filter(function (c) { return c.followers > 0 && c.median > 0; })
      .sort(function (a, b) { return b.followers - a.followers; });
    var betalda = roster.slice(0, Math.max(0, roster.length - ctx.free.count));

    var kandidater = [];
    betalda.forEach(function (c) {
      var m = ctx.match.creators[c.handle];
      if (!m) return;                       /* inte i underlaget: föreslås inte automatiskt */
      var u = underlag(m, cats, c.median);
      if (!u) return;
      var ti = tierFor(ctx.tiers, c.followers);
      if (c.followers < MIN_FOLJARE || u.views < ctx.tiers[ti].price * MIN_VISN_PER_KR) return;
      kandidater.push({
        handle: c.handle, name: c.name, followers: c.followers, tier: ti, kort: !!c.kort,
        tierLabel: ctx.tiers[ti].label, price: ctx.tiers[ti].price,
        views: Math.round(u.views), niva: u.niva, n: u.n, basta: u.basta,
        poang: VIKT[u.niva] * u.views / ctx.tiers[ti].price
      });
    });
    /* Underlaget går först: en kreatör som bevisligen gör ämnet väljs före en som bara har det
       i profilen, även om den senare ger fler visningar per krona. */
    var RANG = { bevisad: 0, gjort: 1, profil: 2, bred: 3 };
    kandidater.sort(function (a, b) { return (RANG[a.niva] - RANG[b.niva]) || (b.poang - a.poang); });

    /* Hela budgeten går till kreatörsvideor. Spark Ads rekommenderas ovanpå. */
    var organiskBudget = budget;

    var valda = [];
    function ryms(k) {
      if (!organiskBudget) return true;
      return kostnad(valda.concat([k]), v, ctx).net <= organiskBudget;
    }
    var tak = inp.antal || (budget ? betalda.length : STANDARD_ANTAL);

    /* Ett stort konto bär kampanjen — men bara om det passar ämnet och inte äter upp budgeten. */
    var stor = kandidater.filter(function (k) { return k.tier <= 1 && k.niva !== 'profil' && k.niva !== 'bred'; })[0]
            || (cats.length ? null : kandidater.filter(function (k) { return k.tier <= 1; })[0]);
    if (stor && tak >= 3 && (!organiskBudget || stor.price * v * 3 <= organiskBudget)) valda.push(stor);

    kandidater.forEach(function (k) {
      if (valda.length >= tak || valda.indexOf(k) >= 0) return;
      if (ryms(k)) valda.push(k);
    });
    valda.sort(function (a, b) { return (RANG[a.niva] - RANG[b.niva]) || (b.views - a.views); });

    var k = kostnad(valda, v, ctx);
    var views = (valda.reduce(function (s, x) { return s + x.views; }, 0) + (valda.length && ctx.free.count ? ctx.free.views : 0)) * v;

    /* Spark Ads, ovanpå: rättigheter för de videor som går bäst och en rekommenderad mediebudget. */
    var spark = null;
    if (sparkOn && valda.length) {
      var antal = Math.max(1, Math.round(valda.length * v * SPARK_VIDEOANDEL));
      var ratt = Math.round(antal * k.list / (valda.length * v) * period.up);
      var media = Math.max(SPARK_MEDIA_MIN, Math.round(k.net * SPARK_MEDIAANDEL / 1000) * 1000);
      spark = {
        period: period.label, up: period.up, videos: antal, rights: ratt, media: media,
        viewers6s: Math.round(media / KR_PER_6S / 1000) * 1000, total: ratt + media
      };
    }

    if (!kandidater.length) {
      notes.push('Vi har inga kreatörer med underlag i det ämnet ännu. Boka ett möte så går vi igenom nätverket tillsammans.');
    } else if (!valda.length) {
      notes.push('Budgeten räcker inte till en kreatör i det här upplägget. Den billigaste som passar kostar ' +
        Math.min.apply(null, kandidater.map(function (x) { return x.price; })) * v + ' kr.');
    } else if (cats.length && valda.every(function (x) { return x.niva === 'profil'; })) {
      notes.push('Ingen av dem har gjort videor i just det ämnet sedan augusti. Urvalet bygger på deras profiler.');
    } else if (cats.length && !valda.some(function (x) { return x.niva === 'bevisad'; })) {
      notes.push('Vi har få videor i det här ämnet sedan augusti, så underlaget är tunt. På ett möte visar vi fler exempel ur nätverket.');
    }
    if (budget && valda.length && kandidater.length === valda.length && k.net < (organiskBudget || budget) * 0.7) {
      notes.push('Alla kreatörer som passar ämnet är med. Resten av budgeten gör mest nytta som två videor per kreatör.');
    }

    return {
      cats: cats, labels: labels, videos: v, budget: budget,
      creators: valda, kandidater: kandidater.length,
      free: valda.length && ctx.free.count ? { count: ctx.free.count, views: ctx.free.views } : null,
      list: k.list, disc: k.disc, saved: k.saved, organic: k.net,
      spark: spark, total: k.net,
      views: views, videoCount: (valda.length + (valda.length ? ctx.free.count : 0)) * v, notes: notes
    };
  }

  /* Varför en kreatör är med — en mening som går att kontrollera mot datan. */
  function motivering(k, labels) {
    var l = k.basta ? (labels[k.basta.key] || k.basta.key).toLowerCase() : '';
    if (k.niva === 'bevisad') return k.basta.n + ' videor inom ' + l + ' sedan augusti';
    if (k.niva === 'gjort') return (k.n === 1 ? '1 video' : k.n + ' videor') + ' inom ' + l + ' sedan augusti';
    if (k.niva === 'profil') return 'Ämnet finns i hennes profil';
    return 'Bred räckvidd';
  }

  /* Tolkar fritext till ämnen. Enkel ordlista — ingen modell, inget skickas någonstans.
     Ett ord i listan matchar början av ett ord i texten ("kläd" → "klädmärke");
     slutar det på $ måste hela ordet stämma ("mat$" matchar inte "material"). */
  var ORD = {
    mode: ['mode', 'kläd', 'klad', 'plagg', 'fashion', 'skor$', 'sko$', 'sneaker', 'väsk', 'vask', 'smycke', 'jeans', 'outfit',
           'accessoar', 'klänning', 'jack', 'streetwear', 'barnkläd', 'barnmode', 'secondhand', 'second', 'vintage', 'klock',
           'glasögon', 'solglasögon', 'underkläd', 'badkläd', 'träningskläd', 'tröj', 'hoodie', 'byx', 'mössa', 'mössor', 'ring$', 'ringar', 'halsband', 'örhäng'],
    skonhet: ['skönhet', 'skonhet', 'smink', 'makeup', 'beauty', 'nagel', 'naglar', 'nagellack', 'parfym', 'doft$', 'dofter', 'frans', 'kosmetik',
              'läpp', 'mascara', 'foundation', 'concealer', 'brun', 'selftan', 'tandblekning'],
    har: ['hår', 'schampo', 'shampoo', 'balsam', 'frisör', 'frisor', 'hair', 'lockar', 'locktång', 'plattång', 'extensions', 'löshår', 'hårfärg'],
    hudvard: ['hud', 'skincare', 'serum', 'ansikts', 'spf$', 'solskydd', 'solkräm', 'cleanser', 'fuktkräm', 'akne', 'kräm', 'krämer'],
    mat: ['mat$', 'maten$', 'matkasse', 'dryck', 'snacks', 'godis', 'kaffe', 'te$', 'bakning', 'bageri', 'restaurang', 'café', 'cafe', 'livsmedel',
          'food', 'läsk', 'proteinbar', 'energidryck', 'choklad', 'glass', 'chips', 'smoothie', 'matcha', 'pizza', 'burgare', 'sushi', 'fika'],
    traning: ['träning', 'traning', 'träna', 'gym', 'sport', 'fotboll', 'löpning', 'löpar', 'kosttillskott', 'protein', 'fitness', 'hälsa', 'halsa',
              'yoga', 'padel', 'golf', 'hockey', 'innebandy', 'cykel', 'vitamin'],
    livsstil: ['livsstil', 'lifestyle', 'vardag', 'app$', 'appen$', 'appar', 'tjänst', 'tjanst', 'event', 'resa$', 'resor', 'resebolag', 'festival',
               'teknik', 'mobil', 'student', 'skola', 'utbildning', 'kurs', 'bank', 'försäkring', 'spel$', 'bok$', 'böcker', 'musik', 'konsert', 'bio$', 'hotell', 'elektronik', 'hörlur'],
    hem: ['hem$', 'hemmet$', 'heminredning', 'inredning', 'möbel', 'mobel', 'pyssel', 'doftljus', 'ljus$', 'kök', 'säng', 'städ', 'textil', 'garn', 'blommor', 'växt']
  };
  function tolkaAmnen(text) {
    var ordITexten = String(text || '').toLowerCase().split(/[^a-zåäöé]+/).filter(Boolean);
    var hits = [];
    Object.keys(ORD).forEach(function (key) {
      var traff = ORD[key].some(function (o) {
        var exakt = o.charAt(o.length - 1) === '$';
        var rot = exakt ? o.slice(0, -1) : o;
        return ordITexten.some(function (w) { return exakt ? w === rot : w.indexOf(rot) === 0; });
      });
      if (traff) hits.push(key);
    });
    return hits.slice(0, 3);
  }
  /* "30 000", "30k", "30 tkr", "0,1 mkr" → kronor. Null om inget tal hittas. */
  function tolkaBelopp(text) {
    var t = String(text || '').toLowerCase().replace(/ /g, ' ');
    var m = t.match(/(\d[\d ]*(?:[.,]\d+)?)\s*(mkr|miljon|tkr|k\b|tusen)?/);
    if (!m) return null;
    var n = parseFloat(m[1].replace(/ /g, '').replace(',', '.'));
    if (!isFinite(n)) return null;
    if (m[2] === 'mkr' || m[2] === 'miljon') n *= 1e6;
    else if (m[2]) n *= 1e3;
    return Math.round(n);
  }

  /* Hittar budgeten i en hel mening: största beloppet på minst 2 000 kr som inte är ett antal
     ("2 videor", "5 kreatörer", "30 dagar", "12 månader"). Null om inget sådant finns. */
  function tolkaBudget(text) {
    var t = String(text || '').toLowerCase().replace(/\u00a0/g, ' ');
    var re = /(\d{1,3}(?: \d{3})+|\d+)(?:[.,](\d+))?\s*(mkr|miljon(?:er)?|tkr|tusen|k(?![a-zåäö]))?\s*([a-zåäö%]*)/g;
    var basta = null, m;
    while ((m = re.exec(t))) {
      if (!m[3] && /^(video|kreatör|influencer|dag|mån|man|år|st$|styck|vecka|veckor|%|procent|person)/.test(m[4])) continue;
      var n = parseFloat(m[1].replace(/ /g, '') + (m[2] ? '.' + m[2] : ''));
      if (m[3] === 'mkr' || (m[3] && m[3].indexOf('miljon') === 0)) n *= 1e6;
      else if (m[3]) n *= 1e3;
      n = Math.round(n);
      if (n >= 2000 && (basta === null || n > basta)) basta = n;
    }
    return basta;
  }

  return { build: build, motivering: motivering, tierFor: tierFor, tolkaAmnen: tolkaAmnen, tolkaBelopp: tolkaBelopp, tolkaBudget: tolkaBudget,
           MIN_BEVISAD: MIN_BEVISAD, KR_PER_6S: KR_PER_6S };
});
