"""
rebuild_archive.py
------------------
Strips the baked-in film data from belcourt_archive.html and rewires it to
load from belcourtfilms.json (or any compatible project JSON) via a file-picker
loading screen, matching the pattern used in belcourt_enrichment-updated.html.

Usage:
  python3 rebuild_archive.py
Produces: belcourt_archive_updated.html
"""

import os

SRC  = os.path.join(os.path.dirname(__file__), 'belcourt_archive.html')
DEST = os.path.join(os.path.dirname(__file__), 'belcourt_archive_updated.html')

with open(SRC, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# --------------------------------------------------------------------------
# Loading screen HTML (inserted right after <body>)
# --------------------------------------------------------------------------
LOAD_SCREEN = '''\
<div id="load-screen" style="
  position:fixed;inset:0;background:#0f1117;z-index:9999;
  display:flex;align-items:center;justify-content:center;
">
  <div style="text-align:center;max-width:420px;padding:2rem;">
    <div style="font-family:'Playfair Display',serif;font-size:28px;font-weight:400;color:#e8eaf0;margin-bottom:0.5rem;">
      The Belcourt Theatre
    </div>
    <div style="font-size:11px;letter-spacing:0.2em;text-transform:uppercase;color:#4a8fe8;margin-bottom:2.5rem;">
      Film Archive
    </div>
    <p style="font-size:13px;color:#6b7590;margin-bottom:1.75rem;line-height:1.6;">
      Load your project file to browse the archive.<br>
      Works with any <code style="font-size:11px;background:#1a1d27;padding:2px 6px;border-radius:3px;color:#93baf5;">belcourtfilms.json</code> or compatible project file.
    </p>
    <label style="
      display:inline-block;padding:10px 28px;
      background:#4a8fe8;color:#fff;border-radius:4px;
      font-family:'DM Sans',sans-serif;font-size:13px;font-weight:500;
      cursor:pointer;transition:background 0.15s;
    " onmouseover="this.style.background='#2d6abf'" onmouseout="this.style.background='#4a8fe8'">
      Load database
      <input type="file" accept=".json" style="display:none" onchange="loadDatabase(this)">
    </label>
    <div id="load-error" style="font-size:12px;color:#e05c5c;margin-top:1rem;display:none;"></div>
  </div>
</div>
'''

# --------------------------------------------------------------------------
# New JS block that replaces the baked-in data and init IIFEs
# --------------------------------------------------------------------------
NEW_JS = '''\
let ALL = [];
let IMDB_TITLES = {};

let filtered = [], page = 1, sortKey = 'o', sortDir = -1;
const PER = 50;
let statsRendered = false;

function loadDatabase(input) {
  const file = input.files[0];
  if (!file) return;
  const err = document.getElementById('load-error');
  err.style.display = 'none';
  const reader = new FileReader();
  reader.onload = function(e) {
    try {
      const data = JSON.parse(e.target.result);

      // Accept project file (version 3) or a bare array
      if (data && data.films && Array.isArray(data.films)) {
        ALL = data.films;
        // Also merge legacy customFilms if present
        if (data.customFilms && data.customFilms.length) {
          ALL = ALL.concat(data.customFilms);
        }
        // Build IMDB_TITLES from preloadedResults + results
        IMDB_TITLES = {};
        const mergedResults = Object.assign({}, data.preloadedResults || {}, data.results || {});
        Object.entries(mergedResults).forEach(function(entry) {
          const id = entry[0], r = entry[1];
          if (r && r.imdbData && r.imdbData.title) IMDB_TITLES[id] = r.imdbData.title;
        });
      } else if (Array.isArray(data)) {
        ALL = data;
      } else {
        throw new Error('Unrecognised file format.');
      }

      if (!ALL.length) throw new Error('No films found in the file.');

      // Merge any locally-saved confirmed titles (legacy enrichment localStorage)
      try {
        const raw = localStorage.getItem('belcourt_enrichment_v1');
        if (raw) {
          const local = JSON.parse(raw);
          Object.entries(local).forEach(function(entry) {
            const id = entry[0], r = entry[1];
            if (r && r.imdbData && r.imdbData.title) IMDB_TITLES[id] = r.imdbData.title;
          });
        }
      } catch(ex) {}

      init();
      document.getElementById('load-screen').style.display = 'none';
    } catch(ex) {
      err.textContent = 'Could not load file: ' + ex.message;
      err.style.display = 'block';
    }
  };
  reader.readAsText(file);
}

function displayTitle(f) {
  return IMDB_TITLES[String(f.id)] || f.t || '\\u2014';
}

function init() {
  // Reset dropdown options (keep the first "All …" option)
  ['fYear','fDecade','fCat','fVenue'].forEach(function(id) {
    const el = document.getElementById(id);
    while (el.options.length > 1) el.remove(1);
  });

  const years = [...new Set(ALL.map(function(f){return f.y;}).filter(Boolean))].sort(function(a,b){return b-a;});
  const fy = document.getElementById('fYear');
  years.forEach(function(y) { const o=document.createElement('option'); o.value=y; o.textContent=y; fy.appendChild(o); });

  const decades = [...new Set(ALL.map(function(f){return f.y?Math.floor(f.y/10)*10:null;}).filter(Boolean))].sort(function(a,b){return b-a;});
  const fd = document.getElementById('fDecade');
  decades.forEach(function(d) { const o=document.createElement('option'); o.value=d; o.textContent=d+'s'; fd.appendChild(o); });

  const cats = [...new Set(ALL.map(function(f){return f.cat;}).filter(Boolean))].sort();
  const fc = document.getElementById('fCat');
  cats.forEach(function(c) { const o=document.createElement('option'); o.value=c; o.textContent=c; fc.appendChild(o); });

  const venues = [...new Set(ALL.map(function(f){return f.co;}).filter(Boolean))].sort();
  const fv = document.getElementById('fVenue');
  venues.forEach(function(v) { const o=document.createElement('option'); o.value=v; o.textContent=v; fv.appendChild(o); });

  // Header stats
  const withRun = ALL.filter(function(f){return f.r&&f.r<400;});
  const avg = Math.round(withRun.reduce(function(s,f){return s+f.r;},0)/withRun.length);
  const longest = [...withRun].sort(function(a,b){return b.r-a.r;})[0];
  document.getElementById('hdr-total').textContent = ALL.length.toLocaleString();
  document.getElementById('hdr-longest').textContent = longest.r;
  document.getElementById('hdr-avg').textContent = avg;

  // Reset charts if stats were previously rendered
  statsRendered = false;

  onFilter();
}

'''

# --------------------------------------------------------------------------
# Build the new file line by line
# --------------------------------------------------------------------------
out = []
i = 0
while i < len(lines):
    line = lines[i]
    stripped = line.strip()

    # After <body>, inject the loading screen
    if stripped == '<body>':
        out.append(line)
        out.append(LOAD_SCREEN)
        i += 1
        continue

    # Update the hardcoded "7,243" total films stat to use a dynamic id
    if 'stat-num">7,243</div>' in line:
        line = line.replace('>7,243<', ' id="hdr-total">—<')
        out.append(line)
        i += 1
        continue

    # Line 225: const ALL = [...] — replace with new JS block
    if stripped.startswith('const ALL = ['):
        out.append(NEW_JS)
        i += 1  # skip the data line
        # Line 226 is blank — skip it
        if i < len(lines) and lines[i].strip() == '':
            i += 1
        # Line 227: let filtered = [...ALL], ... — already in NEW_JS, skip
        if i < len(lines) and lines[i].strip().startswith('let filtered ='):
            i += 1
        # Line 228: const PER = 50; — already in NEW_JS, skip
        if i < len(lines) and lines[i].strip().startswith('const PER ='):
            i += 1
        # Line 229: let statsRendered — already in NEW_JS, skip
        if i < len(lines) and lines[i].strip().startswith('let statsRendered'):
            i += 1
        continue

    # Line 231-232: comments about IMDB_TITLES — skip
    if '// IMDb title lookup' in stripped or '// Also layers in' in stripped:
        i += 1
        continue

    # Line 233: const IMDB_TITLES = {...} — skip (handled in NEW_JS / loadDatabase)
    if stripped.startswith('const IMDB_TITLES ='):
        i += 1
        continue

    # Lines 234-244: IIFE for localStorage enrichment — skip (handled in loadDatabase)
    if stripped.startswith('(function()') and i < 250:
        # skip until the closing })();
        while i < len(lines) and lines[i].strip() != '})();':
            i += 1
        i += 1  # skip the })(); line
        continue

    # Line 246-248: function displayTitle — skip (in NEW_JS)
    if stripped.startswith('function displayTitle('):
        while i < len(lines) and lines[i].strip() != '}':
            i += 1
        i += 1  # skip closing }
        continue

    # Line 250: '// Init dropdowns' comment — skip
    if stripped == '// Init dropdowns':
        i += 1
        continue

    # Lines 251-274: dropdown/stats IIFE — skip (now in init())
    if stripped.startswith('(function()') and i >= 250:
        while i < len(lines) and lines[i].strip() != '})();':
            i += 1
        i += 1  # skip })();
        continue

    # Line 545: onFilter(); bare call — skip (called inside init())
    if stripped == 'onFilter();' and i > 500:
        i += 1
        continue

    out.append(line)
    i += 1

with open(DEST, 'w', encoding='utf-8') as f:
    f.writelines(out)

size_kb = os.path.getsize(DEST) / 1024
print('Written: %s (%.1f KB)' % (DEST, size_kb))
