const data = JSON.parse(document.getElementById("initial-data").textContent);
const { cfg, channels, roles, guild_id } = data;

// ---------- Channel single-select ----------
function initChannelSelect() {
  const wrap = document.querySelector('.channel-select');
  const btn = wrap.querySelector('.select-btn');
  const dd = wrap.querySelector('.dropdown');
  const optsEl = dd.querySelector('.options');
  const search = dd.querySelector('.search');
  let selected = cfg.log_channel_id || null;

  function render(filter = "") {
    optsEl.innerHTML = "";
    const byCat = {};
    channels
      .filter(c => c.name.toLowerCase().includes(filter.toLowerCase()))
      .forEach(c => {
        const cat = c.category || "Без категории";
        (byCat[cat] = byCat[cat] || []).push(c);
      });
    Object.entries(byCat).forEach(([cat, list]) => {
      const h = document.createElement('div');
      h.className = 'category'; h.textContent = '▾ ' + cat;
      optsEl.appendChild(h);
      list.forEach(c => {
        const o = document.createElement('div');
        o.className = 'option' + (selected === c.id ? ' selected' : '');
        o.innerHTML = `<span>#</span> <span>${c.emoji || ''} ${c.name}</span>`;
        o.onclick = () => {
          selected = c.id; cfg.log_channel_id = c.id;
          btn.innerHTML = `<span>${c.emoji || ''} #${c.name}</span><span class="chevron">▾</span>`;
          btn.classList.add('active');
          dd.hidden = true;
        };
        optsEl.appendChild(o);
      });
    });
  }

  btn.onclick = () => { dd.hidden = !dd.hidden; render(search.value); };
  search.oninput = e => render(e.target.value);
  dd.querySelector('.clear-btn').onclick = () => {
    selected = null; cfg.log_channel_id = null;
    btn.innerHTML = '<span class="placeholder">Выберите канал</span><span class="chevron">▾</span>';
    btn.classList.remove('active');
    dd.hidden = true;
  };

  if (selected) {
    const c = channels.find(x => x.id === selected);
    if (c) btn.innerHTML = `<span>${c.emoji || ''} #${c.name}</span><span class="chevron">▾</span>`;
  }

  document.addEventListener('click', e => {
    if (!wrap.contains(e.target)) dd.hidden = true;
  });
}

// ---------- Roles multiselect ----------
function initRoleMultiselect(rootSelector, cfgKey) {
  const wrap = document.querySelector(rootSelector);
  const chipsEl = wrap.querySelector('.chips');
  const addBtn = wrap.querySelector('.add-chip');
  const dd = wrap.querySelector('.dropdown');
  const optsEl = dd.querySelector('.options');
  const search = dd.querySelector('.search');

  function renderChips() {
    chipsEl.innerHTML = "";
    cfg[cfgKey].forEach(id => {
      const r = roles.find(x => x.id === id);
      if (!r) return;
      const chip = document.createElement('span');
      chip.className = 'chip';
      chip.innerHTML = `${r.name} <span class="x">×</span>`;
      chip.querySelector('.x').onclick = () => {
        cfg[cfgKey] = cfg[cfgKey].filter(x => x !== id);
        renderChips();
      };
      chipsEl.appendChild(chip);
    });
  }

  function renderOptions(filter = "") {
    optsEl.innerHTML = "";
    roles
      .filter(r => r.name.toLowerCase().includes(filter.toLowerCase()))
      .forEach(r => {
        const o = document.createElement('div');
        const isSel = cfg[cfgKey].includes(r.id);
        o.className = 'option' + (isSel ? ' selected' : '');
        o.textContent = r.name;
        o.onclick = () => {
          if (isSel) cfg[cfgKey] = cfg[cfgKey].filter(x => x !== r.id);
          else cfg[cfgKey] = [...cfg[cfgKey], r.id];
          renderChips(); renderOptions(search.value);
        };
        optsEl.appendChild(o);
      });
  }

  addBtn.onclick = (e) => { e.stopPropagation(); dd.hidden = !dd.hidden; renderOptions(search.value); };
  search.oninput = e => renderOptions(e.target.value);
  document.addEventListener('click', e => { if (!wrap.contains(e.target)) dd.hidden = true; });

  renderChips();
}

// ---------- Hierarchy sortable list ----------
function initHierarchy() {
  const list = document.getElementById('hierarchyList');
  const addBtn = document.getElementById('addHierarchyRole');

  function render() {
    list.innerHTML = "";
    cfg.hierarchy_role_ids.forEach((id, idx) => {
      const r = roles.find(x => x.id === id);
      if (!r) return;
      const li = document.createElement('li');
      li.draggable = true;
      li.dataset.idx = idx;
      li.innerHTML = `<span>≡ ${r.name}</span><span class="x" style="cursor:pointer;color:#b0b4c2">×</span>`;
      li.querySelector('.x').onclick = () => {
        cfg.hierarchy_role_ids.splice(idx, 1); render();
      };

      li.addEventListener('dragstart', e => {
        li.classList.add('dragging');
        e.dataTransfer.setData('text/plain', idx);
      });
      li.addEventListener('dragend', () => li.classList.remove('dragging'));
      li.addEventListener('dragover', e => e.preventDefault());
      li.addEventListener('drop', e => {
        e.preventDefault();
        const from = +e.dataTransfer.getData('text/plain');
        const to = +li.dataset.idx;
        const [m] = cfg.hierarchy_role_ids.splice(from, 1);
        cfg.hierarchy_role_ids.splice(to, 0, m);
        render();
      });
      list.appendChild(li);
    });
  }

  addBtn.onclick = () => {
    const available = roles.filter(r => !cfg.hierarchy_role_ids.includes(r.id));
    if (!available.length) return alert('Все роли уже добавлены');
    cfg.hierarchy_role_ids.push(available[0].id);
    render();
  };

  render();
}

// ---------- Toggles bind ----------
function bindToggles() {
  const keys = [
    'enabled','hierarchy_enabled','reserve_enabled','sort_enabled',
    'auto_ready','moderation','edits','respawn',
    'voice_create','voice_pick','remind_dm','remind_channel',
    'mvp','giveaway'
  ];
  keys.forEach(k => {
    const el = document.getElementById(k);
    if (!el) return;
    el.addEventListener('change', () => cfg[k] = el.checked);
  });
}

// ---------- Save ----------
document.getElementById('saveBtn').onclick = async () => {
  const res = await fetch(`/sbory/save?guild_id=${encodeURIComponent(guild_id)}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(cfg)
  });
  const j = await res.json();
  if (j.ok) {
    const btn = document.getElementById('saveBtn');
    const old = btn.textContent;
    btn.textContent = 'Сохранено ✓';
    setTimeout(() => btn.textContent = old, 1500);
  }
};

// init
initChannelSelect();
initRoleMultiselect('#creatorRoles', 'creator_role_ids');
initHierarchy();
bindToggles();
