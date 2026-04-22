/* ══════════════════════════════════════════════════════════════
   RECON OSINT — Web Frontend Logic
   SSE-powered real-time scan with card rendering
   ══════════════════════════════════════════════════════════════ */

let currentMode = 'username';
let currentScanId = null;
let eventSource = null;
let allResults = [];
let activeFilter = 'all';

const PLACEHOLDERS = {
    username: 'Enter username...',
    email: 'Enter email address...',
    fullname: 'Enter full name...',
    merge: '',
};

// ── Mode Switching ──────────────────────────────────────────

function setMode(mode) {
    currentMode = mode;

    // Update tabs
    document.querySelectorAll('.mode-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    const searchInput = document.getElementById('searchInput');
    const mergeInputs = document.getElementById('mergeInputs');

    if (mode === 'merge') {
        searchInput.style.display = 'none';
        mergeInputs.classList.add('visible');
    } else {
        searchInput.style.display = '';
        mergeInputs.classList.remove('visible');
        searchInput.placeholder = PLACEHOLDERS[mode];
        searchInput.value = '';
    }
}

// ── Start Scan ──────────────────────────────────────────────

async function startScan() {
    let body = { deep: document.getElementById('deepCheck').checked };

    if (currentMode === 'merge') {
        body.username = document.getElementById('mergeUser').value.trim();
        body.email = document.getElementById('mergeEmail').value.trim();
        body.full_name = document.getElementById('mergeName').value.trim();
        if (!body.username && !body.email && !body.full_name) return;
    } else {
        const query = document.getElementById('searchInput').value.trim();
        if (!query) return;
        if (currentMode === 'username') body.username = query;
        else if (currentMode === 'email') body.email = query;
        else if (currentMode === 'fullname') body.full_name = query;
    }

    // Reset UI
    resetUI();
    showScanning(true);

    try {
        const resp = await fetch('/api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await resp.json();
        if (data.error) {
            logLine('error', data.error);
            showScanning(false);
            return;
        }
        currentScanId = data.scan_id;
        connectSSE(data.scan_id);
    } catch (e) {
        logLine('error', `Failed to start scan: ${e.message}`);
        showScanning(false);
    }
}

// ── Stop Scan ───────────────────────────────────────────────

async function stopScan() {
    if (!currentScanId) return;
    try {
        await fetch(`/api/scan/${currentScanId}/stop`, { method: 'POST' });
    } catch (e) { /* ignore */ }
    if (eventSource) {
        eventSource.close();
        eventSource = null;
    }
    showScanning(false);
    logLine('warning', 'Scan stopped by user.');
}

// ── SSE Connection ──────────────────────────────────────────

function connectSSE(scanId) {
    eventSource = new EventSource(`/api/scan/${scanId}/stream`);

    eventSource.addEventListener('log', (e) => {
        const data = JSON.parse(e.data);
        logLine(data.level, data.message);
    });

    eventSource.addEventListener('progress', (e) => {
        const data = JSON.parse(e.data);
        updateProgress(data.module, data.value);
    });

    eventSource.addEventListener('result', (e) => {
        const data = JSON.parse(e.data);
        addResultCard(data);
    });

    eventSource.addEventListener('enriched', (e) => {
        const data = JSON.parse(e.data);
        updateEnrichedCard(data);
    });

    eventSource.addEventListener('stats', (e) => {
        const data = JSON.parse(e.data);
        updateStats(data);
    });

    eventSource.addEventListener('correlation', (e) => {
        const data = JSON.parse(e.data);
        if (data.clusters) {
            data.clusters.forEach(cluster => addIdentityCard(cluster));
        }
    });

    eventSource.addEventListener('done', (e) => {
        showScanning(false);
        logLine('success', '━'.repeat(40));
        logLine('success', 'Scan stream closed.');
        eventSource.close();
        eventSource = null;
        currentScanId = null;
    });

    eventSource.onerror = () => {
        showScanning(false);
        eventSource.close();
        eventSource = null;
    };
}

// ── UI Helpers ──────────────────────────────────────────────

function resetUI() {
    allResults = [];
    activeFilter = 'all';
    document.getElementById('resultsGrid').innerHTML = '';
    document.getElementById('terminal').innerHTML = '';
    document.getElementById('statProfiles').textContent = '0';
    document.getElementById('statDocs').textContent = '0';
    document.getElementById('statMentions').textContent = '0';
    document.getElementById('statTotal').textContent = '0';

    // Reset progress bars
    document.querySelectorAll('.progress-bar .fill').forEach(el => {
        el.style.width = '0%';
    });
}

function showScanning(active) {
    const searchBtn = document.getElementById('searchBtn');
    const stopBtn = document.getElementById('stopBtn');
    const progress = document.getElementById('progressSection');
    const terminal = document.getElementById('terminal');
    const header = document.getElementById('resultsHeader');

    if (active) {
        searchBtn.classList.add('hidden');
        stopBtn.classList.add('visible');
        progress.style.display = '';
        terminal.style.display = '';
        header.style.display = '';
        document.getElementById('emptyState')?.remove();
    } else {
        searchBtn.classList.remove('hidden');
        stopBtn.classList.remove('visible');
    }
}

function logLine(level, message) {
    const terminal = document.getElementById('terminal');
    const line = document.createElement('div');
    line.className = `log-line ${level}`;
    line.textContent = message;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

function updateProgress(module, value) {
    const bar = document.getElementById(`prog-${module}`);
    if (bar) {
        bar.style.width = `${value}%`;
    }
    // Update overall as average
    const bars = document.querySelectorAll('.progress-bar .fill');
    let total = 0, count = 0;
    bars.forEach(b => {
        if (b.id !== 'progressOverall') {
            const w = parseFloat(b.style.width) || 0;
            if (w > 0) { total += w; count++; }
        }
    });
    const overall = count > 0 ? total / count : 0;
    document.getElementById('progressOverall').style.width = `${overall}%`;
}

function updateStats(data) {
    document.getElementById('statProfiles').textContent = data.profiles;
    document.getElementById('statDocs').textContent = data.documents;
    document.getElementById('statMentions').textContent = data.mentions;
    document.getElementById('statTotal').textContent = data.profiles + data.documents + data.mentions;
}

// ── Card Rendering ──────────────────────────────────────────

function addResultCard(result) {
    allResults.push(result);

    // Check for breach data
    if (result.breach_data && result.platform === 'LeakCheck') {
        addBreachCard(result.breach_data);
        return;
    }

    const url = result.url || '';
    if (!url || !url.startsWith('http')) return;
    if (!result.exists) return;

    const card = createResultCard(result);
    const grid = document.getElementById('resultsGrid');
    grid.appendChild(card);

    applyFilter();
}

function createResultCard(r) {
    const cat = r.category || 'mention';
    const catClass = cat === 'profile' ? 'cat-profile' : cat === 'document' ? 'cat-document' : 'cat-mention';
    const platform = r.platform || r.source || 'Unknown';
    const initial = platform.charAt(0).toUpperCase();

    const card = document.createElement('div');
    card.className = 'result-card';
    card.dataset.category = cat;
    card.dataset.url = r.url || '';

    let avatarHTML = `<span>${initial}</span>`;
    if (r.profile_pic_url) {
        avatarHTML = `<img src="${escapeHtml(r.profile_pic_url)}" alt="">`;
    }

    let bioHTML = '';
    if (r.bio) {
        bioHTML = `<div class="card-bio">${escapeHtml(r.bio.substring(0, 120))}</div>`;
    }

    card.innerHTML = `
        <div class="card-header">
            <div class="card-avatar">${avatarHTML}</div>
            <div class="card-info">
                <div class="card-platform">${escapeHtml(platform)}</div>
                <div class="card-url"><a href="${escapeHtml(r.url)}" target="_blank">${escapeHtml(r.url)}</a></div>
            </div>
            <span class="card-category ${catClass}">${cat}</span>
        </div>
        ${bioHTML}
        <div class="card-actions">
            <a href="${escapeHtml(r.url)}" target="_blank">Open ↗</a>
        </div>
    `;

    return card;
}

function updateEnrichedCard(result) {
    const url = result.url || '';
    const existing = document.querySelector(`.result-card[data-url="${CSS.escape(url)}"]`);
    if (existing) {
        const newCard = createResultCard(result);
        existing.replaceWith(newCard);
    }
}

// ── Breach Card ─────────────────────────────────────────────

function addBreachCard(bd) {
    const total = bd.total_breaches || 0;
    let accentColor, severity, sevClass;
    if (total >= 100) { accentColor = '#ff0033'; severity = 'CRITICAL'; sevClass = 'sev-critical'; }
    else if (total >= 10) { accentColor = '#ffaa00'; severity = 'HIGH'; sevClass = 'sev-high'; }
    else if (total > 0) { accentColor = '#ff6633'; severity = 'MODERATE'; sevClass = 'sev-moderate'; }
    else { accentColor = '#00cc66'; severity = 'CLEAN'; sevClass = 'sev-clean'; }

    const fields = bd.fields_exposed || [];
    const dangerFields = ['password', 'ssn', 'phone', 'address', 'dob', 'ip'];

    let fieldsHTML = '';
    if (fields.length > 0) {
        fieldsHTML = `<div class="exposed-fields"><span class="exposed-label">EXPOSED:</span>`;
        fields.slice(0, 12).forEach(f => {
            const isDanger = dangerFields.includes(f.toLowerCase());
            fieldsHTML += `<span class="field-tag ${isDanger ? 'field-danger' : 'field-normal'}">${escapeHtml(f.toUpperCase())}</span>`;
        });
        if (fields.length > 12) fieldsHTML += `<span class="field-tag field-normal">+${fields.length - 12}</span>`;
        fieldsHTML += '</div>';
    }

    const sources = bd.sources || [];
    let sourcesHTML = '';
    if (sources.length > 0) {
        sourcesHTML = `<div class="breach-sources"><h4>BREACH SOURCES (${sources.length})</h4><div class="sources-grid">`;
        sources.slice(0, 15).forEach(s => {
            sourcesHTML += `<span class="source-name">● ${escapeHtml(s.name || 'Unknown')}</span>`;
            sourcesHTML += `<span class="source-date">${escapeHtml(s.date || '')}</span>`;
        });
        sourcesHTML += '</div>';
        if (sources.length > 15) {
            sourcesHTML += `<p style="color:var(--text-muted);font-size:0.75rem;margin-top:6px;font-style:italic;">... and ${sources.length - 15} more sources</p>`;
        }
        sourcesHTML += '</div>';
    }

    const card = document.createElement('div');
    card.className = 'breach-card';
    card.style.borderTopColor = accentColor;
    card.style.borderColor = accentColor + '44';
    card.innerHTML = `
        <div class="breach-header">
            <span class="icon">🛡</span>
            <h3 style="color:${accentColor}">BREACH INTELLIGENCE</h3>
            <span class="severity-badge ${sevClass}">${severity}</span>
        </div>
        <div class="breach-stats">
            <span class="email">📧 ${escapeHtml(bd.email || '')}</span>
            <span class="count" style="color:${accentColor}">⚠ ${total} breaches</span>
            <span style="color:var(--text-muted)">📁 ${bd.total_sources || 0} sources</span>
        </div>
        <div class="breach-sep"></div>
        ${fieldsHTML}
        ${sourcesHTML}
        <div class="breach-attr">
            <a href="https://leakcheck.io" target="_blank">Powered by LeakCheck</a>
        </div>
    `;

    document.getElementById('resultsGrid').appendChild(card);
}

// ── Identity Card ───────────────────────────────────────────

function addIdentityCard(cluster) {
    const conf = cluster.confidence || 0;
    let confClass = conf >= 70 ? 'conf-high' : conf >= 40 ? 'conf-medium' : 'conf-low';

    let platformsHTML = '';
    (cluster.platforms || []).forEach(p => {
        platformsHTML += `<a href="${escapeHtml(p.url)}" target="_blank" class="platform-chip">${escapeHtml(p.platform)}</a>`;
    });

    const card = document.createElement('div');
    card.className = 'identity-card';
    card.innerHTML = `
        <div class="identity-header">
            <span style="font-size:1.4rem;">👤</span>
            <h3>${escapeHtml(cluster.display_name || cluster.username || 'Unknown')}</h3>
            <span class="confidence-badge ${confClass}">${conf}% confidence</span>
        </div>
        ${cluster.bio ? `<p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:12px;">${escapeHtml(cluster.bio.substring(0, 150))}</p>` : ''}
        <div class="platform-list">${platformsHTML}</div>
    `;

    document.getElementById('resultsGrid').appendChild(card);
}

// ── Results Filtering ───────────────────────────────────────

function filterResults(filter) {
    activeFilter = filter;
    document.querySelectorAll('.results-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === filter);
    });
    applyFilter();
}

function applyFilter() {
    document.querySelectorAll('.result-card').forEach(card => {
        const cat = card.dataset.category;
        if (activeFilter === 'all') {
            card.style.display = '';
        } else if (activeFilter === 'profiles') {
            card.style.display = cat === 'profile' ? '' : 'none';
        } else if (activeFilter === 'documents') {
            card.style.display = cat === 'document' ? '' : 'none';
        } else if (activeFilter === 'mentions') {
            card.style.display = cat === 'mention' ? '' : 'none';
        }
    });

    // Always show breach and identity cards
    document.querySelectorAll('.breach-card, .identity-card').forEach(card => {
        card.style.display = '';
    });
}

// ── Export / Copy ────────────────────────────────────────────

function exportResults() {
    if (allResults.length === 0) return;
    const blob = new Blob([JSON.stringify(allResults, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `recon_results_${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
}

function copyUrls() {
    const urls = allResults
        .filter(r => r.url && r.url.startsWith('http') && r.exists)
        .map(r => r.url);
    if (urls.length === 0) return;
    navigator.clipboard.writeText(urls.join('\n'))
        .then(() => logLine('success', `Copied ${urls.length} URLs to clipboard`))
        .catch(() => logLine('error', 'Failed to copy to clipboard'));
}

// ── Utilities ────────────────────────────────────────────────

function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

// ── Keyboard shortcut ────────────────────────────────────────

document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        const active = document.activeElement;
        if (active && (active.id === 'searchInput' || active.closest('.merge-inputs'))) {
            startScan();
        }
    }
});
