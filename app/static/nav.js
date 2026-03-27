/**
 * Shared navigation bar with auth for all app pages.
 * Include this script on every page. It renders the nav, auth modals, and handles login state.
 *
 * Usage: <script src="/static/nav.js" data-active="dashboard"></script>
 * data-active: which nav link to highlight (dashboard | articles | outlets | webhooks | export)
 */
(function () {
    const activePage = document.currentScript.getAttribute('data-active') || '';

    function injectStyles() {
        const style = document.createElement('style');
        style.textContent = `
            /* ─── Nav ─── */
            .gpr-nav {
                position: sticky; top: 0; z-index: 100;
                padding: 14px 0;
                background: rgba(10,10,15,0.85);
                backdrop-filter: blur(20px);
                border-bottom: 1px solid rgba(42,42,58,0.5);
            }
            .gpr-nav .nav-inner { max-width: 1400px; margin: 0 auto; padding: 0 24px; display: flex; align-items: center; justify-content: space-between; gap: 16px; }
            .gpr-nav .logo { font-weight: 800; font-size: 1.15rem; display: flex; align-items: center; gap: 8px; text-decoration: none; color: #f0f0f5; flex-shrink: 0; }
            .gpr-nav .logo-icon { width: 28px; height: 28px; background: linear-gradient(135deg, #7c5cff, #ec4899); border-radius: 8px; display: grid; place-items: center; font-size: 14px; color: #fff; font-weight: 700; }
            .gpr-nav .nav-links { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
            .gpr-nav .nav-links a {
                color: #8888a0; text-decoration: none; font-size: 0.84rem; font-weight: 500;
                padding: 6px 12px; border-radius: 8px; transition: all .2s;
            }
            .gpr-nav .nav-links a:hover { color: #f0f0f5; background: rgba(124,92,255,0.08); }
            .gpr-nav .nav-links a.active { color: #f0f0f5; background: rgba(124,92,255,0.15); }
            .gpr-nav .nav-auth { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
            .gpr-nav .btn-ghost {
                padding: 7px 16px; border-radius: 8px; font-weight: 600; font-size: 0.84rem;
                border: 1px solid #2a2a3a; cursor: pointer; background: transparent; color: #8888a0;
                font-family: inherit; transition: all .2s;
            }
            .gpr-nav .btn-ghost:hover { color: #f0f0f5; border-color: #7c5cff; }
            .gpr-nav .btn-primary {
                padding: 7px 16px; border-radius: 8px; font-weight: 600; font-size: 0.84rem;
                border: none; cursor: pointer; background: linear-gradient(135deg, #7c5cff, #6344e0);
                color: #fff; font-family: inherit; transition: all .2s;
                box-shadow: 0 4px 16px rgba(124,92,255,0.3);
            }
            .gpr-nav .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 6px 20px rgba(124,92,255,0.4); }
            .gpr-nav .user-pill {
                display: inline-flex; align-items: center; gap: 10px;
                padding: 5px 8px 5px 14px; background: #16161f; border: 1px solid #2a2a3a;
                border-radius: 10px; font-size: 0.84rem; color: #f0f0f5; font-weight: 500;
            }
            .gpr-nav .user-pill .avatar {
                width: 26px; height: 26px; background: linear-gradient(135deg, #7c5cff, #ec4899);
                border-radius: 6px; display: flex; align-items: center; justify-content: center;
                font-size: 0.72rem; font-weight: 700; color: #fff;
            }
            .gpr-nav .user-pill .logout-btn {
                background: none; border: none; color: #5a5a72; cursor: pointer;
                font-size: 0.78rem; font-family: inherit; padding: 2px 6px; border-radius: 4px; transition: color .2s;
            }
            .gpr-nav .user-pill .logout-btn:hover { color: #f87171; }

            /* ─── Auth Modal ─── */
            .auth-overlay {
                display: none; position: fixed; inset: 0;
                background: rgba(0,0,0,0.7); backdrop-filter: blur(8px);
                z-index: 200; align-items: center; justify-content: center;
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

    function link(href, label, id) {
        const cls = id === activePage ? ' class="active"' : '';
        return `<a href="${href}"${cls}>${label}</a>`;
    }

    function renderNav() {
        const nav = document.createElement('nav');
        nav.className = 'gpr-nav';
        nav.innerHTML = `
            <div class="nav-inner">
                <a class="logo" href="/"><div class="logo-icon">G</div> Gaming PR</a>
                <div class="nav-links">
                    ${link('/dashboard', 'Dashboard', 'dashboard')}
                    ${link('/articles', 'Articles', 'articles')}
                    ${link('/manage/articles', 'My Articles', 'manage-articles')}
                    ${link('/translations', 'Translations', 'translations')}
                    ${link('/outlets', 'Outlets', 'outlets')}
                    ${link('/scraper', 'Scraper', 'scraper')}
                    ${link('/feed', 'Live Feed', 'feed')}
                    ${link('/emails', 'Email', 'emails')}
                    ${link('/webhooks', 'Webhooks', 'webhooks')}
                    ${link('/export', 'Export', 'export')}
                    ${link('/docs', 'API Docs', 'docs')}
                </div>
                <div class="nav-auth" id="gprNavAuth"></div>
            </div>
        `;
        document.body.prepend(nav);
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

        // Close on overlay click
        document.querySelectorAll('.auth-overlay').forEach(o => {
            o.addEventListener('click', e => { if (e.target === o) gprCloseModals(); });
        });
    }

    // ─── Auth state ───
    window.gprGetToken = function () { return localStorage.getItem('gpr_token'); };

    function renderAuthState() {
        const container = document.getElementById('gprNavAuth');
        if (!container) return;
        const user = JSON.parse(localStorage.getItem('gpr_user') || 'null');
        if (user) {
            const initials = user.username.slice(0, 2).toUpperCase();
            container.innerHTML =
                '<div class="user-pill">' +
                    '<a href="/profile" class="avatar" style="text-decoration:none;color:#fff" title="Profile">' + initials + '</a>' +
                    '<a href="/profile" style="text-decoration:none;color:inherit">' + user.username + '</a>' +
                    '<button class="logout-btn" onclick="gprLogout()">Log out</button>' +
                '</div>';
        } else {
            container.innerHTML =
                '<button class="btn-ghost" onclick="gprOpenModal(\'login\')">Log in</button>' +
                '<button class="btn-primary" onclick="gprOpenModal(\'register\')">Sign up</button>';
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

    // ─── Init ───
    injectStyles();
    renderNav();
    renderModals();
    renderAuthState();
})();
