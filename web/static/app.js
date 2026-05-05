/* ══════════════════════════════════════════════════════════════
   RECON OSINT — Web Frontend Logic
   SSE-powered real-time scan with card rendering
   ══════════════════════════════════════════════════════════════ */

let currentMode = 'username';
let currentScanId = null;
let eventSource = null;
let allResults = [];
let activeFilter = 'all';
let foundPlatformNames = new Set();

const PLACEHOLDERS = {
    username: 'Enter username to investigate...',
    email: 'Enter email address...',
    fullname: 'Enter full name...',
    merge: '',
};

// Platform icons map
const PLATFORM_ICONS = {
    'Instagram': '📸', 'Twitter / X': '𝕏', 'Facebook': '📘', 'TikTok': '🎵',
    'Snapchat': '👻', 'YouTube': '▶️', 'Twitch': '🟣', 'Reddit': '🤖',
    'LinkedIn': '💼', 'GitHub': '🐙', 'GitLab': '🦊', 'Discord': '💬',
    'Telegram': '✈️', 'Pinterest': '📌', 'Tumblr': '📝', 'Medium': '✍️',
    'Dev.to': '👩‍💻', 'Steam': '🎮', 'Spotify': '🎧', 'SoundCloud': '🔊',
    'Behance': '🎨', 'Dribbble': '🏀', 'Flickr': '📷', 'Vimeo': '🎬',
    'StackOverflow': '📚', 'Kaggle': '📊', 'HackerRank': '💻', 'LeetCode': '🧩',
    'Patreon': '🎁', 'Ko-fi': '☕', 'Etsy': '🛍️', 'eBay': '🛒',
    'Mastodon': '🐘', 'Threads': '🧵', 'Bluesky': '🦋', 'Keybase': '🔑',
    'Gravatar': '👤', 'Chess.com': '♟️', 'Duolingo': '🦉', 'Goodreads': '📖',
    'MyAnimeList': '🎌', 'Letterboxd': '🎞️', 'Kick': '🟢', 'Rumble': '📺',
    'Linktree': '🌳', 'About.me': '👋', 'Substack': '📰', 'WordPress': '📄',
    'DeviantArt': '🖼️', 'ArtStation': '🎨', '500px': '📸', 'Unsplash': '📷',
    'VK': '🔵', 'Quora': '❓', 'ProductHunt': '🚀', 'Pastebin': '📋',
    'HaveIBeenPwned': '🛡️', 'LeakCheck': '🛡️', 'Gravatar': '👤',
};

const PLATFORM_COLORS = {
    'Instagram': '#E4405F', 'Twitter / X': '#1DA1F2', 'Facebook': '#1877F2',
    'TikTok': '#ff0050', 'YouTube': '#FF0000', 'Twitch': '#9146FF',
    'Reddit': '#FF5700', 'LinkedIn': '#0A66C2', 'GitHub': '#6e5494',
    'Spotify': '#1DB954', 'Discord': '#5865F2', 'Pinterest': '#BD081C',
    'Steam': '#171a21', 'Telegram': '#26A5E4', 'Snapchat': '#FFFC00',
};

// ── Mode Switching ──────────────────────────────────────────

function setMode(mode) {
    currentMode = mode;
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
        let query = document.getElementById('searchInput').value.trim();
        if (!query) return;
        
        // If user pasted a full URL, try to extract the username
        if (currentMode === 'username' && query.startsWith('http')) {
            try {
                const u = new URL(query);
                const pathParts = u.pathname.split('/').filter(p => p.length > 0);
                if (pathParts.length > 0) {
                    query = pathParts[pathParts.length - 1]; // Take the last path segment as username
                }
            } catch (e) {}
        }

        if (currentMode === 'username') body.username = query;
        else if (currentMode === 'email') body.email = query;
        else if (currentMode === 'fullname') body.full_name = query;
    }
    resetUI();
    showScanning(true);
    try {
        const resp = await fetch('api/scan', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        const data = await resp.json();
        if (data.error) { logLine('error', data.error); showScanning(false); return; }
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
    try { await fetch(`api/scan/${currentScanId}/stop`, { method: 'POST' }); } catch (e) {}
    if (eventSource) { eventSource.close(); eventSource = null; }
    showScanning(false);
    logLine('warning', 'Scan stopped by user.');
}

// ── SSE Connection ──────────────────────────────────────────

function connectSSE(scanId) {
    eventSource = new EventSource(`api/scan/${scanId}/stream`);
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
        logLine('success', 'Scan complete.');
        eventSource.close();
        eventSource = null;
        currentScanId = null;
        // Show digital footprint dashboard
        buildFootprintDashboard();
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
    foundPlatformNames = new Set();
    document.getElementById('resultsGrid').innerHTML = '';
    document.getElementById('terminal').innerHTML = '';
    document.getElementById('statProfiles').textContent = '0';
    document.getElementById('statDocs').textContent = '0';
    document.getElementById('statMentions').textContent = '0';
    document.getElementById('statTotal').textContent = '0';
    document.getElementById('footprintDashboard').style.display = 'none';
    document.querySelectorAll('.progress-bar .fill').forEach(el => { el.style.width = '0%'; });
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
    if (bar) bar.style.width = `${value}%`;
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
    animateCounter('statProfiles', data.profiles);
    animateCounter('statDocs', data.documents);
    animateCounter('statMentions', data.mentions);
    animateCounter('statTotal', data.profiles + data.documents + data.mentions);
}

function animateCounter(id, target) {
    const el = document.getElementById(id);
    const current = parseInt(el.textContent) || 0;
    if (current === target) return;
    el.textContent = target;
    el.classList.add('stat-bump');
    setTimeout(() => el.classList.remove('stat-bump'), 300);
}

// ── Card Rendering ──────────────────────────────────────────

function addResultCard(result) {
    allResults.push(result);
    if (result.breach_data && result.platform === 'LeakCheck') {
        addBreachCard(result.breach_data);
        return;
    }
    const url = result.url || '';
    if (!url || !url.startsWith('http')) return;
    if (!result.exists) return;

    const platform = result.platform || result.source || 'Unknown';
    foundPlatformNames.add(platform);

    const card = createResultCard(result);
    document.getElementById('resultsGrid').appendChild(card);
    applyFilter();
}

function createResultCard(r) {
    const cat = r.category || 'mention';
    const platform = r.platform || r.source || 'Unknown';
    const icon = PLATFORM_ICONS[platform] || platform.charAt(0).toUpperCase();
    const color = PLATFORM_COLORS[platform] || 'var(--accent)';

    const card = document.createElement('div');
    card.className = 'result-card';
    card.dataset.category = cat;
    card.dataset.url = r.url || '';

    let avatarHTML = `<span class="platform-emoji">${icon}</span>`;
    if (r.profile_pic_b64) {
        avatarHTML = `<img src="data:image/jpeg;base64,${r.profile_pic_b64}" alt="" onerror="this.style.display='none';this.parentElement.innerHTML='<span class=\\'platform-emoji\\'>${icon}</span>'">`;
    } else if (r.profile_pic_url) {
        avatarHTML = `<img src="${escapeHtml(r.profile_pic_url)}" alt="" onerror="this.style.display='none';this.parentElement.innerHTML='<span class=\\'platform-emoji\\'>${icon}</span>'">`;
    }

    let metaHTML = '';
    if (r.followers) metaHTML += `<span class="meta-tag">👥 ${formatNumber(r.followers)}</span>`;
    if (r.is_verified) metaHTML += `<span class="meta-tag verified">✓ Verified</span>`;
    if (r.is_private) metaHTML += `<span class="meta-tag private">🔒 Private</span>`;

    let bioHTML = '';
    if (r.bio) bioHTML = `<div class="card-bio">${escapeHtml(r.bio.substring(0, 140))}</div>`;
    if (r.display_name && r.display_name !== platform)
        bioHTML = `<div class="card-displayname">${escapeHtml(r.display_name)}</div>` + bioHTML;

    const catLabel = cat === 'profile' ? 'PROFILE' : cat === 'document' ? 'DOCUMENT' : 'MENTION';
    const catClass = cat === 'profile' ? 'cat-profile' : cat === 'document' ? 'cat-document' : 'cat-mention';

    card.innerHTML = `
        <div class="card-accent" style="background:${color}"></div>
        <div class="card-header">
            <div class="card-avatar" style="border-color:${color}40">${avatarHTML}</div>
            <div class="card-info">
                <div class="card-platform">${escapeHtml(platform)}</div>
                <div class="card-url"><a href="${escapeHtml(r.url)}" target="_blank" rel="noopener">${escapeHtml(truncateUrl(r.url))}</a></div>
            </div>
            <span class="card-category ${catClass}">${catLabel}</span>
        </div>
        ${bioHTML}
        ${metaHTML ? `<div class="card-meta">${metaHTML}</div>` : ''}
        <div class="card-actions">
            <a href="${escapeHtml(r.url)}" target="_blank" rel="noopener">Open ↗</a>
        </div>
    `;
    return card;
}

function truncateUrl(url) {
    try {
        const u = new URL(url);
        return u.hostname + u.pathname.replace(/\/$/, '');
    } catch { return url; }
}

function formatNumber(n) {
    if (n >= 1000000) return (n / 1000000).toFixed(1) + 'M';
    if (n >= 1000) return (n / 1000).toFixed(1) + 'K';
    return String(n);
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
        if (sources.length > 15) sourcesHTML += `<p style="color:var(--text-muted);font-size:0.75rem;margin-top:6px;font-style:italic;">... and ${sources.length - 15} more</p>`;
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
        ${fieldsHTML}${sourcesHTML}
        <div class="breach-attr"><a href="https://leakcheck.io" target="_blank">Powered by LeakCheck</a></div>
    `;
    document.getElementById('resultsGrid').appendChild(card);
}

// ── Identity Card ───────────────────────────────────────────

function addIdentityCard(cluster) {
    const conf = cluster.confidence || 0;
    let confClass = conf >= 70 ? 'conf-high' : conf >= 40 ? 'conf-medium' : 'conf-low';
    let platformsHTML = '';
    (cluster.platforms || []).forEach(p => {
        const icon = PLATFORM_ICONS[p.platform] || '🔗';
        platformsHTML += `<a href="${escapeHtml(p.url)}" target="_blank" class="platform-chip">${icon} ${escapeHtml(p.platform)}</a>`;
    });

    const card = document.createElement('div');
    card.className = 'identity-card';
    card.innerHTML = `
        <div class="identity-header">
            <span style="font-size:1.4rem;">🔗</span>
            <h3>${escapeHtml(cluster.display_name || cluster.username || 'Unknown')}</h3>
            <span class="confidence-badge ${confClass}">${conf}% match</span>
        </div>
        ${cluster.bio ? `<p style="color:var(--text-secondary);font-size:0.85rem;margin-bottom:12px;">${escapeHtml(cluster.bio.substring(0, 150))}</p>` : ''}
        <div class="platform-list">${platformsHTML}</div>
    `;
    document.getElementById('resultsGrid').appendChild(card);
}

// ── Digital Footprint Dashboard ─────────────────────────────

function buildFootprintDashboard() {
    const dashboard = document.getElementById('footprintDashboard');
    const profiles = allResults.filter(r => r.exists && r.category === 'profile');
    const totalFound = profiles.length;

    if (totalFound === 0) return;

    dashboard.style.display = '';

    // Calculate exposure score (0-100)
    let score = 0;
    const hasSocial = ['Instagram', 'Twitter / X', 'Facebook', 'TikTok'].some(p => foundPlatformNames.has(p));
    const hasDev = ['GitHub', 'GitLab', 'StackOverflow'].some(p => foundPlatformNames.has(p));
    const hasGaming = ['Steam', 'Chess.com', 'Roblox'].some(p => foundPlatformNames.has(p));
    const hasBreach = allResults.some(r => r.breach_data && r.breach_data.total_breaches > 0);

    score += Math.min(totalFound * 5, 40); // Up to 40 pts for platforms found
    if (hasSocial) score += 15;
    if (hasDev) score += 10;
    if (hasGaming) score += 5;
    if (hasBreach) score += 25;
    score = Math.min(score, 100);

    // Animate score ring
    const circle = document.getElementById('scoreCircle');
    const circumference = 339.292;
    const offset = circumference - (score / 100) * circumference;
    setTimeout(() => { circle.style.strokeDashoffset = offset; }, 100);

    // Score color
    let scoreColor = '#00cc66';
    let grade = 'LOW EXPOSURE';
    if (score >= 75) { scoreColor = '#ff0033'; grade = 'HIGH EXPOSURE'; }
    else if (score >= 50) { scoreColor = '#ffaa00'; grade = 'MODERATE EXPOSURE'; }
    else if (score >= 25) { scoreColor = '#ff6633'; grade = 'MILD EXPOSURE'; }

    circle.style.stroke = scoreColor;
    document.getElementById('scoreValue').textContent = score;
    document.getElementById('scoreValue').style.color = scoreColor;
    document.getElementById('scoreGrade').textContent = grade;
    document.getElementById('scoreGrade').style.color = scoreColor;

    // Breakdown
    const breakdown = document.getElementById('scoreBreakdown');
    breakdown.innerHTML = `
        <div class="bd-item"><span>Platforms Found</span><strong>${totalFound}</strong></div>
        <div class="bd-item"><span>Social Media</span><strong>${hasSocial ? '✓' : '✗'}</strong></div>
        <div class="bd-item"><span>Developer Profiles</span><strong>${hasDev ? '✓' : '✗'}</strong></div>
        <div class="bd-item"><span>Data Breaches</span><strong style="color:${hasBreach ? '#ff0033' : '#00cc66'}">${hasBreach ? 'YES' : 'NONE'}</strong></div>
    `;

    // Risk items
    const riskDiv = document.getElementById('riskItems');
    let risks = [];
    if (hasSocial) risks.push({ level: 'medium', text: 'Social media presence detected — profile data may be publicly accessible' });
    if (hasBreach) risks.push({ level: 'high', text: 'Email found in data breaches — credentials may be compromised' });
    if (totalFound >= 10) risks.push({ level: 'high', text: `Found on ${totalFound} platforms — significant digital footprint` });
    else if (totalFound >= 5) risks.push({ level: 'medium', text: `Found on ${totalFound} platforms — moderate digital footprint` });
    else risks.push({ level: 'low', text: `Found on ${totalFound} platforms — minimal digital footprint` });
    if (foundPlatformNames.has('Pastebin')) risks.push({ level: 'high', text: 'Username found on Pastebin — possible data exposure' });

    riskDiv.innerHTML = risks.map(r => `
        <div class="risk-item risk-${r.level}">
            <span class="risk-dot"></span>
            <span>${r.text}</span>
        </div>
    `).join('');

    // Found platforms
    const platformsDiv = document.getElementById('foundPlatforms');
    platformsDiv.innerHTML = '';
    [...foundPlatformNames].sort().forEach(name => {
        const icon = PLATFORM_ICONS[name] || '🔗';
        const color = PLATFORM_COLORS[name] || 'var(--text-secondary)';
        platformsDiv.innerHTML += `<span class="found-chip" style="border-color:${color}40">${icon} ${escapeHtml(name)}</span>`;
    });
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
        if (activeFilter === 'all') card.style.display = '';
        else if (activeFilter === 'profiles') card.style.display = cat === 'profile' ? '' : 'none';
        else if (activeFilter === 'documents') card.style.display = cat === 'document' ? '' : 'none';
        else if (activeFilter === 'mentions') card.style.display = cat === 'mention' ? '' : 'none';
    });
    document.querySelectorAll('.breach-card, .identity-card').forEach(card => { card.style.display = ''; });
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
