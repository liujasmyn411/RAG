// ============================================================
// 林黛玉 Agent 学生管理系统 — 主应用逻辑
// ============================================================

const App = (function () {
  // ── 状态 ──
  let currentUser = null;
  let currentRole = null; // 'student' | 'teacher' | 'admin'
  let chatMessages = [];
  let activeModal = null;

  // ── 路由表 ──
  const routes = {
    '': 'login',
    'login': 'login',
    // 学生
    'student/chat': 'studentChat',
    'student/scores': 'studentScores',
    'student/employment': 'studentEmployment',
    'student/search': 'studentSearch',
    // 教师
    'teacher/students': 'teacherStudents',
    'teacher/profile': 'teacherProfile',
    'teacher/alerts': 'teacherAlerts',
    'teacher/stats': 'teacherStats',
    // 管理员
    'admin/accounts': 'adminAccounts',
    'admin/security': 'adminSecurity',
    'admin/knowledge': 'adminKnowledge',
    'admin/config': 'adminConfig',
    // CRUD
    'crud/students': 'crudStudents',
    'crud/scores': 'crudScores',
    'crud/employment': 'crudEmployment',
    'crud/classes': 'crudClasses',
    'crud/teachers': 'crudTeachers',
    // 可视化
    'architecture': 'architecture',
    // 统计
    'statistics': 'statistics',
    // NL 查询
    'nl-query': 'nlQuery'
  };

  // ── 初始化 ──
  function init() {
    bindGlobalEvents();
    window.addEventListener('hashchange', handleRoute);
    handleRoute();
  }

  // ── 全局事件 ──
  function bindGlobalEvents() {
    // 角色切换
    document.querySelectorAll('.role-switch button').forEach(btn => {
      btn.addEventListener('click', function () {
        const role = this.dataset.role;
        switchRole(role);
      });
    });

    // 模式切换
    const modeToggle = document.getElementById('modeToggle');
    if (modeToggle) {
      modeToggle.checked = API.getMode() === 'real';
      modeToggle.addEventListener('change', function () {
        const newMode = this.checked ? 'real' : 'mock';
        API.setMode(newMode);
        updateModeLabel();
        showToast('已切换至 ' + (newMode === 'mock' ? '模拟数据' : '真实API') + ' 模式', 'info');
        handleRoute(); // 刷新当前页
      });
    }
    updateModeLabel();

    // 弹窗关闭
    document.getElementById('modalOverlay')?.addEventListener('click', function (e) {
      if (e.target === this) closeModal();
    });
    document.getElementById('modalClose')?.addEventListener('click', closeModal);

    // 侧边栏菜单点击
    document.getElementById('sidebarMenu')?.addEventListener('click', function (e) {
      const item = e.target.closest('.sidebar-item');
      if (item && item.dataset.route) {
        navigate(item.dataset.route);
      }
    });
  }

  function updateModeLabel() {
    const mockEl = document.getElementById('modeLabelMock');
    const realEl = document.getElementById('modeLabelReal');
    if (mockEl) mockEl.classList.toggle('active', API.getMode() === 'mock');
    if (realEl) realEl.classList.toggle('active', API.getMode() === 'real');
  }

  // ── 路由 ──
  function navigate(hash) {
    window.location.hash = '#' + hash;
  }

  function handleRoute() {
    const hash = (window.location.hash || '#').slice(1);
    // 解析带参数的路由: teacher/profile/XH_2024001
    let routeKey = hash;
    let routeParam = null;
    for (const pattern of Object.keys(routes)) {
      if (pattern.includes('/')) {
        const prefix = pattern.split('/').slice(0, -1).join('/');
        if (hash.startsWith(prefix + '/')) {
          routeKey = pattern;
          routeParam = hash.slice((prefix + '/').length);
          break;
        }
      }
    }

    const handlerName = routes[routeKey];
    if (!handlerName) { navigate('login'); return; }

    // 检查登录
    if (routeKey !== '' && routeKey !== 'login' && !currentUser) {
      navigate('login');
      return;
    }

    // 显示/隐藏页面
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    const pageEl = document.getElementById('page-' + handlerName);
    if (pageEl) pageEl.classList.add('active');

    // 渲染侧边栏
    renderSidebar();

    // 更新头部用户信息
    updateHeader();

    // 调用页面渲染函数
    if (typeof window['render_' + handlerName] === 'function') {
      window['render_' + handlerName](routeParam);
    }
  }

  // ── 角色切换 ──
  function switchRole(role) {
    currentRole = role;
    const users = {
      student: { user_id: 'XH_2024001', role: 'student', name: '小红', class_name: '初二3班', teacher_id: 'TCH_001' },
      teacher: { user_id: 'TCH_001', role: 'teacher', name: '张老师', department: '教务处', title: '辅导员' },
      admin: { user_id: 'ADMIN_001', role: 'admin', name: '系统管理员' }
    };
    currentUser = users[role];

    // 更新角色按钮
    document.querySelectorAll('.role-switch button').forEach(b => {
      b.classList.toggle('active', b.dataset.role === role);
    });

    // 更新用户徽章
    const badge = document.getElementById('userBadge');
    if (badge) {
      const initials = currentUser.name.charAt(0);
      badge.innerHTML = `<span class="user-avatar">${initials}</span><span>${currentUser.name}</span>`;
    }

    // 跳转到角色默认页
    const defaultRoutes = {
      student: 'student/chat',
      teacher: 'teacher/students',
      admin: 'admin/accounts'
    };
    navigate(defaultRoutes[role]);
  }

  function updateHeader() {
    if (!currentUser) return;
    const badge = document.getElementById('userBadge');
    if (badge) {
      const initials = currentUser.name.charAt(0);
      badge.innerHTML = `<span class="user-avatar">${initials}</span><span>${currentUser.name}</span>`;
    }
    document.querySelectorAll('.role-switch button').forEach(b => {
      b.classList.toggle('active', b.dataset.role === currentRole);
    });
  }

  // ── 侧边栏 ──
  function renderSidebar() {
    const menu = document.getElementById('sidebarMenu');
    if (!menu) return;
    const hash = (window.location.hash || '#').slice(1);

    let items = [];
    if (currentRole === 'student') {
      items = [
        { section: '林黛玉互动', items: [
          { icon: '🌸', label: '黛玉对话', route: 'student/chat' },
          { icon: '📜', label: '四大名著检索', route: 'student/search' }
        ]},
        { section: '个人中心', items: [
          { icon: '📊', label: '我的成绩', route: 'student/scores' },
          { icon: '💼', label: '我的就业', route: 'student/employment' }
        ]},
        { section: '系统展示', items: [
          { icon: '🏗️', label: '系统架构', route: 'architecture' },
          { icon: '📈', label: '统计分析', route: 'statistics' }
        ]}
      ];
    } else if (currentRole === 'teacher') {
      items = [
        { section: '学生管理', items: [
          { icon: '👥', label: '班级学生', route: 'teacher/students' },
          { icon: '📋', label: '学生画像', route: 'teacher/students' }
        ]},
        { section: '监控预警', items: [
          { icon: '🔔', label: '危机预警', route: 'teacher/alerts' },
          { icon: '📊', label: '班级统计', route: 'teacher/stats' }
        ]},
        { section: '智能查询', items: [
          { icon: '🔍', label: 'NL自然语言查询', route: 'nl-query' }
        ]},
        { section: '数据管理', items: [
          { icon: '📝', label: '学生CRUD', route: 'crud/students' },
          { icon: '📐', label: '成绩管理', route: 'crud/scores' },
          { icon: '💼', label: '就业管理', route: 'crud/employment' }
        ]}
      ];
    } else if (currentRole === 'admin') {
      items = [
        { section: '系统管控', items: [
          { icon: '🔒', label: '账号管控', route: 'admin/accounts' },
          { icon: '🛡️', label: '安全日志', route: 'admin/security' }
        ]},
        { section: '知识库', items: [
          { icon: '📚', label: '红楼知识库', route: 'admin/knowledge' },
          { icon: '⚙️', label: '系统配置', route: 'admin/config' }
        ]},
        { section: '数据管理', items: [
          { icon: '📝', label: '学生CRUD', route: 'crud/students' },
          { icon: '📐', label: '成绩管理', route: 'crud/scores' },
          { icon: '💼', label: '就业管理', route: 'crud/employment' },
          { icon: '🏫', label: '班级管理', route: 'crud/classes' },
          { icon: '👨‍🏫', label: '教师管理', route: 'crud/teachers' }
        ]},
        { section: '系统展示', items: [
          { icon: '🏗️', label: '系统架构', route: 'architecture' },
          { icon: '📈', label: '统计分析', route: 'statistics' }
        ]},
        { section: '智能查询', items: [
          { icon: '🔍', label: 'NL自然语言查询', route: 'nl-query' }
        ]}
      ];
    }

    let html = '';
    items.forEach(section => {
      html += `<div class="sidebar-section">${section.section}</div>`;
      section.items.forEach(item => {
        const isActive = hash === item.route || hash.startsWith(item.route + '/');
        html += `<div class="sidebar-item${isActive ? ' active' : ''}" data-route="${item.route}">
          <span class="icon">${item.icon}</span><span class="label">${item.label}</span>
        </div>`;
      });
    });
    menu.innerHTML = html;
  }

  // ── 弹窗 ──
  function openModal(title, contentHtml, onSave) {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = contentHtml;
    document.getElementById('modalOverlay').classList.add('show');

    const saveBtn = document.getElementById('modalSave');
    const newSaveBtn = saveBtn.cloneNode(true);
    saveBtn.parentNode.replaceChild(newSaveBtn, saveBtn);
    if (onSave) {
      newSaveBtn.style.display = '';
      newSaveBtn.addEventListener('click', onSave);
    } else {
      newSaveBtn.style.display = 'none';
    }
    activeModal = true;
  }

  function closeModal() {
    document.getElementById('modalOverlay').classList.remove('show');
    activeModal = false;
  }

  function getFormData(formId) {
    const form = document.getElementById(formId);
    if (!form) return {};
    const data = {};
    form.querySelectorAll('input, select, textarea').forEach(el => {
      if (el.name) data[el.name] = el.value;
    });
    return data;
  }

  // ── Toast ──
  function showToast(msg, type) {
    type = type || 'info';
    const toast = document.createElement('div');
    toast.className = 'toast toast-' + type;
    toast.textContent = msg;
    document.body.appendChild(toast);
    setTimeout(() => toast.remove(), 3000);
  }

  // ── 工具函数 ──
  function el(id) { return document.getElementById(id); }
  function escapeHtml(str) { const d = document.createElement('div'); d.textContent = str; return d.innerHTML; }

  function formatDate(d) { if (!d) return '-'; return new Date(d).toLocaleDateString('zh-CN'); }
  function formatDateTime(d) { if (!d) return '-'; return new Date(d).toLocaleString('zh-CN'); }

  function emotionLabel(emotion) {
    const map = { anxiety: '焦虑', sadness: '悲伤', frustration: '挫败', anger: '愤怒', hopelessness: '绝望', fear: '恐惧', calm: '平静', happy: '开心', excited: '兴奋', confused: '困惑', shame: '羞愧', lonely: '孤独' };
    return map[emotion] || emotion;
  }
  function emotionColor(emotion) {
    const map = { anxiety: '#E65100', sadness: '#1565C0', hopelessness: '#C62828', fear: '#6A1B9A', calm: '#2E7D32', happy: '#F57F17', frustrated: '#E65100', anger: '#C62828', lonely: '#1565C0' };
    return map[emotion] || '#6B5E4A';
  }

  function statusBadge(status) {
    const map = {
      normal: 'badge-green', flagged_b1_l2: 'badge-orange', limited_b1: 'badge-red', blocked_b1: 'badge-red',
      warned_b2: 'badge-yellow', limited_b2: 'badge-orange', blocked_b2: 'badge-red',
      limited: 'badge-orange', blocked: 'badge-red',
      flagged: 'badge-yellow', pending: 'badge-yellow', confirmed: 'badge-blue', escalated: 'badge-red', closed: 'badge-green'
    };
    const labels = {
      normal: '正常', flagged_b1_l2: 'B1标记', limited_b1: 'B1限制', blocked_b1: 'B1封禁',
      warned_b2: 'B2警告', limited_b2: 'B2限制', blocked_b2: 'B2封禁',
      limited: '已限制', blocked: '已冻结',
      pending: '待处理', confirmed: '已确认', escalated: '已升级', closed: '已关闭'
    };
    return `<span class="badge ${map[status] || 'badge-blue'}">${labels[status] || status}</span>`;
  }

  // ═══════════════════════════════════════════════════════
  //  页面渲染函数
  // ═══════════════════════════════════════════════════════

  // ── 登录页 ──
  window.render_login = function () {
    const container = el('page-login');
    if (!container) return;
    document.querySelector('.app-layout') && (document.querySelector('.app-layout').style.display = 'none');
    document.getElementById('loginShell') && (document.getElementById('loginShell').style.display = 'flex');
  };

  window.doMockLogin = function (role) {
    // Mock 模式快速演示
    if (API.getMode() !== 'mock') {
      API.setMode('mock');
      document.getElementById('modeToggle') && (document.getElementById('modeToggle').checked = false);
    }
    document.querySelector('.app-layout') && (document.querySelector('.app-layout').style.display = 'flex');
    document.getElementById('loginShell') && (document.getElementById('loginShell').style.display = 'none');
    switchRole(role);
  };

  window.doRealLogin = async function () {
    const userId = document.getElementById('loginUserId')?.value.trim();
    const password = document.getElementById('loginPassword')?.value.trim();
    const errEl = document.getElementById('loginError');

    if (!userId || !password) {
      if (errEl) errEl.textContent = '请输入用户ID和密码';
      return;
    }

    const btn = document.getElementById('loginBtn');
    if (btn) { btn.disabled = true; btn.textContent = '登录中...'; }

    try {
      const res = await API.login(userId, password);
      if (res && res.error) {
        if (errEl) errEl.textContent = res.error;
        if (btn) { btn.disabled = false; btn.textContent = '登 录'; }
        return;
      }
      if (!res || !res.access_token) {
        if (errEl) errEl.textContent = '登录失败，请检查后端服务';
        if (btn) { btn.disabled = false; btn.textContent = '登 录'; }
        return;
      }

      // 登录成功
      document.querySelector('.app-layout') && (document.querySelector('.app-layout').style.display = 'flex');
      document.getElementById('loginShell') && (document.getElementById('loginShell').style.display = 'none');
      currentUser = {
        user_id: res.user_id,
        role: res.role,
        name: res.name
      };
      currentRole = res.role;

      const badge = document.getElementById('userBadge');
      if (badge) {
        const initials = currentUser.name.charAt(0);
        badge.innerHTML = `<span class="user-avatar">${initials}</span><span>${currentUser.name}</span>`;
      }
      document.querySelectorAll('.role-switch button').forEach(b => {
        b.classList.toggle('active', b.dataset.role === currentRole);
      });

      const defaultRoutes = { student: 'student/chat', teacher: 'teacher/students', admin: 'admin/accounts' };
      navigate(defaultRoutes[currentRole] || 'student/chat');
    } catch (e) {
      if (errEl) errEl.textContent = '网络错误: ' + e.message;
      if (btn) { btn.disabled = false; btn.textContent = '登 录'; }
    }
  };

  // 登录页回车触发登录
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && document.getElementById('loginShell')?.style.display !== 'none') {
      window.doRealLogin();
    }
  });

  // ── 学生对话 ──
  window.render_studentChat = async function () {
    const container = el('page-studentChat');
    if (!container) return;
    if (chatMessages.length === 0) {
      chatMessages = [
        { role: 'agent', text: '你来了。今儿可有什么心事，说与我听听？', intent: 'daiyu_chat', tags: [] }
      ];
    }
    renderChatMessages();
    updateMemoryPanel(null);
    updateSafetyIndicator(null);
    bindChatEvents();
  };

  function bindChatEvents() {
    const input = el('chatInput');
    const sendBtn = el('chatSendBtn');
    if (!input || !sendBtn) return;

    const send = async () => {
      const msg = input.value.trim();
      if (!msg) return;
      input.value = '';
      addChatMessage('user', msg);
      input.disabled = true; sendBtn.disabled = true;
      showTyping();

      try {
        const res = await API.sendChat(msg);
        removeTyping();
        addChatMessage('agent', res.reply, res.intent, res.memory_context?.L3 || []);
        updateMemoryPanel(res.memory_context || {});
        updateSafetyIndicator(res.safety_flag);
      } catch (e) {
        removeTyping();
        addChatMessage('system', '⚠️ 消息发送失败：' + e.message);
      }
      input.disabled = false; sendBtn.disabled = false;
      input.focus();
    };

    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });

    // 快捷演示按钮
    document.querySelectorAll('.chat-quick-actions .btn').forEach(btn => {
      btn.addEventListener('click', async function () {
        const scenario = this.dataset.scenario;
        const m = window.MOCK_DATA;
        let msg, reply, intent, memCtx, safetyFlag;

        switch (scenario) {
          case 'academic':
            msg = m.chatScenarios.academic_query.userMessage;
            reply = m.chatScenarios.academic_query.agentReply;
            intent = 'academic_query';
            memCtx = m.chatScenarios.academic_query.memoryContext;
            safetyFlag = null;
            break;
          case 'chat':
            msg = m.chatScenarios.daiyu_chat.userMessage;
            reply = m.chatScenarios.daiyu_chat.agentReply;
            intent = 'daiyu_chat';
            memCtx = m.chatScenarios.daiyu_chat.memoryContext;
            safetyFlag = null;
            break;
          case 'crisis':
            msg = m.chatScenarios.psych_crisis.userMessage;
            reply = m.chatScenarios.psych_crisis.agentReply;
            intent = 'psych_crisis';
            memCtx = m.chatScenarios.psych_crisis.memoryContext;
            safetyFlag = 'flagged';
            break;
          case 'b1':
            msg = m.chatScenarios.safety_b1.userMessage;
            reply = m.chatScenarios.safety_b1.agentReply;
            intent = 'blocked';
            memCtx = m.chatScenarios.safety_b1.memoryContext;
            safetyFlag = 'flagged';
            break;
          case 'b2':
            msg = m.chatScenarios.safety_b2.userMessage;
            reply = m.chatScenarios.safety_b2.agentReply;
            intent = 'daiyu_chat';
            memCtx = m.chatScenarios.safety_b2.memoryContext;
            safetyFlag = null;
            break;
        }

        addChatMessage('user', msg);
        showTyping();
        await sleep(800);
        removeTyping();
        addChatMessage('agent', reply, intent);
        updateMemoryPanel(memCtx);
        updateSafetyIndicator(safetyFlag);
      });
    });
  }

  function addChatMessage(role, text, intent, tags) {
    chatMessages.push({ role, text, intent: intent || null, tags: tags || [], time: new Date() });
    renderChatMessages();
  }

  function renderChatMessages() {
    const container = el('chatMessages');
    if (!container) return;
    let html = '';
    chatMessages.forEach((msg, i) => {
      if (msg.role === 'system') {
        html += `<div class="chat-msg system"><div class="msg-bubble">${escapeHtml(msg.text)}</div></div>`;
      } else {
        const avatarClass = msg.role === 'agent' ? 'agent-avatar' : 'user-avatar';
        const avatarText = msg.role === 'agent' ? '黛' : (currentUser?.name?.charAt(0) || '我');
        html += `<div class="chat-msg ${msg.role}">
          <div class="msg-avatar ${avatarClass}">${avatarText}</div>
          <div>
            <div class="msg-bubble">${escapeHtml(msg.text).replace(/\n/g, '<br>')}</div>
            ${msg.tags && msg.tags.length > 0 ? `<div class="msg-memory-tags">${msg.tags.map(t => `<span class="msg-memory-tag active">${t}</span>`).join('')}</div>` : ''}
          </div>
        </div>`;
      }
    });
    container.innerHTML = html;
    container.scrollTop = container.scrollHeight;
  }

  function showTyping() {
    const container = el('chatMessages');
    if (!container) return;
    const div = document.createElement('div');
    div.className = 'chat-msg agent';
    div.id = 'typingIndicator';
    div.innerHTML = `<div class="msg-avatar agent-avatar">黛</div><div class="msg-bubble"><div class="typing-indicator"><span></span><span></span><span></span></div></div>`;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
  }

  function removeTyping() {
    const el = document.getElementById('typingIndicator');
    if (el) el.remove();
  }

  function updateMemoryPanel(memCtx) {
    const panel = el('memoryPanel');
    if (!panel) return;

    if (!memCtx || Object.keys(memCtx).every(k => !memCtx[k])) {
      panel.innerHTML = '<div class="memory-block empty">暂无记忆上下文注入</div>';
      return;
    }

    let html = '';

    // L0
    html += '<div class="memory-block"><div class="title">🏯 L0 角色本体</div>';
    if (memCtx.L0 && memCtx.L0.scene) {
      html += `<div class="item">场景：${escapeHtml(memCtx.L0.scene)}</div>`;
      html += `<div class="item">情绪：${escapeHtml(memCtx.L0.emotion || '')}</div>`;
      html += `<div class="item">提示：${escapeHtml(memCtx.L0.hint || '')}</div>`;
    } else { html += '<div class="item">未加载</div>'; }
    html += '</div>';

    // L1
    html += '<div class="memory-block"><div class="title">📋 L1 事实锚点</div>';
    if (memCtx.L1) {
      Object.entries(memCtx.L1).forEach(([k, v]) => {
        html += `<div class="item"><b>${k}</b>: ${v}</div>`;
      });
    } else { html += '<div class="item">未加载</div>'; }
    html += '</div>';

    // L2
    html += '<div class="memory-block"><div class="title">🧠 L2 语义认知 (Neo4j)</div>';
    if (memCtx.L2 && memCtx.L2.length > 0) {
      memCtx.L2.forEach(c => {
        html += `<div class="item"><b>${escapeHtml(c.label || c.relation)}</b>: ${escapeHtml(c.detail || '')}</div>`;
      });
    } else { html += '<div class="item">未加载</div>'; }
    html += '</div>';

    // L3
    html += '<div class="memory-block"><div class="title">📸 L3 情景快照 (Milvus)</div>';
    if (memCtx.L3 && memCtx.L3.length > 0) {
      memCtx.L3.forEach(m => {
        html += `<div class="item"><b>${escapeHtml(m.label || m.emotion)}</b>: ${escapeHtml(m.detail || m.summary || '')}</div>`;
      });
    } else { html += '<div class="item">未检索到相关快照</div>'; }
    html += '</div>';

    // 安全
    if (memCtx.safety) {
      html += '<div class="memory-block" style="border-color:#F44336;"><div class="title">🛡️ 安全事件</div>';
      Object.entries(memCtx.safety).forEach(([k, v]) => {
        html += `<div class="item"><b>${k}</b>: ${v}</div>`;
      });
      html += '</div>';
    }

    panel.innerHTML = html;
  }

  function updateSafetyIndicator(flag) {
    const el = document.getElementById('safetyIndicator');
    if (!el) return;
    if (flag === 'flagged') {
      el.className = 'safety-indicator flagged';
      el.textContent = '⚠️ 安全熔断已触发 — 已切换至安全响应模式';
    } else {
      el.className = 'safety-indicator safe';
      el.textContent = '✅ 安全状态正常 — 黛玉角色正常运行中';
    }
  }

  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  // ── 学生：成绩 ──
  window.render_studentScores = async function () {
    const container = el('page-studentScores');
    if (!container) return;
    const scores = await API.getScores(currentUser.user_id);
    let html = '<div class="card"><div class="card-header">📊 成绩趋势</div>';
    html += renderLineChart(scores, 400, 200);
    html += '</div>';
    html += '<div class="card"><div class="card-header">📋 成绩列表</div><div class="table-wrap"><table>';
    html += '<thead><tr><th>考核序次</th><th>成绩</th><th>日期</th></tr></thead><tbody>';
    (scores || []).forEach(s => {
      const cls = s.score >= 80 ? 'color:var(--jade)' : s.score >= 60 ? 'color:var(--gold)' : 'color:var(--zhu-sha)';
      html += `<tr><td>第${s.exam_sequence}次</td><td style="${cls};font-weight:600;">${s.score}分</td><td>${formatDate(s.created_at)}</td></tr>`;
    });
    html += '</tbody></table></div></div>';
    container.innerHTML = html;
  };

  // ── 学生：就业 ──
  window.render_studentEmployment = async function () {
    const container = el('page-studentEmployment');
    if (!container) return;
    const emp = await API.getEmployment(currentUser.user_id);
    let html = '<div class="card"><div class="card-header">💼 就业信息</div>';
    if (emp && emp.company_name) {
      html += `<div class="report-section"><div class="report-field"><span class="field-label">公司</span><span class="field-value">${escapeHtml(emp.company_name)}</span></div>
        <div class="report-field"><span class="field-label">薪资</span><span class="field-value" style="color:var(--zhu-sha);font-weight:600;">¥${emp.salary}/月</span></div>
        <div class="report-field"><span class="field-label">就业开放</span><span class="field-value">${formatDate(emp.employment_open_time)}</span></div>
        <div class="report-field"><span class="field-label">Offer时间</span><span class="field-value">${formatDate(emp.offer_time)}</span></div>
        ${emp.employment_open_time && emp.offer_time ? `<div class="report-field"><span class="field-label">就业时长</span><span class="field-value">${Math.ceil((new Date(emp.offer_time) - new Date(emp.employment_open_time)) / (1000*60*60*24))} 天</span></div>` : ''}
      </div>`;
    } else {
      html += '<p style="color:var(--mo-lighter);text-align:center;padding:20px;">暂无就业信息</p>';
    }
    html += '</div>';
    container.innerHTML = html;
  };

  // ── 学生：四大名著检索 ──
  window.render_studentSearch = async function () {
    const container = el('page-studentSearch');
    if (!container) return;
    container.innerHTML = `
      <div class="page-title">📜 四大名著检索</div>
      <div class="search-bar">
        <input class="form-input" id="searchInput" placeholder="输入关键词检索四大名著..." style="flex:1;">
        <select class="form-select" id="searchSource" style="width:150px;">
          <option value="">全部名著</option>
          <option value="红楼梦">红楼梦</option>
          <option value="三国演义">三国演义</option>
          <option value="水浒传">水浒传</option>
          <option value="西游记">西游记</option>
        </select>
        <button class="btn btn-gold" id="searchBtn">🔍 检索</button>
      </div>
      <div id="searchResults" class="search-results">
        <p style="color:var(--mo-lighter);text-align:center;padding:40px;">输入关键词，探索四大名著的精彩片段</p>
      </div>
    `;

    const doSearch = () => {
      const query = el('searchInput').value.trim();
      const source = el('searchSource').value;
      const results = API.getClassicSearch(query, source);
      const resultsDiv = el('searchResults');
      if (results.length === 0) {
        resultsDiv.innerHTML = '<p style="color:var(--mo-lighter);text-align:center;padding:40px;">未找到相关结果</p>';
        return;
      }
      resultsDiv.innerHTML = results.map(r => `
        <div class="result-item">
          <div class="result-title">${escapeHtml(r.title)}</div>
          <div class="result-content">${escapeHtml(r.content)}</div>
          <div class="result-meta">
            <span>📖 ${escapeHtml(r.source)}</span>
            <span>相关度: ${(r.relevance * 100).toFixed(0)}%</span>
          </div>
        </div>
      `).join('');
    };

    el('searchBtn').addEventListener('click', doSearch);
    el('searchInput').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
  };

  // ── 教师：班级学生列表 ──
  window.render_teacherStudents = async function () {
    const container = el('page-teacherStudents');
    if (!container) return;
    const students = await API.getStudents({});
    const profiles = window.MOCK_DATA.studentProfiles;

    let html = '<div class="page-title">👥 班级学生</div><div class="student-grid">';
    students.forEach(s => {
      const profile = profiles[s.student_id];
      const status = profile ? profile.safety_status : 'normal';
      let emotionTag = '';
      if (profile) {
        if (profile.safety_status.includes('blocked') || profile.safety_status.includes('crisis')) emotionTag = '<span class="badge badge-red">⚠ 危机</span>';
        else if (profile.violation_b2_count >= 3) emotionTag = '<span class="badge badge-orange">需关注</span>';
        else if (profile.safety_status === 'normal') emotionTag = '<span class="badge badge-green">平稳</span>';
      }
      html += `<div class="student-card" onclick="App.navigateTo('teacher/profile/${s.student_id}')">
        <div class="name">${escapeHtml(s.name)} <span style="font-size:12px;color:var(--mo-lighter);">${escapeHtml(s.student_id)}</span></div>
        <div class="meta">${escapeHtml(s.class_name)} · ${escapeHtml(s.gender)} · ${s.age}岁</div>
        <div class="tags">${emotionTag} ${statusBadge(status)}</div>
      </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
  };

  // ── 教师：学生画像 ──
  window.render_teacherProfile = async function (studentId) {
    const container = el('page-teacherProfile');
    if (!container) return;

    if (!studentId || studentId === 'profile') {
      container.innerHTML = '<div class="page-title">📋 学生画像</div><p style="color:var(--mo-lighter);">请从学生列表中选择一名学生查看画像。</p>';
      return;
    }

    const report = await API.getStudentProfileReport(studentId);
    if (!report || report.error) {
      container.innerHTML = '<div class="page-title">📋 学生画像</div><p style="color:var(--zhu-sha);">加载失败</p>';
      return;
    }

    const p = report.profile;
    let html = `<div class="page-title">📋 学生画像 — ${escapeHtml(report.name)} <span style="font-size:14px;color:var(--mo-lighter);">${escapeHtml(studentId)}</span></div>`;

    // 基本信息
    html += '<div class="card"><div class="card-header">基本信息</div><div class="report-section">';
    html += `<div class="report-field"><span class="field-label">姓名</span><span class="field-value">${escapeHtml(report.name)}</span></div>`;
    html += `<div class="report-field"><span class="field-label">班级</span><span class="field-value">${escapeHtml(report.class_name)}</span></div>`;
    if (p) {
      html += `<div class="report-field"><span class="field-label">总会话数</span><span class="field-value">${p.total_sessions} 次</span></div>`;
      html += `<div class="report-field"><span class="field-label">总消息数</span><span class="field-value">${p.total_messages} 条</span></div>`;
      html += `<div class="report-field"><span class="field-label">首次互动</span><span class="field-value">${formatDate(p.first_interaction_at)}</span></div>`;
      html += `<div class="report-field"><span class="field-label">最近互动</span><span class="field-value">${formatDate(p.last_interaction_at)}</span></div>`;
    }
    html += '</div></div>';

    // 学业分析
    html += '<div class="card"><div class="card-header">📊 学业分析</div>';
    if (report.scores && report.scores.length > 0) {
      html += renderLineChart(report.scores, 500, 180);
    }
    if (report.cognition && report.cognition.length > 0) {
      html += '<div style="margin-top:12px;">';
      report.cognition.filter(c => c.relation === '偏科').forEach(c => {
        html += `<div class="report-field"><span class="field-label">${c.relation}·${c.target}</span><span class="field-value">${escapeHtml(c.level || '')} (置信度: ${(c.confidence * 100).toFixed(0)}%)</span></div>`;
      });
      html += '</div>';
    }
    html += '</div>';

    // 心理状态
    html += '<div class="card"><div class="card-header">🧠 心理状态 (L2 认知)</div>';
    if (report.cognition && report.cognition.length > 0) {
      html += '<div class="report-section">';
      report.cognition.forEach(c => {
        const trendIcon = c.trend === '下降' ? '📉' : c.trend === '上升' ? '📈' : '➡️';
        html += `<div class="report-field"><span class="field-label">${c.relation}·${c.target}</span><span class="field-value">${trendIcon} ${escapeHtml(c.level || c.valence || '')} (C: ${(c.confidence * 100).toFixed(0)}%)</span></div>`;
      });
      html += '</div>';
    } else { html += '<p style="color:var(--mo-lighter);">暂无L2认知数据</p>'; }
    html += '</div>';

    // 风险评估
    html += '<div class="card"><div class="card-header">🛡️ 风险评估</div>';
    if (p) {
      html += `<div class="report-field"><span class="field-label">安全状态</span><span class="field-value">${statusBadge(p.safety_status)}</span></div>`;
      html += `<div class="report-field"><span class="field-label">账号状态</span><span class="field-value">${statusBadge(p.account_status)}</span></div>`;
      html += `<div class="report-field"><span class="field-label">B1违规(政治敏感)</span><span class="field-value" style="color:${p.violation_b1_count > 0 ? 'var(--zhu-sha)' : 'var(--jade)'};">${p.violation_b1_count} 次 ${p.violation_b1_count > 0 ? '⚠️ 永久记录' : ''}</span></div>`;
      html += `<div class="report-field"><span class="field-label">B2违规(粗鄙语言)</span><span class="field-value" style="color:${p.violation_b2_count >= 3 ? 'var(--zhu-sha)' : 'var(--mo-se)'};">${p.violation_b2_count} 次 (7天滑动窗口)</span></div>`;
    }
    html += '</div>';

    // L3 最近快照
    if (report.recent_memories && report.recent_memories.length > 0) {
      html += '<div class="card"><div class="card-header">📸 最近 L3 情景快照</div>';
      report.recent_memories.forEach(m => {
        html += `<div class="result-item"><div class="result-title" style="color:${emotionColor(m.emotion_primary)};">${emotionLabel(m.emotion_primary)} · ${escapeHtml(m.topic || '')}</div><div class="result-content">${escapeHtml(m.summary)}</div><div class="result-meta">${formatDate(m.timestamp)} · 重要性: ${(m.importance * 100).toFixed(0)}%</div></div>`;
      });
      html += '</div>';
    }

    // 综合报告
    html += `<div class="card"><div class="card-header">📝 综合报告</div><p style="line-height:1.8;">${escapeHtml(report.report_text || '暂无报告')}</p></div>`;

    container.innerHTML = html;
  };

  // ── 教师：危机预警 ──
  window.render_teacherAlerts = async function () {
    const container = el('page-teacherAlerts');
    if (!container) return;
    const alerts = await API.getCrisisAlerts();
    let html = '<div class="page-title">🔔 危机预警</div>';
    if (!alerts || alerts.length === 0) {
      html += '<p style="color:var(--mo-lighter);text-align:center;padding:40px;">✅ 当前无待处理预警</p>';
    } else {
      alerts.forEach(a => {
        html += `<div class="alert-card ${a.severity === 'urgent' ? '' : 'warning'}">
          <div class="alert-header">
            <span class="alert-student">${escapeHtml(a.student_name || a.student_id)} ${a.severity === 'urgent' ? '⚠️ 紧急' : '⚡ 预警'}</span>
            <span class="alert-time">${formatDateTime(a.triggered_at)}</span>
          </div>
          <div class="alert-summary">${escapeHtml(a.summary)}</div>
          <div class="alert-status">${statusBadge(a.status)}</div>
        </div>`;
      });
    }
    container.innerHTML = html;
  };

  // ── 教师：班级统计 ──
  window.render_teacherStats = async function () {
    const container = el('page-teacherStats');
    if (!container) return;
    const stats = await API.getClassStats('初二3班');
    let html = '<div class="page-title">📊 班级统计 — 初二3班</div>';
    html += `<div class="card"><div class="card-header">📈 情绪分布</div>`;
    html += renderBarChart(stats.distributions || {}, 500, 220);
    html += '</div>';
    html += `<div class="card"><div class="card-header">📝 综合报告</div><p style="line-height:1.8;">${escapeHtml(stats.report_text || '暂无')}</p></div>`;
    if (stats.student_count < 5) {
      html += '<div class="card" style="border-color:var(--gold);"><p style="color:var(--gold);text-align:center;">⚠️ 样本量不足5人，部分数据已隐藏以保护隐私</p></div>';
    }
    container.innerHTML = html;
  };

  // ── 管理员：账号管控 ──
  window.render_adminAccounts = async function () {
    const container = el('page-adminAccounts');
    if (!container) return;
    const students = await API.getStudents({});
    const profiles = window.MOCK_DATA.studentProfiles;
    let html = '<div class="page-title">🔒 账号管控</div><div class="table-wrap"><table>';
    html += '<thead><tr><th>学号</th><th>姓名</th><th>班级</th><th>账号状态</th><th>安全状态</th><th>B1违规</th><th>B2违规</th><th>操作</th></tr></thead><tbody>';
    students.forEach(s => {
      const p = profiles[s.student_id] || {};
      html += `<tr>
        <td>${escapeHtml(s.student_id)}</td>
        <td>${escapeHtml(s.name)}</td>
        <td>${escapeHtml(s.class_name)}</td>
        <td>${statusBadge(p.account_status || 'normal')}</td>
        <td>${statusBadge(p.safety_status || 'normal')}</td>
        <td>${p.violation_b1_count || 0}</td>
        <td>${p.violation_b2_count || 0}</td>
        <td>
          <button class="btn btn-sm btn-outline" onclick="App.blockUser('${s.student_id}')">${(p.account_status === 'blocked') ? '解封' : '封禁'}</button>
          <button class="btn btn-sm btn-outline" onclick="App.resetViolations('${s.student_id}')">重置违规</button>
        </td>
      </tr>`;
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
  };

  // ── 管理员：安全日志 ──
  window.render_adminSecurity = async function () {
    const container = el('page-adminSecurity');
    if (!container) return;
    let html = '<div class="page-title">🛡️ 安全日志</div>';

    const allLogs = [];
    const logs1 = await API.getSecurityLogs('XH_2024001');
    const logs2 = await API.getSecurityLogs('XH_2024002');
    allLogs.push(...(logs1 || []).map(l => ({ ...l, student_name: '小红' })));
    allLogs.push(...(logs2 || []).map(l => ({ ...l, student_name: '小明' })));

    html += '<div class="table-wrap"><table><thead><tr><th>时间</th><th>学生</th><th>类别</th><th>级别</th><th>触发方式</th><th>处理</th><th>脱敏摘要</th></tr></thead><tbody>';
    allLogs.forEach(l => {
      const catLabels = { political: 'B1政治', vulgar: 'B2粗鄙', injection: 'C注入', psych_crisis: 'A心理危机' };
      html += `<tr>
        <td>${formatDateTime(l.created_at)}</td>
        <td>${escapeHtml(l.student_name)}</td>
        <td><span class="badge ${l.category === 'political' ? 'badge-red' : l.category === 'vulgar' ? 'badge-orange' : 'badge-purple'}">${catLabels[l.category] || l.category}</span></td>
        <td>Level ${l.risk_level}</td>
        <td>${l.trigger_type === 'keyword' ? '关键词' : 'LLM语义'}</td>
        <td>${escapeHtml(l.escalation)}</td>
        <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(l.anonymized_summary || '')}</td>
      </tr>`;
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
  };

  // ── 管理员：知识库 ──
  window.render_adminKnowledge = async function () {
    const container = el('page-adminKnowledge');
    if (!container) return;
    const scenes = API.getHLMMScenes();
    let html = '<div class="page-title">📚 红楼梦知识库 (L0 角色本体)</div>';
    html += '<div style="margin-bottom:16px;"><button class="btn btn-gold btn-sm" onclick="App.showAddScene()">+ 添加场景</button></div>';
    html += '<div class="knowledge-grid">';
    scenes.forEach(s => {
      html += `<div class="knowledge-card">
        <div class="scene-name">📖 ${escapeHtml(s.scene_name)} <span style="font-size:12px;color:var(--mo-lighter);">第${s.chapter}回</span></div>
        <div class="tags">${(s.emotion_tags || []).map(t => `<span class="badge badge-purple">${t}</span>`).join(' ')}</div>
        <div class="key-quote">「${escapeHtml(s.key_quote)}」</div>
        <div style="font-size:13px;color:var(--mo-light);margin-top:8px;">${escapeHtml(s.scene_summary)}</div>
        <div class="tags" style="margin-top:4px;">${(s.characters || []).map(c => `<span class="badge badge-blue">${c}</span>`).join(' ')}</div>
      </div>`;
    });
    html += '</div>';
    container.innerHTML = html;
  };

  // ── 管理员：系统配置 ──
  window.render_adminConfig = async function () {
    const container = el('page-adminConfig');
    if (!container) return;
    const config = API.getConfig();
    let html = '<div class="page-title">⚙️ 系统配置</div><div class="config-grid">';
    Object.entries(config).forEach(([k, v]) => {
      const label = { decay_lambda: '衰减率 λ', hot_retrieval_top_k: 'Hot检索 Top-K', reranker_top_k: 'Reranker Top-K', sliding_window_size: '滑动窗口大小', summary_max_length: '摘要最大长度', reflection_threshold_count: 'Reflection 触发计数', reflection_threshold_days: 'Reflection 触发天数', cold_hot_days: 'Cold热归档天数', cold_warm_days: 'Cold温归档天数', b2_sliding_window_days: 'B2滑动窗口天数', b2_decay_hours: 'B2衰减间隔(小时)', crisis_alert_timeout_minutes: '危机通知超时(分钟)', embedding_model: '向量化模型', embedding_dim: '向量维度', llm_model: 'LLM主模型', llm_haiku: 'LLM轻量模型' }[k] || k;
      html += `<div class="config-item"><span class="key">${label}</span><span class="val">${Array.isArray(v) ? v.join(', ') : v}</span></div>`;
    });
    html += '</div>';
    container.innerHTML = html;
  };

  // ── CRUD：学生 ──
  window.render_crudStudents = async function () {
    const container = el('page-crudStudents');
    if (!container) return;
    const students = await API.getStudents({});
    let html = '<div class="page-title">📝 学生管理</div>';
    html += '<div style="margin-bottom:16px;"><button class="btn btn-primary btn-sm" onclick="App.showStudentForm()">+ 新增学生</button></div>';
    html += '<div class="table-wrap"><table><thead><tr><th>学号</th><th>姓名</th><th>班级</th><th>性别</th><th>年龄</th><th>籍贯</th><th>学历</th><th>操作</th></tr></thead><tbody>';
    students.forEach(s => {
      html += `<tr>
        <td>${escapeHtml(s.student_id)}</td><td>${escapeHtml(s.name)}</td><td>${escapeHtml(s.class_name)}</td>
        <td>${s.gender}</td><td>${s.age}</td><td>${escapeHtml(s.hometown || '')}</td><td>${escapeHtml(s.education || '')}</td>
        <td>
          <button class="btn btn-sm btn-outline" onclick="App.editStudent('${s.student_id}')">编辑</button>
          <button class="btn btn-sm btn-danger" onclick="App.deleteStudentConfirm('${s.student_id}')">删除</button>
        </td>
      </tr>`;
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
  };

  // ── CRUD：成绩 ──
  window.render_crudScores = async function () {
    const container = el('page-crudScores');
    if (!container) return;
    const students = await API.getStudents({});
    let html = '<div class="page-title">📐 成绩管理</div>';
    html += '<div style="margin-bottom:16px;"><button class="btn btn-primary btn-sm" onclick="App.showScoreForm()">+ 录入成绩</button></div>';
    html += '<div style="margin-bottom:12px;"><select class="form-select" id="scoreStudentFilter" style="width:200px;" onchange="App.filterScores()"><option value="">选择学生...</option>';
    students.forEach(s => { html += `<option value="${s.student_id}">${escapeHtml(s.name)} (${escapeHtml(s.student_id)})</option>`; });
    html += '</select></div><div id="scoreTableArea"><p style="color:var(--mo-lighter);">请选择学生查看成绩</p></div>';
    container.innerHTML = html;
  };

  async function filterScores() {
    const stuId = el('scoreStudentFilter')?.value;
    const area = el('scoreTableArea');
    if (!stuId || !area) { area && (area.innerHTML = '<p style="color:var(--mo-lighter);">请选择学生</p>'); return; }
    const scores = await API.getScores(stuId);
    let html = '<div class="table-wrap"><table><thead><tr><th>考核序次</th><th>成绩</th><th>日期</th><th>操作</th></tr></thead><tbody>';
    (scores || []).forEach(s => {
      html += `<tr><td>第${s.exam_sequence}次</td><td>${s.score}分</td><td>${formatDate(s.created_at)}</td>
        <td><button class="btn btn-sm btn-outline" onclick="App.editScore(${s.id},'${s.student_id}',${s.exam_sequence},${s.score})">编辑</button>
        <button class="btn btn-sm btn-danger" onclick="App.deleteScoreConfirm('${s.student_id}',${s.exam_sequence})">删除</button></td></tr>`;
    });
    html += '</tbody></table></div>';
    area.innerHTML = html;
  }

  // ── CRUD：就业 ──
  window.render_crudEmployment = async function () {
    const container = el('page-crudEmployment');
    if (!container) return;
    const students = await API.getStudents({});
    const allEmp = {};
    for (const s of students) {
      const emp = await API.getEmployment(s.student_id);
      if (emp) allEmp[s.student_id] = emp;
    }
    let html = '<div class="page-title">💼 就业管理</div>';
    html += '<div class="table-wrap"><table><thead><tr><th>学号</th><th>姓名</th><th>班级</th><th>公司</th><th>薪资</th><th>就业开放</th><th>Offer时间</th><th>操作</th></tr></thead><tbody>';
    students.forEach(s => {
      const emp = allEmp[s.student_id];
      html += `<tr>
        <td>${escapeHtml(s.student_id)}</td><td>${escapeHtml(s.name)}</td><td>${escapeHtml(s.class_name)}</td>
        <td>${escapeHtml(emp?.company_name || '-')}</td><td>${emp?.salary ? '¥' + emp.salary : '-'}</td>
        <td>${formatDate(emp?.employment_open_time)}</td><td>${formatDate(emp?.offer_time)}</td>
        <td><button class="btn btn-sm btn-outline" onclick="App.editEmployment('${s.student_id}')">编辑</button></td>
      </tr>`;
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
  };

  // ── CRUD：班级 ──
  window.render_crudClasses = async function () {
    const container = el('page-crudClasses');
    if (!container) return;
    const classes = await API.getClasses();
    let html = '<div class="page-title">🏫 班级管理</div>';
    html += '<div style="margin-bottom:16px;"><button class="btn btn-primary btn-sm" onclick="App.showClassForm()">+ 新增班级</button></div>';
    html += '<div class="table-wrap"><table><thead><tr><th>班级名</th><th>年级</th><th>开课时间</th><th>班主任</th><th>辅导员</th><th>操作</th></tr></thead><tbody>';
    (classes || []).forEach(c => {
      html += `<tr><td>${escapeHtml(c.class_name)}</td><td>${escapeHtml(c.grade)}</td><td>${formatDate(c.start_time)}</td><td>${escapeHtml(c.head_teacher)}</td><td>${escapeHtml(c.instructor)}</td>
        <td><button class="btn btn-sm btn-outline" onclick="App.editClass('${escapeHtml(c.class_name)}')">编辑</button>
        <button class="btn btn-sm btn-danger" onclick="App.deleteClassConfirm('${escapeHtml(c.class_name)}')">删除</button></td></tr>`;
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
  };

  // ── CRUD：教师 ──
  window.render_crudTeachers = async function () {
    const container = el('page-crudTeachers');
    if (!container) return;
    const teachers = await API.getTeachers();
    let html = '<div class="page-title">👨‍🏫 教师管理</div>';
    html += '<div style="margin-bottom:16px;"><button class="btn btn-primary btn-sm" onclick="App.showTeacherForm()">+ 新增教师</button></div>';
    html += '<div class="table-wrap"><table><thead><tr><th>教师ID</th><th>姓名</th><th>部门</th><th>职称</th><th>电话</th><th>操作</th></tr></thead><tbody>';
    (teachers || []).forEach(t => {
      html += `<tr><td>${escapeHtml(t.teacher_id)}</td><td>${escapeHtml(t.name)}</td><td>${escapeHtml(t.department || '')}</td><td>${escapeHtml(t.title || '')}</td><td>${escapeHtml(t.phone || '')}</td>
        <td><button class="btn btn-sm btn-outline" onclick="App.editTeacher('${escapeHtml(t.teacher_id)}')">编辑</button>
        <button class="btn btn-sm btn-danger" onclick="App.deleteTeacherConfirm('${escapeHtml(t.teacher_id)}')">删除</button></td></tr>`;
    });
    html += '</tbody></table></div>';
    container.innerHTML = html;
  };

  // ── 统计 ──
  window.render_statistics = async function () {
    const container = el('page-statistics');
    if (!container) return;

    const [older30, gender, high80, fails, examAvg, topSal, durations, classAvg] = await Promise.all([
      API.getStatistics('older-than-30'), API.getStatistics('gender-count'),
      API.getStatistics('always-above-80'), API.getStatistics('failures'),
      API.getStatistics('exam-avg'), API.getStatistics('top-salary'),
      API.getStatistics('duration-per-student'), API.getStatistics('avg-duration-by-class')
    ]);

    let html = '<div class="page-title">📈 统计分析</div>';

    // 超30岁
    html += '<div class="card"><div class="card-header">👴 超过30岁学员</div><div class="table-wrap"><table><thead><tr><th>姓名</th><th>班级</th><th>年龄</th><th>性别</th></tr></thead><tbody>';
    (older30 || []).forEach(s => { html += `<tr><td>${escapeHtml(s.name)}</td><td>${escapeHtml(s.class_name)}</td><td>${s.age}岁</td><td>${s.gender}</td></tr>`; });
    html += '</tbody></table></div></div>';

    // 性别统计
    html += '<div class="card"><div class="card-header">👫 班级性别统计</div><div class="table-wrap"><table><thead><tr><th>班级</th><th>总人数</th><th>男生</th><th>女生</th></tr></thead><tbody>';
    (gender || []).forEach(g => { html += `<tr><td>${escapeHtml(g.class_name)}</td><td>${g.total}</td><td>${g.male}</td><td>${g.female}</td></tr>`; });
    html += '</tbody></table></div></div>';

    // 高分学生
    html += '<div class="card"><div class="card-header">🌟 每次考试80分以上</div><div class="table-wrap"><table><thead><tr><th>姓名</th><th>班级</th><th>平均分</th></tr></thead><tbody>';
    (high80 || []).forEach(s => { html += `<tr><td>${escapeHtml(s.name)}</td><td>${escapeHtml(s.class_name)}</td><td>${s.avg_score}分</td></tr>`; });
    html += '</tbody></table></div></div>';

    // 不及格
    html += '<div class="card"><div class="card-header">⚠️ 两次以上不及格</div><div class="table-wrap"><table><thead><tr><th>姓名</th><th>班级</th><th>不及格次数</th><th>不及格成绩</th></tr></thead><tbody>';
    (fails || []).forEach(s => { html += `<tr><td>${escapeHtml(s.name)}</td><td>${escapeHtml(s.class_name)}</td><td>${s.fail_count}次</td><td>${s.fail_scores}</td></tr>`; });
    html += '</tbody></table></div></div>';

    // 薪资TOP5
    html += '<div class="card"><div class="card-header">💰 就业薪资TOP5</div><div class="table-wrap"><table><thead><tr><th>姓名</th><th>班级</th><th>公司</th><th>薪资</th><th>Offer时间</th></tr></thead><tbody>';
    (topSal || []).forEach(s => { html += `<tr><td>${escapeHtml(s.name)}</td><td>${escapeHtml(s.class_name)}</td><td>${escapeHtml(s.company_name)}</td><td style="color:var(--zhu-sha);font-weight:600;">¥${s.salary}</td><td>${formatDate(s.offer_time)}</td></tr>`; });
    html += '</tbody></table></div></div>';

    // 就业时长
    html += '<div class="card"><div class="card-header">⏱️ 学生就业时长</div><div class="table-wrap"><table><thead><tr><th>姓名</th><th>班级</th><th>就业时长(天)</th></tr></thead><tbody>';
    (durations || []).forEach(s => { html += `<tr><td>${escapeHtml(s.name)}</td><td>${escapeHtml(s.class_name)}</td><td>${s.duration_days} 天</td></tr>`; });
    html += '</tbody></table></div></div>';

    // 班级平均就业时长
    html += '<div class="card"><div class="card-header">🏫 班级平均就业时长</div><div class="table-wrap"><table><thead><tr><th>班级</th><th>平均就业时长(天)</th></tr></thead><tbody>';
    (classAvg || []).forEach(s => { html += `<tr><td>${escapeHtml(s.class_name)}</td><td>${s.avg_duration_days} 天</td></tr>`; });
    html += '</tbody></table></div></div>';

    container.innerHTML = html;
  };

  // ── NL 自然语言查询 ──
  window.render_nlQuery = async function () {
    const resultDiv = el('nlQueryResult');
    const hintDiv = el('nlQueryHint');
    if (resultDiv) resultDiv.style.display = 'none';
    if (hintDiv) hintDiv.style.display = 'block';

    // 绑定查询事件
    const input = el('nlQueryInput');
    const btn = el('nlQueryBtn');
    if (!input || !btn) return;

    const doQuery = async () => {
      const q = input.value.trim();
      if (!q) return;

      // 显示加载状态
      if (resultDiv) resultDiv.style.display = 'block';
      if (hintDiv) hintDiv.style.display = 'none';
      if (resultDiv) {
        resultDiv.innerHTML = '<div class="card"><div style="text-align:center;padding:40px;color:var(--mo-lighter);">⏳ 正在分析查询并生成 SQL...</div></div>';
      }
      input.disabled = true; btn.disabled = true;

      try {
        const res = await API.nlQuery(q);
        renderNLResult(res);
      } catch (e) {
        if (resultDiv) {
          resultDiv.innerHTML = `<div class="card"><div style="text-align:center;padding:40px;color:var(--zhu-sha);">⚠️ 查询失败: ${escapeHtml(e.message)}</div></div>`;
        }
      }
      input.disabled = false; btn.disabled = false;
      input.focus();
    };

    btn.addEventListener('click', doQuery);
    input.addEventListener('keydown', e => { if (e.key === 'Enter') doQuery(); });

    // 快捷示例按钮
    document.querySelectorAll('.nl-example').forEach(b => {
      b.addEventListener('click', function () {
        const q = this.dataset.q;
        if (input) input.value = q;
        doQuery();
      });
    });
  };

  function renderNLResult(res) {
    const container = el('page-nlQuery');
    if (!container) return;

    let html = '';

    // SQL 展示
    const rowCountText = res.result_row_count != null ? `${res.result_row_count} 条结果` : '';
    const errorHtml = res.sql_error
      ? `<div style="color:var(--zhu-sha);padding:8px 16px;font-size:13px;">⚠️ SQL 校验/执行错误: ${escapeHtml(res.sql_error)}</div>`
      : '';

    html += `<div class="card" style="margin-bottom:16px;">
      <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
        <span>📝 生成的 SQL</span>
        <span style="font-size:13px;color:var(--mo-lighter);">${rowCountText}</span>
      </div>
      <pre style="background:var(--bg-card);border:1px solid var(--border-light);border-radius:8px;padding:12px 16px;font-size:13px;overflow-x:auto;white-space:pre-wrap;word-break:break-all;">${escapeHtml(res.sql || '')}</pre>
      ${errorHtml}
    </div>`;

    // 结果展示
    html += '<div class="card"><div class="card-header">📊 查询结果</div>';

    if (res.answer) {
      html += `<div style="padding:16px;line-height:1.8;font-size:14px;">${escapeHtml(res.answer).replace(/\n/g, '<br>')}</div>`;
    }

    // 原始数据表格
    if (res.result && res.result.length > 0) {
      html += '<div style="padding:0 16px 16px;overflow-x:auto;"><div class="table-wrap"><table><thead><tr>';
      const cols = Object.keys(res.result[0]);
      cols.forEach(c => { html += `<th>${escapeHtml(c)}</th>`; });
      html += '</tr></thead><tbody>';
      res.result.forEach(row => {
        html += '<tr>';
        cols.forEach(c => { html += `<td>${escapeHtml(String(row[c] ?? ''))}</td>`; });
        html += '</tr>';
      });
      html += '</tbody></table></div></div>';
    } else if (!res.sql_error) {
      html += '<div style="text-align:center;padding:40px;color:var(--mo-lighter);">没有匹配的数据</div>';
    }

    html += '</div>';

    // 更新 DOM
    const resultDiv = el('nlQueryResult');
    if (!resultDiv) {
      // fallback: 直接设置容器
      container.innerHTML = container.querySelector('.page-title')?.outerHTML + html;
      return;
    }
    resultDiv.innerHTML = html;
    resultDiv.style.display = 'block';
    const hintDiv = el('nlQueryHint');
    if (hintDiv) hintDiv.style.display = 'none';
  }

  // ── 架构可视化 ──
  window.render_architecture = async function () {
    const container = el('page-architecture');
    if (!container) return;

    let html = '<div class="page-title">🏗️ 系统架构可视化</div>';

    // 1. 四层记忆金字塔
    html += '<div class="viz-section"><h2>🗼 四层记忆金字塔</h2><div class="pyramid">';
    const layers = API.getMemoryLayers();
    layers.forEach((l, i) => {
      html += `<div class="pyramid-layer pyramid-l${3 - i}" onclick="this.classList.toggle('expanded')">
        <div><b>${l.level}</b> ${l.name}</div>
        <div class="storage">${l.storage}</div>
        <div class="detail">
          <p><b>数据量:</b> ${l.volume}</p>
          <p><b>存储内容:</b> ${l.content}</p>
          <p><b>生命周期:</b> ${l.lifecycle}</p>
          <p><b>检索方式:</b> ${l.retrieval}</p>
        </div>
      </div>`;
    });
    html += '</div></div>';

    // 2. LangGraph 流程图
    html += '<div class="viz-section"><h2>🔄 LangGraph 处理流程</h2><div class="card"><div class="graph-flow">';
    const nodes = API.getGraphNodes();
    nodes.forEach((n, i) => {
      html += `<div class="graph-node">
        <div class="graph-tooltip">${escapeHtml(n.description)}</div>
        <div class="node-category">${escapeHtml(n.category)}</div>
        <div class="node-name">${escapeHtml(n.name)}</div>
      </div>`;
      if (i < nodes.length - 1) {
        html += '<div class="graph-arrow">→</div>';
      }
      // 在安全过滤后展示分支
      if (i === 0) {
        html += '<div style="display:flex;flex-direction:column;align-items:center;margin-top:-24px;font-size:10px;color:var(--mo-lighter);">';
        html += '<span style="color:#F44336;">flagged → 直接生成安全回复</span>';
        html += '<span style="color:#4CAF50;">safe → 正常流程 ↓</span>';
        html += '</div>';
      }
    });
    html += '</div></div></div>';

    // 3. 三数据库分工
    html += '<div class="viz-section"><h2>🗄️ 三数据库分工</h2><div class="db-grid">';
    html += `<div class="db-card pg"><div class="db-name">🐘 PostgreSQL</div><div class="db-items"><ul>
      <li>📋 L1 业务事实（学籍/成绩/考勤）</li>
      <li>❄️ L3-Cold 原始对话归档</li>
      <li>📦 会话归档 & 学生档案</li>
      <li>🛡️ 安全日志 & 审计日志</li>
      <li>🔗 Thread-Session 映射</li>
      <li style="color:var(--mo-lighter);font-size:12px;">查询方式: SQL | 一致性: 强一致</li>
    </ul></div></div>`;
    html += `<div class="db-card milvus"><div class="db-name">🔷 Milvus</div><div class="db-items"><ul>
      <li>📸 L3-Hot 结构化情景摘要</li>
      <li>🏯 红楼梦名场面向量库</li>
      <li>🔍 ANN 向量检索 (HNSW)</li>
      <li>🏷️ 按 student_id 分区隔离</li>
      <li>📐 768维 bge-large-zh-v1.5</li>
      <li style="color:var(--mo-lighter);font-size:12px;">查询方式: ANN+过滤 | 一致性: 最终一致</li>
    </ul></div></div>`;
    html += `<div class="db-card neo4j"><div class="db-name">🕸️ Neo4j</div><div class="db-items"><ul>
      <li>🏯 L0 角色本体（红楼人物图）</li>
      <li>🧠 L2 语义认知（学生标签）</li>
      <li>💞 跨层关系（黛玉→学生关心边）</li>
      <li>📊 置信度动力学追踪</li>
      <li>🔄 定时衰减 & 冲突管理</li>
      <li style="color:var(--mo-lighter);font-size:12px;">查询方式: Cypher | 一致性: 强一致</li>
    </ul></div></div>`;
    html += '</div></div>';

    container.innerHTML = html;
  };

  // ═══════════════════════════════════════════════════════
  //  SVG 图表渲染
  // ═══════════════════════════════════════════════════════

  function renderLineChart(data, width, height) {
    if (!data || data.length === 0) return '<p style="color:var(--mo-lighter);text-align:center;">暂无数据</p>';
    const pad = { top: 20, right: 20, bottom: 30, left: 40 };
    const w = width - pad.left - pad.right;
    const h = height - pad.top - pad.bottom;

    const scores = data.map(d => d.score);
    const max = Math.max(...scores, 100);
    const min = Math.min(...scores, 0) - 5;
    const range = max - min;

    let points = data.map((d, i) => {
      const x = pad.left + (i / Math.max(data.length - 1, 1)) * w;
      const y = pad.top + h - ((d.score - min) / range) * h;
      return `${x},${y}`;
    }).join(' ');

    let yLabels = '';
    for (let i = 0; i <= 4; i++) {
      const val = min + (range / 4) * i;
      const y = pad.top + h - ((val - min) / range) * h;
      yLabels += `<text x="${pad.left - 6}" y="${y + 4}" text-anchor="end" font-size="10" fill="var(--mo-lighter)">${Math.round(val)}</text>`;
      yLabels += `<line x1="${pad.left}" y1="${y}" x2="${pad.left + w}" y2="${y}" stroke="var(--border-light)" stroke-dasharray="4,4"/>`;
    }

    return `<div class="chart-wrap"><svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
      ${yLabels}
      <polyline points="${points}" fill="none" stroke="var(--zhu-sha)" stroke-width="2" stroke-linejoin="round"/>
      ${data.map((d, i) => {
        const x = pad.left + (i / Math.max(data.length - 1, 1)) * w;
        const y = pad.top + h - ((d.score - min) / range) * h;
        return `<circle cx="${x}" cy="${y}" r="4" fill="var(--zhu-sha)"/><text x="${x}" y="${y - 10}" text-anchor="middle" font-size="11" fill="var(--mo-se)">${d.score}分</text><text x="${x}" y="${pad.top + h + 18}" text-anchor="middle" font-size="10" fill="var(--mo-lighter)">第${d.exam_sequence}次</text>`;
      }).join('')}
    </svg></div>`;
  }

  function renderBarChart(dist, width, height) {
    const entries = Object.entries(dist);
    if (entries.length === 0) return '<p style="color:var(--mo-lighter);text-align:center;">暂无数据</p>';

    const pad = { top: 10, right: 20, bottom: 40, left: 20 };
    const w = width - pad.left - pad.right;
    const h = height - pad.top - pad.bottom;
    const barW = Math.min(60, w / entries.length - 8);
    const max = Math.max(...entries.map(e => e[1]), 1);
    const colors = ['#C23531', '#E65100', '#F57F17', '#2E7D32', '#1565C0', '#6A1B9A', '#4A7B9D'];

    return `<div class="chart-wrap"><svg width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
      ${entries.map((e, i) => {
        const x = pad.left + i * (w / entries.length) + (w / entries.length - barW) / 2;
        const barH = (e[1] / max) * h;
        const y = pad.top + h - barH;
        return `<rect x="${x}" y="${y}" width="${barW}" height="${barH}" rx="4" fill="${colors[i % colors.length]}" class="bar"/><text x="${x + barW / 2}" y="${y - 6}" text-anchor="middle" font-size="12" fill="var(--mo-se)" font-weight="600">${e[1]}</text><text x="${x + barW / 2}" y="${pad.top + h + 18}" text-anchor="middle" font-size="11" fill="var(--mo-light)">${escapeHtml(e[0])}</text>`;
      }).join('')}
    </svg></div>`;
  }

  // ═══════════════════════════════════════════════════════
  //  CRUD 操作：弹窗
  // ═══════════════════════════════════════════════════════

  async function showStudentForm(existing) {
    const title = existing ? '编辑学生' : '新增学生';
    const data = existing || {};
    const formHtml = `<form id="studentForm">
      <div class="form-row"><div class="form-group"><label class="form-label">学号 *</label><input class="form-input" name="student_id" value="${escapeHtml(data.student_id || '')}" ${existing ? 'readonly' : ''}></div>
      <div class="form-group"><label class="form-label">姓名 *</label><input class="form-input" name="name" value="${escapeHtml(data.name || '')}"></div></div>
      <div class="form-row"><div class="form-group"><label class="form-label">班级 *</label><input class="form-input" name="class_name" value="${escapeHtml(data.class_name || '')}"></div>
      <div class="form-group"><label class="form-label">性别</label><select class="form-select" name="gender"><option value="男" ${data.gender === '男' ? 'selected' : ''}>男</option><option value="女" ${data.gender === '女' ? 'selected' : ''}>女</option></select></div></div>
      <div class="form-row"><div class="form-group"><label class="form-label">年龄</label><input class="form-input" name="age" type="number" value="${data.age || ''}"></div>
      <div class="form-group"><label class="form-label">籍贯</label><input class="form-input" name="hometown" value="${escapeHtml(data.hometown || '')}"></div></div>
      <div class="form-row"><div class="form-group"><label class="form-label">学历</label><input class="form-input" name="education" value="${escapeHtml(data.education || '')}"></div>
      <div class="form-group"><label class="form-label">专业</label><input class="form-input" name="major" value="${escapeHtml(data.major || '')}"></div></div>
    </form>`;

    openModal(title, formHtml, async () => {
      const formData = getFormData('studentForm');
      if (!formData.student_id || !formData.name || !formData.class_name) { showToast('请填写必填字段', 'error'); return; }
      if (existing) {
        await API.updateStudent(existing.student_id, formData);
      } else {
        await API.createStudent(formData);
      }
      closeModal();
      showToast(existing ? '更新成功' : '创建成功', 'success');
      handleRoute();
    });
  }

  function showScoreForm(existing) {
    const title = existing ? '编辑成绩' : '录入成绩';
    const data = existing || {};
    const formHtml = `<form id="scoreForm">
      <div class="form-row"><div class="form-group"><label class="form-label">学号 *</label><input class="form-input" name="student_id" value="${escapeHtml(data.student_id || '')}" ${existing ? 'readonly' : ''}></div>
      <div class="form-group"><label class="form-label">考核序次 *</label><input class="form-input" name="exam_sequence" type="number" value="${data.exam_sequence || ''}" ${existing ? 'readonly' : ''}></div></div>
      <div class="form-group"><label class="form-label">成绩 *</label><input class="form-input" name="score" type="number" step="0.1" value="${data.score || ''}"></div>
    </form>`;
    openModal(title, formHtml, async () => {
      const formData = getFormData('scoreForm');
      if (!formData.student_id || !formData.exam_sequence || !formData.score) { showToast('请填写必填字段', 'error'); return; }
      formData.exam_sequence = parseInt(formData.exam_sequence);
      formData.score = parseFloat(formData.score);
      if (existing) {
        await API.updateScore(formData);
      } else {
        await API.createScore(formData);
      }
      closeModal();
      showToast(existing ? '更新成功' : '录入成功', 'success');
      handleRoute();
    });
  }

  function showEmploymentForm(studentId, existing) {
    const data = existing || {};
    const formHtml = `<form id="employmentForm">
      <div class="form-group"><label class="form-label">公司名称</label><input class="form-input" name="company_name" value="${escapeHtml(data.company_name || '')}"></div>
      <div class="form-row"><div class="form-group"><label class="form-label">薪资</label><input class="form-input" name="salary" type="number" value="${data.salary || ''}"></div>
      <div class="form-group"><label class="form-label">就业开放时间</label><input class="form-input" name="employment_open_time" type="date" value="${data.employment_open_time || ''}"></div></div>
      <div class="form-group"><label class="form-label">Offer下发时间</label><input class="form-input" name="offer_time" type="date" value="${data.offer_time || ''}"></div>
    </form>`;
    openModal('编辑就业信息', formHtml, async () => {
      const formData = getFormData('employmentForm');
      if (formData.salary) formData.salary = parseInt(formData.salary);
      await API.upsertEmployment(studentId, formData);
      closeModal();
      showToast('保存成功', 'success');
      handleRoute();
    });
  }

  function showClassForm(existing) {
    const data = existing || {};
    const formHtml = `<form id="classForm">
      <div class="form-group"><label class="form-label">班级名 *</label><input class="form-input" name="class_name" value="${escapeHtml(data.class_name || '')}" ${existing ? 'readonly' : ''}></div>
      <div class="form-row"><div class="form-group"><label class="form-label">年级</label><input class="form-input" name="grade" value="${escapeHtml(data.grade || '')}"></div>
      <div class="form-group"><label class="form-label">开课时间</label><input class="form-input" name="start_time" type="date" value="${data.start_time || ''}"></div></div>
      <div class="form-row"><div class="form-group"><label class="form-label">班主任</label><input class="form-input" name="head_teacher" value="${escapeHtml(data.head_teacher || '')}"></div>
      <div class="form-group"><label class="form-label">辅导员</label><input class="form-input" name="instructor" value="${escapeHtml(data.instructor || '')}"></div></div>
    </form>`;
    openModal(existing ? '编辑班级' : '新增班级', formHtml, async () => {
      const formData = getFormData('classForm');
      if (!formData.class_name) { showToast('请填写班级名', 'error'); return; }
      if (existing) {
        await API.updateClass(existing.class_name, formData);
      } else {
        await API.createClass(formData);
      }
      closeModal();
      showToast(existing ? '更新成功' : '创建成功', 'success');
      handleRoute();
    });
  }

  function showTeacherForm(existing) {
    const data = existing || {};
    const formHtml = `<form id="teacherForm">
      <div class="form-group"><label class="form-label">教师ID *</label><input class="form-input" name="teacher_id" value="${escapeHtml(data.teacher_id || '')}" ${existing ? 'readonly' : ''}></div>
      <div class="form-group"><label class="form-label">姓名 *</label><input class="form-input" name="name" value="${escapeHtml(data.name || '')}"></div>
      <div class="form-row"><div class="form-group"><label class="form-label">部门</label><input class="form-input" name="department" value="${escapeHtml(data.department || '')}"></div>
      <div class="form-group"><label class="form-label">职称</label><input class="form-input" name="title" value="${escapeHtml(data.title || '')}"></div></div>
      <div class="form-group"><label class="form-label">电话</label><input class="form-input" name="phone" value="${escapeHtml(data.phone || '')}"></div>
    </form>`;
    openModal(existing ? '编辑教师' : '新增教师', formHtml, async () => {
      const formData = getFormData('teacherForm');
      if (!formData.teacher_id || !formData.name) { showToast('请填写必填字段', 'error'); return; }
      if (existing) {
        await API.updateTeacher(existing.teacher_id, formData);
      } else {
        await API.createTeacher(formData);
      }
      closeModal();
      showToast(existing ? '更新成功' : '创建成功', 'success');
      handleRoute();
    });
  }

  // ── 确认删除 ──
  async function deleteStudentConfirm(id) {
    if (!confirm(`确定删除学生 ${id} 吗？`)) return;
    await API.deleteStudent(id);
    showToast('删除成功', 'success');
    handleRoute();
  }

  async function deleteScoreConfirm(stuId, seq) {
    if (!confirm(`确定删除第${seq}次考试成绩吗？`)) return;
    await API.deleteScore({ student_id: stuId, exam_sequence: seq });
    showToast('删除成功', 'success');
    handleRoute();
  }

  async function deleteClassConfirm(name) {
    if (!confirm(`确定删除班级 ${name} 吗？`)) return;
    await API.deleteClass(name);
    showToast('删除成功', 'success');
    handleRoute();
  }

  async function deleteTeacherConfirm(id) {
    if (!confirm(`确定删除教师 ${id} 吗？`)) return;
    await API.deleteTeacher(id);
    showToast('删除成功', 'success');
    handleRoute();
  }

  // ── 管理员操作 ──
  async function blockUser(id) {
    const profile = window.MOCK_DATA.studentProfiles[id];
    const isBlocked = profile && profile.account_status === 'blocked';
    const action = isBlocked ? 'unblock' : 'block';
    const reason = prompt(isBlocked ? '解封原因：' : '封禁原因：');
    if (!reason) return;
    await API.accountControl({ student_id: id, action, reason });
    showToast(isBlocked ? '已解封' : '已封禁', 'success');
    handleRoute();
  }

  async function resetViolations(id) {
    if (!confirm(`确定重置学生 ${id} 的违规计数吗？`)) return;
    await API.accountControl({ student_id: id, action: 'reset_violation', reason: '管理员手动重置' });
    showToast('违规计数已重置', 'success');
    handleRoute();
  }

  function showAddScene() {
    const formHtml = `<form id="sceneForm">
      <div class="form-group"><label class="form-label">场景名</label><input class="form-input" name="scene_name"></div>
      <div class="form-row"><div class="form-group"><label class="form-label">章节</label><input class="form-input" name="chapter" type="number"></div>
      <div class="form-group"><label class="form-label">情绪标签</label><input class="form-input" name="emotion_tag"></div></div>
      <div class="form-group"><label class="form-label">核心台词</label><textarea class="form-textarea" name="key_quote"></textarea></div>
      <div class="form-group"><label class="form-label">场景简述</label><textarea class="form-textarea" name="scene_summary"></textarea></div>
    </form>`;
    openModal('添加红楼场景', formHtml, async () => {
      const formData = getFormData('sceneForm');
      await API.knowledgeManage('add', formData);
      closeModal();
      showToast('添加成功', 'success');
      handleRoute();
    });
  }

  // ── 导航辅助 ──
  function navigateTo(hash) {
    navigate(hash);
  }

  // ═══════════════════════════════════════════════════════
  //  公开API
  // ═══════════════════════════════════════════════════════

  return {
    init,
    navigateTo,
    // CRUD弹窗
    showStudentForm: () => showStudentForm(),
    editStudent: async (id) => { const s = await API.getStudent(id); showStudentForm(s); },
    showScoreForm: () => showScoreForm(),
    editScore: (id, stuId, seq, score) => showScoreForm({ id, student_id: stuId, exam_sequence: seq, score }),
    editEmployment: async (id) => { const e = await API.getEmployment(id); showEmploymentForm(id, e); },
    showClassForm: () => showClassForm(),
    editClass: async (name) => { const c = (await API.getClasses()).find(x => x.class_name === name); showClassForm(c); },
    showTeacherForm: () => showTeacherForm(),
    editTeacher: async (id) => { const t = (await API.getTeachers()).find(x => x.teacher_id === id); showTeacherForm(t); },
    // 删除
    deleteStudentConfirm, deleteScoreConfirm, deleteClassConfirm, deleteTeacherConfirm,
    // 管理员
    blockUser, resetViolations, showAddScene,
    // 成绩筛选
    filterScores,
    // 图表
    renderLineChart, renderBarChart
  };
})();

window.App = App;
window.filterScores = () => App.filterScores();

// 启动
document.addEventListener('DOMContentLoaded', () => App.init());
