/**
 * Shared left sidebar navigation with auth for all app pages.
 * Include on every page: <script src="/static/nav.js" data-active="dashboard"></script>
 */
(function () {
    const activePage = document.currentScript.getAttribute('data-active') || '';

    function injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* ─── Sidebar ─── */
            .gpr-sidebar {
                position: fixed; top: 0; left: 0; bottom: 0; width: 240px;
                background: #0d0d14; border-right: 1px solid #1e1e2e;
                z-index: 100; display: flex; flex-direction: column;
                overflow-y: auto; overflow-x: hidden;
                scrollbar-width: thin; scrollbar-color: #2a2a3a transparent;
            }
            .gpr-sidebar::-webkit-scrollbar { width: 4px; }
            .gpr-sidebar::-webkit-scrollbar-thumb { background: #2a2a3a; border-radius: 4px; }

            .gpr-sidebar .sb-header {
                padding: 20px 18px 16px; border-bottom: 1px solid #1e1e2e;
                flex-shrink: 0;
            }
            .gpr-sidebar .logo {
                font-weight: 800; font-size: 1.05rem; display: flex; align-items: center;
                gap: 10px; text-decoration: none; color: #f0f0f5;
            }
            .gpr-sidebar .logo-icon {
                width: 32px; height: 32px; background: linear-gradient(135deg, #7c5cff, #ec4899);
                border-radius: 10px; display: grid; place-items: center;
                font-size: 14px; color: #fff; font-weight: 700; flex-shrink: 0;
            }

            .gpr-sidebar .sb-nav { flex: 1; padding: 12px 10px; }
            .gpr-sidebar .sb-group { margin-bottom: 20px; }
            .gpr-sidebar .sb-group-label {
                font-size: 0.65rem; font-weight: 700; text-transform: uppercase;
                letter-spacing: 1px; color: #5a5a72; padding: 0 10px; margin-bottom: 6px;
            }
            .gpr-sidebar .sb-link {
                display: flex; align-items: center; gap: 10px;
                padding: 8px 10px; border-radius: 8px; font-size: 0.84rem; font-weight: 500;
                color: #8888a0; text-decoration: none; transition: all .15s;
                margin-bottom: 1px;
            }
            .gpr-sidebar .sb-link:hover { color: #f0f0f5; background: rgba(124,92,255,0.08); }
            .gpr-sidebar .sb-link.active { color: #f0f0f5; background: rgba(124,92,255,0.15); }
            .gpr-sidebar .sb-link .sb-icon {
                width: 20px; text-align: center; font-size: 0.9rem; flex-shrink: 0;
                opacity: 0.7;
            }
            .gpr-sidebar .sb-link.active .sb-icon { opacity: 1; }
            .gpr-sidebar .sb-link .sb-text { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

            .gpr-sidebar .sb-divider { height: 1px; background: #1e1e2e; margin: 8px 10px; }

            /* User section at bottom */
            .gpr-sidebar .sb-footer {
                padding: 14px 14px; border-top: 1px solid #1e1e2e;
                flex-shrink: 0;
            }
            .gpr-sidebar .sb-user {
                display: flex; align-items: center; gap: 10px;
                padding: 8px 6px; border-radius: 8px;
                transition: background .15s;
            }
            .gpr-sidebar .sb-user:hover { background: rgba(124,92,255,0.06); }
            .gpr-sidebar .sb-avatar {
                width: 32px; height: 32px; background: linear-gradient(135deg, #7c5cff, #ec4899);
                border-radius: 8px; display: flex; align-items: center; justify-content: center;
                font-size: 0.72rem; font-weight: 700; color: #fff; flex-shrink: 0;
                text-decoration: none;
            }
            .gpr-sidebar .sb-user-info { flex: 1; min-width: 0; }
            .gpr-sidebar .sb-user-name {
                font-size: 0.82rem; font-weight: 600; color: #f0f0f5;
                white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
            }
            .gpr-sidebar .sb-user-name a { color: inherit; text-decoration: none; }
            .gpr-sidebar .sb-user-role { font-size: 0.68rem; color: #5a5a72; }
            .gpr-sidebar .sb-logout {
                background: none; border: none; color: #5a5a72; cursor: pointer;
                font-size: 0.72rem; font-family: inherit; padding: 4px 6px;
                border-radius: 4px; transition: color .2s; flex-shrink: 0;
            }
            .gpr-sidebar .sb-logout:hover { color: #f87171; }
            .gpr-sidebar .sb-auth-btns { display: flex; flex-direction: column; gap: 6px; }
            .gpr-sidebar .sb-btn {
                display: block; text-align: center; padding: 9px 14px; border-radius: 8px;
                font-size: 0.84rem; font-weight: 600; cursor: pointer; font-family: inherit;
                border: none; transition: all .2s;
            }
            .gpr-sidebar .sb-btn-primary {
                background: linear-gradient(135deg, #7c5cff, #6344e0); color: #fff;
                box-shadow: 0 3px 12px rgba(124,92,255,0.25);
            }
            .gpr-sidebar .sb-btn-primary:hover { box-shadow: 0 4px 16px rgba(124,92,255,0.35); }
            .gpr-sidebar .sb-btn-ghost {
                background: transparent; color: #8888a0;
                border: 1px solid #2a2a3a;
            }
            .gpr-sidebar .sb-btn-ghost:hover { color: #f0f0f5; border-color: #7c5cff; }

            /* ─── Mobile hamburger ─── */
            .gpr-hamburger {
                display: none; position: fixed; top: 14px; left: 14px; z-index: 101;
                width: 40px; height: 40px; border-radius: 10px;
                background: #16161f; border: 1px solid #2a2a3a;
                cursor: pointer; align-items: center; justify-content: center;
            }
            .gpr-hamburger span {
                display: block; width: 18px; height: 2px; background: #f0f0f5;
                border-radius: 2px; transition: all .2s; position: relative;
            }
            .gpr-hamburger span::before, .gpr-hamburger span::after {
                content: ''; position: absolute; left: 0; width: 100%; height: 2px;
                background: #f0f0f5; border-radius: 2px; transition: all .2s;
            }
            .gpr-hamburger span::before { top: -6px; }
            .gpr-hamburger span::after { top: 6px; }
            .gpr-hamburger.open span { background: transparent; }
            .gpr-hamburger.open span::before { top: 0; transform: rotate(45deg); }
            .gpr-hamburger.open span::after { top: 0; transform: rotate(-45deg); }

            .gpr-sidebar-overlay {
                display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.5);
                z-index: 99;
            }

            /* ─── Body offset ─── */
            body { padding-left: 240px; }

            @media (max-width: 768px) {
                body { padding-left: 0; }
                .gpr-sidebar { transform: translateX(-100%); transition: transform .25s ease; }
                .gpr-sidebar.open { transform: translateX(0); }
                .gpr-hamburger { display: flex; }
                .gpr-sidebar-overlay.open { display: block; }
            }

            /* ─── Auth Modal ─── */
            .auth-overlay {
                display: none; position: fixed; inset: 0;
                background: rgba(0,0,0,0.7); backdrop-filter: blur(8px);
                z-index: 300; align-items: center; justify-content: center;
            }
            .auth-overlay.active { display: flex; }
            .auth-modal {
                background: #111118; border: 1px solid #2a2a3a; border-radius: 20px;
                padding: 36px; width: 100%; max-width: 400px; position: relative;
                box-shadow: 0 25px 60px rgba(0,0,0,0.5);
            }
            .auth-modal .close-btn {
                position: absolute; top: 14px; right: 14px; background: none; border: none;
                color: #5a5a72; cursor: pointer; font-size: 1.3rem; transition: color .2s;
            }
            .auth-modal .close-btn:hover { color: #f0f0f5; }
            .auth-modal h2 { font-size: 1.35rem; font-weight: 700; margin-bottom: 6px; color: #f0f0f5; }
            .auth-modal .sub { color: #8888a0; font-size: 0.88rem; margin-bottom: 24px; }
            .auth-modal .fg { margin-bottom: 16px; }
            .auth-modal label { display: block; font-size: 0.82rem; font-weight: 500; color: #8888a0; margin-bottom: 5px; }
            .auth-modal input {
                width: 100%; padding: 10px 12px; background: #0a0a0f; border: 1px solid #2a2a3a;
                border-radius: 8px; color: #f0f0f5; font-size: 0.9rem; font-family: inherit; outline: none; transition: border-color .2s;
            }
            .auth-modal input:focus { border-color: #7c5cff; }
            .auth-modal input::placeholder { color: #5a5a72; }
            .auth-modal .submit-btn {
                width: 100%; padding: 11px; border-radius: 10px; font-weight: 600; font-size: 0.92rem;
                border: none; cursor: pointer; background: linear-gradient(135deg, #7c5cff, #6344e0);
                color: #fff; font-family: inherit; margin-top: 4px; transition: all .2s;
                box-shadow: 0 4px 16px rgba(124,92,255,0.3);
            }
            .auth-modal .submit-btn:hover { transform: translateY(-1px); }
            .auth-modal .submit-btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }
            .auth-modal .form-error {
                background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.3);
                color: #f87171; padding: 9px 12px; border-radius: 8px; font-size: 0.82rem;
                margin-bottom: 14px; display: none;
            }
            .auth-modal .form-error.visible { display: block; }
            .auth-modal .switch-text { text-align: center; margin-top: 18px; font-size: 0.82rem; color: #8888a0; }
            .auth-modal .switch-text a { color: #9b7fff; font-weight: 600; cursor: pointer; text-decoration: none; }
            .auth-modal .switch-text a:hover { text-decoration: underline; }
        `;
        document.head.appendChild(style);
    }

    function slink(href, icon, label, id) {
        const cls = id === activePage ? ' active' : '';
        return `<a href="${href}" class="sb-link${cls}"><span class="sb-icon">${icon}</span><span class="sb-text">${label}</span></a>`;
    }

    function renderSidebar() {
        // Hamburger button
        const hamburger = document.createElement('button');
        hamburger.className = 'gpr-hamburger';
        hamburger.innerHTML = '<span></span>';
        hamburger.onclick = toggleMobileMenu;
        document.body.prepend(hamburger);

        // Overlay
        const overlay = document.createElement('div');
        overlay.className = 'gpr-sidebar-overlay';
        overlay.onclick = toggleMobileMenu;
        document.body.prepend(overlay);

        // Sidebar
        const sidebar = document.createElement('aside');
        sidebar.className = 'gpr-sidebar';
        sidebar.innerHTML = `
            <div class="sb-header">
                <a class="logo" href="/"><div class="logo-icon">G</div> Gaming PR</a>
            </div>
            <div class="sb-nav">
                <div class="sb-group">
                    ${slink('/dashboard', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>', 'Dashboard', 'dashboard')}
                </div>
                <div class="sb-group">
                    <div class="sb-group-label">Content</div>
                    ${slink('/articles', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></svg>', 'Scraped Articles', 'articles')}
                    ${slink('/manage/articles', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>', 'My Articles', 'manage-articles')}
                    ${slink('/translations', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><circle cx="12" cy="12" r="10"/><line x1="2" y1="12" x2="22" y2="12"/><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>', 'Translations', 'translations')}
                </div>
                <div class="sb-group">
                    <div class="sb-group-label">Sources</div>
                    ${slink('/outlets', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>', 'Outlets', 'outlets')}
                    ${slink('/scraper', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>', 'Scraper', 'scraper')}
                    ${slink('/feed', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1"/></svg>', 'Live Feed', 'feed')}
                </div>
                <div class="sb-group">
                    <div class="sb-group-label">Integrations</div>
                    ${slink('/emails', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/><polyline points="22,6 12,13 2,6"/></svg>', 'Email', 'emails')}
                    ${slink('/webhooks', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg>', 'Webhooks', 'webhooks')}
                    ${slink('/export', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>', 'Export', 'export')}
                </div>
                <div class="sb-divider"></div>
                ${slink('/docs', '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>', 'API Docs', 'docs')}
            </div>
            <div class="sb-footer" id="gprNavAuth"></div>
        `;
        document.body.prepend(sidebar);
    }

    function toggleMobileMenu() {
        document.querySelector('.gpr-sidebar').classList.toggle('open');
        document.querySelector('.gpr-hamburger').classList.toggle('open');
        document.querySelector('.gpr-sidebar-overlay').classList.toggle('open');
    }

    function renderModals() {
        const div = document.createElement('div');
        div.innerHTML = `
            <div class="auth-overlay" id="gprLoginModal">
                <div class="auth-modal">
                    <button class="close-btn" onclick="gprCloseModals()">&times;</button>
                    <h2>Welcome back</h2>
                    <p class="sub">Log in to your Gaming PR account</p>
                    <div class="form-error" id="gprLoginError"></div>
                    <form onsubmit="gprHandleLogin(event)">
                        <div class="fg"><label>Username</label><input type="text" id="gprLoginUser" placeholder="Enter username" required></div>
                        <div class="fg"><label>Password</label><input type="password" id="gprLoginPass" placeholder="Enter password" required></div>
                        <button type="submit" class="submit-btn" id="gprLoginBtn">Log in</button>
                    </form>
                    <p class="switch-text">Don't have an account? <a onclick="gprOpenModal('register')">Sign up</a></p>
                </div>
            </div>
            <div class="auth-overlay" id="gprRegisterModal">
                <div class="auth-modal">
                    <button class="close-btn" onclick="gprCloseModals()">&times;</button>
                    <h2>Create an account</h2>
                    <p class="sub">Join the Gaming PR Platform</p>
                    <div class="form-error" id="gprRegisterError"></div>
                    <form onsubmit="gprHandleRegister(event)">
                        <div class="fg"><label>Username</label><input type="text" id="gprRegUser" placeholder="Choose a username" required></div>
                        <div class="fg"><label>Email</label><input type="email" id="gprRegEmail" placeholder="you@example.com" required></div>
                        <div class="fg"><label>Password</label><input type="password" id="gprRegPass" placeholder="At least 8 characters" required minlength="8"></div>
                        <button type="submit" class="submit-btn" id="gprRegBtn">Create account</button>
                    </form>
                    <p class="switch-text">Already have an account? <a onclick="gprOpenModal('login')">Log in</a></p>
                </div>
            </div>
        `;
        document.body.appendChild(div);
        document.querySelectorAll('.auth-overlay').forEach(o => {
            o.addEventListener('click', e => { if (e.target === o) gprCloseModals(); });
        });
    }

    // ─── Auth state ───
    window.gprGetToken = function () { return localStorage.getItem('gpr_token'); };

    function escHtml(s) { const d = document.createElement('div'); d.textContent = s; return d.innerHTML; }

    function renderAuthState() {
        const container = document.getElementById('gprNavAuth');
        if (!container) return;
        const user = JSON.parse(localStorage.getItem('gpr_user') || 'null');
        if (user) {
            const initials = escHtml(user.username.slice(0, 2).toUpperCase());
            const safeName = escHtml(user.username);
            container.innerHTML =
                '<div class="sb-user">' +
                    '<a href="/profile" class="sb-avatar" title="Profile">' + initials + '</a>' +
                    '<div class="sb-user-info">' +
                        '<div class="sb-user-name"><a href="/profile">' + safeName + '</a></div>' +
                        '<div class="sb-user-role">' + (user.is_admin ? 'Admin' : 'User') + '</div>' +
                    '</div>' +
                    '<button class="sb-logout" onclick="gprLogout()" title="Log out">' +
                        '<svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" viewBox="0 0 24 24"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>' +
                    '</button>' +
                '</div>';
        } else {
            container.innerHTML =
                '<div class="sb-auth-btns">' +
                    '<button class="sb-btn sb-btn-primary" onclick="gprOpenModal(\'login\')">Log in</button>' +
                    '<button class="sb-btn sb-btn-ghost" onclick="gprOpenModal(\'register\')">Sign up</button>' +
                '</div>';
        }
    }

    window.gprOpenModal = function (type) {
        gprCloseModals();
        document.getElementById(type === 'register' ? 'gprRegisterModal' : 'gprLoginModal').classList.add('active');
    };

    window.gprCloseModals = function () {
        document.querySelectorAll('.auth-overlay').forEach(m => m.classList.remove('active'));
        document.querySelectorAll('.auth-modal .form-error').forEach(e => { e.textContent = ''; e.classList.remove('visible'); });
    };

    window.gprLogout = function () {
        localStorage.removeItem('gpr_token');
        localStorage.removeItem('gpr_user');
        renderAuthState();
    };

    function showError(id, msg) {
        const el = document.getElementById(id);
        el.textContent = msg;
        el.classList.add('visible');
    }

    function setLoggedIn(user, token) {
        localStorage.setItem('gpr_token', token);
        localStorage.setItem('gpr_user', JSON.stringify(user));
        renderAuthState();
        gprCloseModals();
    }

    window.gprHandleLogin = async function (e) {
        e.preventDefault();
        const btn = document.getElementById('gprLoginBtn');
        btn.disabled = true; btn.textContent = 'Logging in...';
        try {
            const res = await fetch('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: document.getElementById('gprLoginUser').value,
                    password: document.getElementById('gprLoginPass').value,
                }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Login failed');
            setLoggedIn(data.user, data.access_token);
        } catch (err) {
            showError('gprLoginError', err.message);
        } finally {
            btn.disabled = false; btn.textContent = 'Log in';
        }
    };

    window.gprHandleRegister = async function (e) {
        e.preventDefault();
        const btn = document.getElementById('gprRegBtn');
        btn.disabled = true; btn.textContent = 'Creating account...';
        try {
            const res = await fetch('/api/auth/register', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    username: document.getElementById('gprRegUser').value,
                    email: document.getElementById('gprRegEmail').value,
                    password: document.getElementById('gprRegPass').value,
                }),
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'Registration failed');
            setLoggedIn(data.user, data.access_token);
        } catch (err) {
            showError('gprRegisterError', err.message);
        } finally {
            btn.disabled = false; btn.textContent = 'Create account';
        }
    };

    // ─── Toast notifications ───
    function injectToastStyles() {
        const s = document.createElement('style');
        s.textContent = `
            .gpr-toast-container { position: fixed; top: 16px; right: 16px; z-index: 400; display: flex; flex-direction: column; gap: 8px; pointer-events: none; }
            .gpr-toast {
                pointer-events: auto; padding: 12px 18px; border-radius: 10px; font-size: 0.84rem; font-weight: 500;
                font-family: 'Inter', sans-serif; box-shadow: 0 8px 30px rgba(0,0,0,0.4); animation: toastIn .3s ease;
                display: flex; align-items: center; gap: 10px; max-width: 380px; cursor: pointer;
                border: 1px solid #2a2a3a; background: #16161f; color: #f0f0f5;
            }
            .gpr-toast.success { border-color: rgba(34,197,94,0.4); }
            .gpr-toast.success .toast-icon { color: #22c55e; }
            .gpr-toast.error { border-color: rgba(239,68,68,0.4); }
            .gpr-toast.error .toast-icon { color: #ef4444; }
            .gpr-toast.info { border-color: rgba(124,92,255,0.4); }
            .gpr-toast.info .toast-icon { color: #9b7fff; }
            .toast-icon { font-size: 1.1rem; flex-shrink: 0; }
            .toast-body { flex: 1; }
            .toast-title { font-weight: 700; font-size: 0.82rem; margin-bottom: 2px; }
            .toast-msg { font-size: 0.78rem; color: #8888a0; }
            .gpr-toast .toast-close { background: none; border: none; color: #5a5a72; cursor: pointer; font-size: 1rem; padding: 0 4px; }
            @keyframes toastIn { from { opacity: 0; transform: translateX(40px); } to { opacity: 1; transform: translateX(0); } }
        `;
        document.head.appendChild(s);
    }

    function renderToastContainer() {
        const c = document.createElement('div');
        c.className = 'gpr-toast-container';
        c.id = 'gprToasts';
        document.body.appendChild(c);
    }

    window.gprToast = function (title, msg, type = 'info', duration = 8000) {
        const container = document.getElementById('gprToasts');
        if (!container) return;
        const t = document.createElement('div');
        t.className = 'gpr-toast ' + type;
        const icon = type === 'success' ? '&#10003;' : type === 'error' ? '&#10007;' : '&#9432;';
        t.innerHTML = `<span class="toast-icon">${icon}</span><div class="toast-body"><div class="toast-title">${title}</div><div class="toast-msg">${msg}</div></div><button class="toast-close" onclick="this.parentElement.remove()">&#215;</button>`;
        container.appendChild(t);
        if (duration > 0) setTimeout(() => { if (t.parentElement) t.remove(); }, duration);
    };

    // ─── Background job tracker ───
    // Stores running scrape jobs in localStorage so any page can track them.
    // Polls /api/scraper/jobs to detect completion and shows a toast.
    function initJobTracker() {
        const POLL_INTERVAL = 5000;
        const STORAGE_KEY = 'gpr_bg_jobs';

        window.gprTrackJob = function (label, outletIds, type) {
            const jobs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            jobs.push({ label, outletIds, type, startedAt: Date.now(), total: outletIds.length, done: 0 });
            localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs));
        };

        window.gprUpdateJobProgress = function (index, done) {
            const jobs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            if (jobs[index]) { jobs[index].done = done; localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs)); }
        };

        window.gprCompleteJob = function (index, summary) {
            const jobs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            if (jobs[index]) {
                const job = jobs[index];
                jobs.splice(index, 1);
                localStorage.setItem(STORAGE_KEY, JSON.stringify(jobs));
                gprToast(
                    job.type === 'articles' ? 'Scrape Complete' : 'Contact Scan Complete',
                    summary || `${job.total} outlet${job.total > 1 ? 's' : ''} processed`,
                    'success', 12000
                );
            }
        };

        // On page load, check if there are stale jobs (older than 30min) and clean them
        const jobs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        const now = Date.now();
        const fresh = jobs.filter(j => now - j.startedAt < 30 * 60 * 1000);
        if (fresh.length !== jobs.length) localStorage.setItem(STORAGE_KEY, JSON.stringify(fresh));

        // Show indicator if jobs are running
        function checkRunningJobs() {
            const jobs = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
            if (jobs.length > 0) {
                const j = jobs[0];
                const pct = j.total > 0 ? Math.round((j.done / j.total) * 100) : 0;
                // Update sidebar footer if element exists
                let indicator = document.getElementById('gprJobIndicator');
                if (!indicator) {
                    const footer = document.querySelector('.gpr-sidebar .sb-footer');
                    if (footer) {
                        indicator = document.createElement('div');
                        indicator.id = 'gprJobIndicator';
                        indicator.style.cssText = 'padding:8px 0 4px;font-size:0.74rem;color:#06b6d4;display:flex;align-items:center;gap:6px';
                        footer.prepend(indicator);
                    }
                }
                if (indicator) {
                    indicator.innerHTML = `<span style="width:12px;height:12px;border:2px solid #2a2a3a;border-top-color:#06b6d4;border-radius:50%;animation:spin .8s linear infinite;display:inline-block"></span> ${j.label} ${j.done}/${j.total}`;
                }
            } else {
                const indicator = document.getElementById('gprJobIndicator');
                if (indicator) indicator.remove();
            }
        }
        setInterval(checkRunningJobs, 2000);
        checkRunningJobs();
    }

    // ─── Init ───
    injectStyles();
    injectToastStyles();
    renderSidebar();
    renderToastContainer();
    renderModals();
    renderAuthState();
    initJobTracker();
})();
