// ============================================================
// 林黛玉 Agent 学生管理系统 — API 服务层
// 支持 Mock 模拟数据 / 真实后端 API 双模式切换
// ============================================================

const API = (function () {
  const STORAGE_KEY = 'api_mode';
  const TOKEN_KEY = 'auth_token';
  const USER_KEY = 'auth_user';
  let _mode = localStorage.getItem(STORAGE_KEY) || 'mock';
  const BASE_URL = 'http://localhost:8000';

  function getMode() {
    return _mode;
  }

  function setMode(mode) {
    _mode = mode;
    localStorage.setItem(STORAGE_KEY, mode);
  }

  function isMock() {
    return _mode === 'mock';
  }

  // ── Token 管理 ──

  function getToken() {
    return localStorage.getItem(TOKEN_KEY);
  }

  function setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  }

  function clearToken() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }

  function getSavedUser() {
    try {
      return JSON.parse(localStorage.getItem(USER_KEY));
    } catch { return null; }
  }

  function saveUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }

  // 通用 fetch 封装（自动带 Authorization header）
  async function _fetch(url, options = {}) {
    if (isMock()) return null;
    const token = getToken();
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (token) {
      headers['Authorization'] = 'Bearer ' + token;
    }
    try {
      const res = await fetch(BASE_URL + url, {
        headers,
      });
      if (!res.ok) {
        const err = await res.text();
        throw new Error(`HTTP ${res.status}: ${err}`);
      }
      return res.json();
    } catch (e) {
      console.warn('[API] 请求失败:', e.message);
      return { error: e.message };
    }
  }

  function _delay(ms) {
    return new Promise(r => setTimeout(r, ms));
  }

  // 模拟网络延迟
  async function _mock(resultOrFn) {
    await _delay(150 + Math.random() * 200);
    if (typeof resultOrFn === 'function') return resultOrFn();
    if (resultOrFn === undefined || resultOrFn === null) return null;
    return JSON.parse(JSON.stringify(resultOrFn)); // deep clone
  }

  const M = () => window.MOCK_DATA;

  // ==================== 公共 ====================

  async function healthCheck() {
    if (isMock()) return _mock({ status: 'ok' });
    return _fetch('/health');
  }

  // ==================== 聊天 ====================

  async function sendChat(message) {
    if (isMock()) {
      return _mock(() => {
        const m = M();
        // 根据消息内容匹配场景
        let scenario;
        if (message.includes('成绩') || message.includes('分数') || message.includes('考了多少')) {
          scenario = m.chatScenarios.academic_query;
        } else if (message.includes('不想活') || message.includes('活着好累') || message.includes('死了')) {
          scenario = m.chatScenarios.psych_crisis;
        } else if (message.includes('敏感') || message.includes('政治')) {
          scenario = m.chatScenarios.safety_b1;
        } else if (message.includes('脏话') || message.includes('粗鄙')) {
          scenario = m.chatScenarios.safety_b2;
        } else {
          scenario = m.chatScenarios.daiyu_chat;
        }
        return {
          reply: scenario.agentReply,
          intent: scenario.intent,
          safety_flag: scenario.safetyFlag || null,
          memory_context: scenario.memoryContext,
          fact_data: scenario.factData
        };
      });
    }
    return _fetch('/chat/send', {
      method: 'POST',
      body: JSON.stringify({ message })
    });
  }

  // ==================== 学生 CRUD ====================

  async function getStudents(params = {}) {
    if (isMock()) {
      return _mock(() => {
        const m = M();
        let list = [...m.students];
        if (params.student_id) list = list.filter(s => s.student_id === params.student_id);
        if (params.name) list = list.filter(s => s.name.includes(params.name));
        if (params.class_name) list = list.filter(s => s.class_name === params.class_name);
        if (params.skip != null) list = list.slice(params.skip);
        if (params.limit != null) list = list.slice(0, params.limit);
        return list;
      });
    }
    const qs = new URLSearchParams(params).toString();
    return _fetch('/students' + (qs ? '?' + qs : ''));
  }

  async function getStudent(id) {
    if (isMock()) return _mock(() => M().students.find(s => s.student_id === id));
    return _fetch('/students/' + id);
  }

  async function createStudent(data) {
    if (isMock()) return _mock(() => ({ ...data, is_deleted: false, created_at: new Date().toISOString() }));
    return _fetch('/students', { method: 'POST', body: JSON.stringify(data) });
  }

  async function updateStudent(id, data) {
    if (isMock()) return _mock(() => ({ ...M().students.find(s => s.student_id === id), ...data }));
    return _fetch('/students/' + id, { method: 'PUT', body: JSON.stringify(data) });
  }

  async function deleteStudent(id) {
    if (isMock()) return _mock({ message: '删除成功' });
    return _fetch('/students/' + id, { method: 'DELETE' });
  }

  // ==================== 成绩 CRUD ====================

  async function getScores(stuId) {
    if (isMock()) return _mock(() => M().scores[stuId] || []);
    return _fetch('/score/' + stuId);
  }

  async function createScore(data) {
    if (isMock()) return _mock(() => ({ id: Date.now(), ...data, created_at: new Date().toISOString() }));
    return _fetch('/score/', { method: 'POST', body: JSON.stringify(data) });
  }

  async function updateScore(data) {
    if (isMock()) return _mock(() => data);
    return _fetch('/score/update', { method: 'PUT', body: JSON.stringify(data) });
  }

  async function deleteScore(data) {
    if (isMock()) return _mock({ message: '删除成功' });
    return _fetch('/score/delete', { method: 'POST', body: JSON.stringify(data) });
  }

  // ==================== 就业 CRUD ====================

  async function getEmployment(stuId) {
    if (isMock()) return _mock(() => M().employment[stuId] || null);
    return _fetch('/employment/students/' + stuId);
  }

  async function getClassEmployment(className) {
    if (isMock()) {
      return _mock(() => Object.values(M().employment).filter(e => e.class_name === className && e.company_name));
    }
    return _fetch('/employment/class/' + className);
  }

  async function upsertEmployment(stuId, data) {
    if (isMock()) return _mock(() => ({ ...data, student_id: stuId }));
    return _fetch('/employment/students/' + stuId, { method: 'POST', body: JSON.stringify(data) });
  }

  async function deleteEmployment(stuId) {
    if (isMock()) return _mock({ message: '删除成功' });
    return _fetch('/employment/students/' + stuId, { method: 'DELETE' });
  }

  // ==================== 班级 CRUD ====================

  async function getClasses() {
    if (isMock()) return _mock(M().classes);
    return _fetch('/classes');
  }

  async function createClass(data) {
    if (isMock()) return _mock(data);
    return _fetch('/classes', { method: 'POST', body: JSON.stringify(data) });
  }

  async function updateClass(name, data) {
    if (isMock()) return _mock(data);
    return _fetch('/classes/' + name, { method: 'PUT', body: JSON.stringify(data) });
  }

  async function deleteClass(name) {
    if (isMock()) return _mock({ message: '删除成功' });
    return _fetch('/classes/' + name, { method: 'DELETE' });
  }

  // ==================== 教师 CRUD ====================

  async function getTeachers() {
    if (isMock()) return _mock(M().teachers);
    return _fetch('/teachers');
  }

  async function createTeacher(data) {
    if (isMock()) return _mock(data);
    return _fetch('/teachers', { method: 'POST', body: JSON.stringify(data) });
  }

  async function updateTeacher(id, data) {
    if (isMock()) return _mock(data);
    return _fetch('/teachers/' + id, { method: 'PUT', body: JSON.stringify(data) });
  }

  async function deleteTeacher(id) {
    if (isMock()) return _mock({ message: '删除成功' });
    return _fetch('/teachers/' + id, { method: 'DELETE' });
  }

  // ==================== 教师专用 ====================

  async function getStudentProfileReport(studentId) {
    if (isMock()) {
      return _mock(() => {
        const p = M().studentProfiles[studentId];
        const cog = M().l2Cognition[studentId] || [];
        const mem = M().l3Memories[studentId] || [];
        return {
          student_id: studentId,
          name: (M().students.find(s => s.student_id === studentId) || {}).name || '',
          class_name: (M().students.find(s => s.student_id === studentId) || {}).class_name || '',
          report_text: `${p ? p.rolling_summary : ''} L2认知标签: ${cog.map(c => c.relation + '(' + c.target + ')').join(', ')}。 最近L3快照: ${mem.slice(0, 2).map(m => m.summary).join('; ')}`,
          generated_at: new Date().toISOString(),
          profile: p,
          cognition: cog,
          recent_memories: mem.slice(0, 3),
          scores: M().scores[studentId] || [],
          care_strength: 0.71
        };
      });
    }
    return _fetch('/teacher/student/' + studentId);
  }

  async function getClassStats(className) {
    if (isMock()) {
      return _mock(() => ({
        class_name: className,
        student_count: M().students.filter(s => s.class_name === className).length,
        report_text: `${className}整体心理状态：考前焦虑比例偏高(约41%)，情绪偏低学生约占28%。建议安排减压班会。`,
        generated_at: new Date().toISOString(),
        distributions: {
          '考前焦虑': 5, '情绪偏低': 3, '社交回避': 2, '平稳': 8, '积极': 4
        }
      }));
    }
    return _fetch('/teacher/class/' + className + '/stats');
  }

  async function getCrisisAlerts() {
    if (isMock()) return _mock(M().crisisAlerts);
    return _fetch('/teacher/alerts');
  }

  // ==================== 管理员专用 ====================

  async function getAdminAuditL3(studentId, days = 30) {
    if (isMock()) {
      return _mock(() => {
        const mems = M().l3Memories[studentId] || [];
        return mems.map(m => ({ ...m, raw_dialogue: `[原文归档] ${m.summary} (脱敏后)` }));
      });
    }
    return _fetch(`/admin/audit/l3?student_id=${studentId}&days=${days}`, { method: 'POST' });
  }

  async function accountControl(data) {
    if (isMock()) return _mock({ success: true, ...data });
    return _fetch('/admin/account/control', { method: 'POST', body: JSON.stringify(data) });
  }

  async function knowledgeManage(action, data) {
    if (isMock()) return _mock({ success: true, action, data });
    return _fetch('/admin/knowledge?action=' + action, { method: 'POST', body: JSON.stringify(data) });
  }

  async function getSecurityLogs(studentId, category, days = 30) {
    if (isMock()) {
      return _mock(() => {
        let logs = M().securityLogs[studentId] || [];
        if (category) logs = logs.filter(l => l.category === category);
        return logs;
      });
    }
    let url = `/admin/security-logs/${studentId}?days=${days}`;
    if (category) url += '&category=' + category;
    return _fetch(url);
  }

  // ==================== 统计 ====================

  async function getStatistics(type) {
    if (isMock()) {
      return _mock(() => {
        const s = M().statistics;
        const map = {
          'older-than-30': s.olderThan30,
          'gender-count': s.genderCounts,
          'always-above-80': s.highScores,
          'failures': s.failures,
          'exam-avg': s.examAvgs,
          'top-salary': s.topSalary,
          'duration-per-student': s.employmentDurations,
          'avg-duration-by-class': s.classAvgDurations
        };
        return map[type] || [];
      });
    }
    const pathMap = {
      'older-than-30': '/statistics/students/older-than-30',
      'gender-count': '/statistics/class/gender-count',
      'always-above-80': '/statistics/scores/always-above-80',
      'failures': '/statistics/scores/failures',
      'exam-avg': '/statistics/scores/exam-avg-by-class',
      'top-salary': '/statistics/employment/top-salary',
      'duration-per-student': '/statistics/employment/duration-per-student',
      'avg-duration-by-class': '/statistics/employment/avg-duration-by-class'
    };
    return _fetch(pathMap[type] || '/statistics/' + type);
  }

  // ==================== 记忆/架构数据 ====================

  async function getL3Memories(studentId) {
    if (isMock()) return _mock(() => M().l3Memories[studentId] || []);
    return _fetch('/memory/l3/' + studentId);
  }

  async function getL2Cognition(studentId) {
    if (isMock()) return _mock(() => M().l2Cognition[studentId] || []);
    return _fetch('/memory/l2/' + studentId);
  }

  async function getStudentProfile(studentId) {
    if (isMock()) return _mock(M().studentProfiles[studentId] || null);
    return _fetch('/memory/profile/' + studentId);
  }

  // ==================== NL 自然语言查询 ====================

  async function nlQuery(question) {
    if (isMock()) {
      return _mock(() => {
        const m = M();
        let result = [];
        let sql = '-- Mock模式，未实际执行SQL';
        if (question.includes('女生') && question.includes('数学') && question.includes('85')) {
          sql = "SELECT s.student_id, s.name, s.class_name, sc.score FROM students s JOIN scores sc ON s.student_id = sc.student_id WHERE s.gender = '女' AND sc.subject = '数学' AND sc.score > 85 AND s.is_deleted = 0";
          result = [{ student_id: 'XH_2024001', name: '小红', class_name: '初二3班', score: 92.0 }];
        } else if (question.includes('男生') && question.includes('初二3班')) {
          sql = "SELECT COUNT(*) AS male_count FROM students WHERE class_name = '初二3班' AND gender = '男' AND is_deleted = 0";
          result = [{ male_count: 15 }];
        } else if (question.includes('薪资') && (question.includes('最高') || question.includes('平均'))) {
          sql = "SELECT e.class_name, AVG(e.salary) AS avg_salary FROM employment e WHERE e.salary IS NOT NULL GROUP BY e.class_name ORDER BY avg_salary DESC LIMIT 1";
          result = [{ class_name: '初二3班', avg_salary: 12500.0 }];
        } else if (question.includes('30岁')) {
          sql = "SELECT student_id, name, class_name, age, gender FROM students WHERE age > 30 AND is_deleted = 0 ORDER BY age DESC";
          result = m.statistics.olderThan30;
        } else if (question.includes('不及格')) {
          sql = "SELECT s.name, s.class_name, COUNT(sc.id) AS fail_count FROM students s JOIN scores sc ON s.student_id = sc.student_id WHERE sc.score < 60 AND s.is_deleted = 0 GROUP BY s.student_id HAVING fail_count > 2";
          result = m.statistics.failures;
        } else {
          sql = `-- 自动生成查询: ${question}`;
          result = [{ message: 'Mock模式: 请切换到API模式以执行真实查询' }];
        }
        return {
          question, sql, sql_error: null,
          result, result_row_count: result.length,
          answer: `查询完成，共 ${result.length} 条结果。`
        };
      });
    }
    return _fetch('/nl-query/', {
      method: 'POST',
      body: JSON.stringify({ question })
    });
  }

  // ==================== 认证 ====================

  async function login(userId, password) {
    if (isMock()) {
      return _mock(() => {
        const users = window.MOCK_DATA.users;
        const u = users[userId];
        if (!u) return { error: '用户名或密码错误' };
        const token = 'mock_token_' + userId;
        setToken(token);
        saveUser({ user_id: userId, role: u.role, name: u.name });
        return { access_token: token, token_type: 'bearer', user_id: userId, role: u.role, name: u.name };
      });
    }
    const res = await _fetch('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ user_id: userId, password: password }),
    });
    if (res && !res.error && res.access_token) {
      setToken(res.access_token);
      saveUser({ user_id: res.user_id, role: res.role, name: res.name });
    }
    return res;
  }

  // ==================== 公开接口 ====================

  return {
    // 模式控制
    getMode, setMode, isMock, BASE_URL,

    // 认证
    login, getToken, setToken, clearToken, getSavedUser,

    // 系统
    healthCheck,

    // 聊天
    sendChat,

    // 学生 CRUD
    getStudents, getStudent, createStudent, updateStudent, deleteStudent,

    // 成绩 CRUD
    getScores, createScore, updateScore, deleteScore,

    // 就业 CRUD
    getEmployment, getClassEmployment, upsertEmployment, deleteEmployment,

    // 班级 CRUD
    getClasses, createClass, updateClass, deleteClass,

    // 教师 CRUD
    getTeachers, createTeacher, updateTeacher, deleteTeacher,

    // 教师专用
    getStudentProfileReport, getClassStats, getCrisisAlerts,

    // 管理员专用
    getAdminAuditL3, accountControl, knowledgeManage, getSecurityLogs,

    // 统计
    getStatistics,

    // NL 查询
    nlQuery,

    // 记忆
    getL3Memories, getL2Cognition, getStudentProfile,

    // 常量数据（无需API）
    getGraphNodes: () => window.MOCK_DATA.graphNodes,
    getMemoryLayers: () => window.MOCK_DATA.memoryLayers,
    getHLMMScenes: () => window.MOCK_DATA.hlmmScenes,
    getCharacters: () => window.MOCK_DATA.characters,
    getCharacterRelations: () => window.MOCK_DATA.characterRelations,
    getConfig: () => window.MOCK_DATA.config,
    getClassicSearch: (query, source) => {
      const results = window.MOCK_DATA.classicSearchResults;
      let all = [];
      if (source && results[source]) {
        all = results[source];
      } else {
        Object.values(results).forEach(arr => all = all.concat(arr));
      }
      if (query) {
        const q = query.toLowerCase();
        all = all.filter(r => r.title.includes(q) || r.content.includes(q));
      }
      return all;
    }
  };
})();

window.API = API;
