"""
RECON OSINT — Blog Articles Data
12 placeholder articles for the blog system.
"""

ARTICLES = [
    {
        "slug": "what-is-osint",
        "title": "What is OSINT? A Beginner's Guide to Open Source Intelligence",
        "excerpt": "Learn what Open Source Intelligence (OSINT) is, how it works, and why it matters for your online security.",
        "category": "OSINT",
        "tag_class": "tag-osint",
        "author": "RECON Team",
        "date": "2026-04-28",
        "read_time": "6 min read",
        "content": """
<h2>What is OSINT?</h2>
<p>Open Source Intelligence (OSINT) refers to the collection and analysis of information gathered from publicly available sources. This includes social media profiles, public records, websites, forums, and any other data that can be accessed without special authorization.</p>
<p>OSINT has become a critical tool in cybersecurity, journalism, law enforcement, and corporate security. With the explosion of digital data, understanding what information is publicly available about you — your <strong>digital footprint</strong> — has never been more important.</p>

<h2>How Does OSINT Work?</h2>
<p>OSINT practitioners use a combination of manual research and automated tools to gather data. The process typically involves:</p>
<ul>
<li><strong>Username enumeration</strong> — Checking if a username exists across hundreds of platforms</li>
<li><strong>Email investigation</strong> — Discovering accounts linked to an email address</li>
<li><strong>Data breach analysis</strong> — Checking if credentials have been exposed in known breaches</li>
<li><strong>Social media profiling</strong> — Analyzing public profiles for personal information</li>
<li><strong>Google dorking</strong> — Using advanced search operators to find hidden information</li>
</ul>

<h2>Why Should You Care?</h2>
<p>Every time you create an account, post a comment, or share a photo online, you're adding to your digital footprint. Attackers can use this information for social engineering, identity theft, or targeted phishing attacks.</p>
<p>By understanding OSINT, you can take proactive steps to minimize your exposure and protect your privacy.</p>

<h3>Try It Yourself</h3>
<p>Want to see what the internet knows about you? Use our <a href="/tool">RECON OSINT Scanner</a> to scan your username across 120+ platforms and check for data breaches.</p>
"""
    },
    {
        "slug": "check-email-breached",
        "title": "How to Check if Your Email Has Been Breached",
        "excerpt": "Your email might be in a data breach right now. Here's how to find out and what to do about it.",
        "category": "Security",
        "tag_class": "tag-security",
        "author": "RECON Team",
        "date": "2026-04-25",
        "read_time": "5 min read",
        "content": """
<h2>The Growing Threat of Data Breaches</h2>
<p>Data breaches have become alarmingly common. In 2025 alone, over 3 billion records were exposed in major breaches. Your email address is often the key identifier that links you across multiple breached databases.</p>

<h2>How to Check Your Email</h2>
<p>There are several ways to check if your email has been compromised:</p>
<ul>
<li><strong>RECON Email Scanner</strong> — Our tool checks your email against multiple breach databases and identifies linked accounts across 55+ platforms</li>
<li><strong>Have I Been Pwned</strong> — A free service by Troy Hunt that checks known breaches</li>
<li><strong>LeakCheck</strong> — A comprehensive breach detection service</li>
</ul>

<h2>What to Do If You've Been Breached</h2>
<ol>
<li><strong>Change your passwords immediately</strong> — Start with the most critical accounts (email, banking)</li>
<li><strong>Enable two-factor authentication (2FA)</strong> — This adds an extra layer of security</li>
<li><strong>Check for unauthorized access</strong> — Review recent login activity on your accounts</li>
<li><strong>Use unique passwords</strong> — Never reuse passwords across different services</li>
<li><strong>Consider a password manager</strong> — Tools like Bitwarden or 1Password generate and store unique passwords</li>
</ol>

<p>Don't wait until it's too late. <a href="/tool">Scan your email now</a> to find out if you've been breached.</p>
"""
    },
    {
        "slug": "reduce-digital-footprint",
        "title": "10 Ways to Reduce Your Digital Footprint",
        "excerpt": "Practical steps you can take today to minimize your online presence and protect your privacy.",
        "category": "Privacy",
        "tag_class": "tag-privacy",
        "author": "RECON Team",
        "date": "2026-04-22",
        "read_time": "7 min read",
        "content": """
<h2>Why Reduce Your Digital Footprint?</h2>
<p>Your digital footprint is the trail of data you leave behind when you use the internet. The larger your footprint, the more vulnerable you are to identity theft, doxxing, and social engineering attacks.</p>

<h2>10 Actionable Steps</h2>
<h3>1. Audit Your Online Accounts</h3>
<p>Use an OSINT tool like <a href="/tool">RECON</a> to discover all the accounts linked to your username or email. You might be surprised by how many forgotten accounts exist.</p>

<h3>2. Delete Unused Accounts</h3>
<p>Visit each platform you no longer use and delete or deactivate your account. Services like JustDeleteMe can guide you through the process.</p>

<h3>3. Use Unique Usernames</h3>
<p>Using the same username everywhere makes it trivial to link your accounts together. Consider using different handles for different contexts.</p>

<h3>4. Review Privacy Settings</h3>
<p>Go through the privacy settings on every active account. Set profiles to private where possible and limit what information is publicly visible.</p>

<h3>5. Use a VPN</h3>
<p>A VPN masks your IP address and encrypts your traffic, making it harder to track your online activity.</p>

<h3>6. Opt Out of Data Brokers</h3>
<p>Data brokers collect and sell your personal information. Services like DeleteMe can help you opt out of major brokers.</p>

<h3>7. Use Privacy-Focused Tools</h3>
<p>Switch to privacy-respecting alternatives: DuckDuckGo for search, Signal for messaging, ProtonMail for email.</p>

<h3>8. Be Careful with Photos</h3>
<p>Photos contain metadata (EXIF data) that can reveal your location, device, and more. Strip metadata before sharing.</p>

<h3>9. Limit Social Media Sharing</h3>
<p>Think before you post. Every piece of information you share publicly can be collected and used against you.</p>

<h3>10. Monitor Regularly</h3>
<p>Your digital footprint is always growing. Make it a habit to regularly audit your online presence using tools like RECON.</p>
"""
    },
    {
        "slug": "username-opsec",
        "title": "Username OPSEC: Why Using the Same Handle Everywhere is Dangerous",
        "excerpt": "Using the same username across platforms makes you easy to track. Learn why OPSEC matters.",
        "category": "OPSEC",
        "tag_class": "tag-opsec",
        "author": "RECON Team",
        "date": "2026-04-19",
        "read_time": "5 min read",
        "content": """
<h2>The Username Problem</h2>
<p>Most people use the same username across multiple platforms. It's convenient, memorable, and makes it easy for friends to find you. But it also makes it incredibly easy for anyone — including malicious actors — to build a complete profile of your online presence.</p>

<h2>How Username Correlation Works</h2>
<p>OSINT tools like <a href="/tool">RECON</a> can check a single username against 120+ platforms in seconds. If your username matches on Instagram, GitHub, Reddit, and Steam, an investigator now knows your interests, your code, your opinions, and your gaming habits.</p>

<h2>Real-World Risks</h2>
<ul>
<li><strong>Doxxing</strong> — Correlating accounts can reveal your real identity</li>
<li><strong>Social engineering</strong> — Attackers use personal details from one platform to manipulate you on another</li>
<li><strong>Targeted phishing</strong> — Knowing your interests makes phishing emails more convincing</li>
<li><strong>Stalking</strong> — A single username can expose your entire online life</li>
</ul>

<h2>Best Practices for Username OPSEC</h2>
<ul>
<li>Use different usernames for personal, professional, and anonymous activities</li>
<li>Avoid using your real name or birth year in usernames</li>
<li>Consider using randomly generated handles for sensitive accounts</li>
<li>Regularly audit your username across platforms with OSINT tools</li>
</ul>
"""
    },
    {
        "slug": "understanding-data-breaches",
        "title": "Understanding Data Breaches: What Happens to Your Data",
        "excerpt": "When a company gets breached, your data enters a shadowy marketplace. Here's what happens next.",
        "category": "Security",
        "tag_class": "tag-security",
        "author": "RECON Team",
        "date": "2026-04-16",
        "read_time": "6 min read",
        "content": """
<h2>Anatomy of a Data Breach</h2>
<p>A data breach occurs when unauthorized individuals gain access to sensitive data. This can happen through hacking, insider threats, misconfigured databases, or phishing attacks.</p>

<h2>The Lifecycle of Breached Data</h2>
<h3>Stage 1: Initial Breach</h3>
<p>Attackers exploit a vulnerability to access a company's database. This could be an SQL injection, compromised credentials, or a zero-day exploit.</p>

<h3>Stage 2: Data Exfiltration</h3>
<p>The stolen data — which can include emails, passwords, phone numbers, addresses, and even financial information — is downloaded and organized.</p>

<h3>Stage 3: Underground Trading</h3>
<p>Breached databases are sold on dark web marketplaces and hacking forums. Prices depend on the data's freshness and sensitivity.</p>

<h3>Stage 4: Credential Stuffing</h3>
<p>Attackers use stolen email/password combinations to try logging into other services, exploiting the fact that most people reuse passwords.</p>

<h2>What Data Gets Exposed?</h2>
<ul>
<li><strong>Emails and passwords</strong> — The most common and most dangerous</li>
<li><strong>Phone numbers</strong> — Used for SIM swapping attacks</li>
<li><strong>IP addresses</strong> — Can reveal approximate location</li>
<li><strong>Personal details</strong> — Names, dates of birth, addresses</li>
</ul>

<p>Check if your data has been exposed using our <a href="/tool">breach detection tool</a>.</p>
"""
    },
    {
        "slug": "social-engineering-osint",
        "title": "How Hackers Use Social Engineering to Find You Online",
        "excerpt": "Social engineering combined with OSINT is a powerful attack vector. Learn how to defend yourself.",
        "category": "Threats",
        "tag_class": "tag-threats",
        "author": "RECON Team",
        "date": "2026-04-13",
        "read_time": "6 min read",
        "content": """
<h2>What is Social Engineering?</h2>
<p>Social engineering is the art of manipulating people into divulging confidential information. Unlike traditional hacking, it exploits human psychology rather than technical vulnerabilities.</p>

<h2>OSINT + Social Engineering</h2>
<p>Before launching a social engineering attack, threat actors use OSINT to research their targets. The more they know about you, the more convincing their approach.</p>

<h3>Common Attack Scenarios</h3>
<ul>
<li><strong>Spear phishing</strong> — Personalized emails referencing your real interests, job, or recent activities</li>
<li><strong>Pretexting</strong> — Calling your bank while pretending to be you, using details found online</li>
<li><strong>Baiting</strong> — Leaving infected USB drives in locations you frequent</li>
<li><strong>Vishing</strong> — Phone calls using information from your social media profiles</li>
</ul>

<h2>How to Protect Yourself</h2>
<ul>
<li>Minimize the personal information you share publicly</li>
<li>Be skeptical of unsolicited contacts, even if they seem to know you</li>
<li>Verify requests through official channels before taking action</li>
<li>Use our <a href="/tool">RECON tool</a> to see what attackers can find about you</li>
</ul>
"""
    },
    {
        "slug": "email-security-guide-2026",
        "title": "The Complete Guide to Email Security in 2026",
        "excerpt": "Email remains the #1 attack vector. Here's everything you need to know to secure your inbox.",
        "category": "Security",
        "tag_class": "tag-security",
        "author": "RECON Team",
        "date": "2026-04-10",
        "read_time": "8 min read",
        "content": """
<h2>Why Email Security Matters</h2>
<p>Over 90% of cyberattacks begin with a phishing email. Your email is the gateway to your digital life — it's used for account recovery, two-factor authentication, and communication with banks, employers, and government agencies.</p>

<h2>Essential Email Security Practices</h2>

<h3>1. Use Strong, Unique Passwords</h3>
<p>Your email password should be at least 16 characters long and completely unique. Use a password manager to generate and store it.</p>

<h3>2. Enable Two-Factor Authentication</h3>
<p>Use an authenticator app (not SMS) for 2FA. Hardware keys like YubiKey offer the strongest protection.</p>

<h3>3. Be Wary of Phishing</h3>
<p>Always check the sender's actual email address, hover over links before clicking, and never open unexpected attachments.</p>

<h3>4. Use Email Aliases</h3>
<p>Services like SimpleLogin or Apple's Hide My Email let you create unique aliases for each service, preventing cross-site tracking.</p>

<h3>5. Encrypt Sensitive Emails</h3>
<p>Use ProtonMail or PGP encryption for sensitive communications.</p>

<h3>6. Monitor for Breaches</h3>
<p>Regularly check if your email has been exposed in data breaches using tools like <a href="/tool">RECON</a>.</p>
"""
    },
    {
        "slug": "remove-personal-info-internet",
        "title": "How to Remove Your Personal Information from the Internet",
        "excerpt": "A step-by-step guide to cleaning up your online presence and removing personal data from the web.",
        "category": "Privacy",
        "tag_class": "tag-privacy",
        "author": "RECON Team",
        "date": "2026-04-07",
        "read_time": "7 min read",
        "content": """
<h2>Step 1: Discover Your Footprint</h2>
<p>Before you can remove information, you need to know what's out there. Use <a href="/tool">RECON's OSINT Scanner</a> to find all accounts and mentions associated with your username or email.</p>

<h2>Step 2: Delete Old Accounts</h2>
<p>Go through each platform and request account deletion. Some platforms make this difficult — look for guides on JustDeleteMe or AccountKiller.</p>

<h2>Step 3: Remove Data Broker Listings</h2>
<p>Data brokers like Spokeo, WhitePages, and BeenVerified collect and sell your personal information. Visit each site and submit opt-out requests.</p>

<h2>Step 4: Google Yourself</h2>
<p>Search for your name, email, phone number, and usernames. Request removal of sensitive results through Google's content removal tool.</p>

<h2>Step 5: Clean Up Social Media</h2>
<p>Review and delete old posts, photos, and comments. Tighten privacy settings on remaining accounts.</p>

<h2>Step 6: Set Up Monitoring</h2>
<p>Set up Google Alerts for your name and email. Periodically re-scan with OSINT tools to catch new exposures.</p>

<p>Remember, this is an ongoing process. The internet is constantly archiving and indexing data, so regular monitoring is essential.</p>
"""
    },
    {
        "slug": "google-dorking-osint",
        "title": "What is Google Dorking and How is it Used in OSINT?",
        "excerpt": "Google dorking uses advanced search operators to uncover hidden information. Learn the techniques.",
        "category": "OSINT",
        "tag_class": "tag-osint",
        "author": "RECON Team",
        "date": "2026-04-04",
        "read_time": "6 min read",
        "content": """
<h2>What is Google Dorking?</h2>
<p>Google dorking (also called Google hacking) is the technique of using advanced search operators to find information that isn't easily discoverable through normal searches. It's a powerful OSINT technique used by security researchers, journalists, and penetration testers.</p>

<h2>Common Google Dork Operators</h2>
<ul>
<li><strong>site:</strong> — Search within a specific website (e.g., <code>site:reddit.com "username"</code>)</li>
<li><strong>inurl:</strong> — Find pages with specific text in the URL</li>
<li><strong>intitle:</strong> — Search for pages with specific title text</li>
<li><strong>filetype:</strong> — Find specific file types (e.g., <code>filetype:pdf</code>)</li>
<li><strong>"exact phrase"</strong> — Search for an exact string match</li>
</ul>

<h2>OSINT Applications</h2>
<p>In OSINT investigations, Google dorking can reveal:</p>
<ul>
<li>Public documents containing personal information</li>
<li>Exposed configuration files and databases</li>
<li>Social media posts mentioning a target</li>
<li>Forum posts and comments across the web</li>
</ul>

<p>RECON automatically uses Google dorking as part of its scanning engine. <a href="/tool">Try it now</a> to see what Google reveals about your username.</p>
"""
    },
    {
        "slug": "why-care-digital-footprint",
        "title": "Why You Should Care About Your Digital Footprint",
        "excerpt": "Your digital footprint affects your privacy, security, and even your career. Here's why it matters.",
        "category": "Privacy",
        "tag_class": "tag-privacy",
        "author": "RECON Team",
        "date": "2026-04-01",
        "read_time": "5 min read",
        "content": """
<h2>What is a Digital Footprint?</h2>
<p>Your digital footprint is the sum of all the traces you leave online. This includes every account you create, every post you make, every photo you upload, and every website you visit.</p>

<h2>Active vs. Passive Footprints</h2>
<p><strong>Active footprint:</strong> Data you intentionally share — social media posts, forum comments, account registrations.</p>
<p><strong>Passive footprint:</strong> Data collected without your direct action — cookies, IP logs, browsing history, device fingerprints.</p>

<h2>Why It Matters</h2>
<h3>Privacy & Security</h3>
<p>The more data available about you, the easier it is for attackers to craft targeted attacks, steal your identity, or impersonate you.</p>

<h3>Professional Impact</h3>
<p>Employers regularly search for candidates online. Old social media posts, inappropriate comments, or questionable associations can cost you opportunities.</p>

<h3>Personal Safety</h3>
<p>Stalkers and harassers can use your digital footprint to find your location, daily routines, and personal relationships.</p>

<h2>Take Action</h2>
<p>The first step to managing your digital footprint is understanding it. <a href="/tool">Scan your username with RECON</a> to see exactly what the internet knows about you.</p>
"""
    },
    {
        "slug": "top-osint-tools-2026",
        "title": "Top 10 OSINT Tools Every Security Researcher Should Know",
        "excerpt": "A curated list of the most powerful OSINT tools available in 2026 for security professionals.",
        "category": "OSINT",
        "tag_class": "tag-osint",
        "author": "RECON Team",
        "date": "2026-03-28",
        "read_time": "8 min read",
        "content": """
<h2>Essential OSINT Tools</h2>

<h3>1. RECON</h3>
<p>Our own platform scans 120+ platforms for username presence, checks email breaches, performs Google dorking, and correlates identities. <a href="/tool">Try it free</a>.</p>

<h3>2. Maltego</h3>
<p>A powerful link analysis tool that visualizes relationships between people, companies, domains, and other entities.</p>

<h3>3. Shodan</h3>
<p>The search engine for internet-connected devices. Discovers servers, webcams, industrial control systems, and more.</p>

<h3>4. SpiderFoot</h3>
<p>An automated OSINT collection tool that queries over 100 data sources.</p>

<h3>5. theHarvester</h3>
<p>Gathers emails, subdomains, hosts, and employee names from different public sources.</p>

<h3>6. Recon-ng</h3>
<p>A full-featured web reconnaissance framework with modules for various OSINT tasks.</p>

<h3>7. Sherlock</h3>
<p>A command-line tool for hunting usernames across social networks.</p>

<h3>8. Have I Been Pwned</h3>
<p>A free service for checking if your email or phone has been compromised in a data breach.</p>

<h3>9. Wayback Machine</h3>
<p>Access archived versions of websites to find deleted content and historical data.</p>

<h3>10. ExifTool</h3>
<p>Extract metadata from images and documents, revealing information like GPS coordinates and device details.</p>
"""
    },
    {
        "slug": "protect-yourself-after-breach",
        "title": "How to Protect Yourself After a Data Breach",
        "excerpt": "Your data was breached. Don't panic — here's your step-by-step action plan to minimize the damage.",
        "category": "Security",
        "tag_class": "tag-security",
        "author": "RECON Team",
        "date": "2026-03-25",
        "read_time": "6 min read",
        "content": """
<h2>Immediate Actions (First 24 Hours)</h2>
<ol>
<li><strong>Change the breached password</strong> — If you used it anywhere else, change it there too</li>
<li><strong>Enable 2FA</strong> — Add two-factor authentication to the breached account and all critical accounts</li>
<li><strong>Check for unauthorized activity</strong> — Review login history, recent transactions, and sent messages</li>
</ol>

<h2>Short-Term Actions (First Week)</h2>
<ol>
<li><strong>Run a full breach check</strong> — Use <a href="/tool">RECON's email scanner</a> to see all breaches your email is part of</li>
<li><strong>Update all passwords</strong> — Use a password manager to generate unique passwords for every account</li>
<li><strong>Monitor your accounts</strong> — Watch for suspicious emails, login attempts, or unauthorized charges</li>
<li><strong>Consider a credit freeze</strong> — If financial data was exposed, freeze your credit with major bureaus</li>
</ol>

<h2>Long-Term Actions</h2>
<ul>
<li>Set up breach monitoring alerts</li>
<li>Use email aliases for new account registrations</li>
<li>Regularly audit your digital footprint with OSINT tools</li>
<li>Review and minimize the personal data you share online</li>
</ul>

<p>The key is to act quickly and methodically. A data breach doesn't have to be catastrophic if you respond effectively.</p>
"""
    },
]


def get_all_articles():
    """Return all articles sorted by date (newest first)."""
    return sorted(ARTICLES, key=lambda a: a['date'], reverse=True)


def get_article_by_slug(slug):
    """Return a single article by its slug, or None."""
    for article in ARTICLES:
        if article['slug'] == slug:
            return article
    return None


def get_related_articles(current_slug, limit=3):
    """Return related articles (same category, excluding current)."""
    current = get_article_by_slug(current_slug)
    if not current:
        return []
    related = [a for a in ARTICLES if a['slug'] != current_slug and a['category'] == current['category']]
    if len(related) < limit:
        others = [a for a in ARTICLES if a['slug'] != current_slug and a['category'] != current['category']]
        related.extend(others[:limit - len(related)])
    return related[:limit]
