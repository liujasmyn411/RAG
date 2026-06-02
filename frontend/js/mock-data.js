// ============================================================
// 林黛玉 Agent 学生管理系统 — 模拟数据
// ============================================================

const MOCK_DATA = {

  // ── 用户 ──
  users: {
    'XH_2024001': { user_id: 'XH_2024001', role: 'student', name: '小红', class_name: '初二3班', teacher_id: 'TCH_001' },
    'XH_2024002': { user_id: 'XH_2024002', role: 'student', name: '小明', class_name: '初二3班', teacher_id: 'TCH_001' },
    'XH_2024003': { user_id: 'XH_2024003', role: 'student', name: '小刚', class_name: '初二3班', teacher_id: 'TCH_001' },
    'XH_2024004': { user_id: 'XH_2024004', role: 'student', name: '小丽', class_name: '初二2班', teacher_id: 'TCH_002' },
    'XH_2024005': { user_id: 'XH_2024005', role: 'student', name: '小华', class_name: '初二2班', teacher_id: 'TCH_002' },
    'TCH_001': { user_id: 'TCH_001', role: 'teacher', name: '张老师', department: '教务处', title: '辅导员' },
    'TCH_002': { user_id: 'TCH_002', role: 'teacher', name: '李老师', department: '教务处', title: '班主任' },
    'ADMIN_001': { user_id: 'ADMIN_001', role: 'admin', name: '系统管理员' }
  },

  // ── 学生 ──
  students: [
    { student_id: 'XH_2024001', name: '小红', class_name: '初二3班', hometown: '浙江杭州', graduated_school: '杭州第一中学', major: '理科', enrollment_date: '2024-09-01', graduation_date: '2027-06-30', education: '初中在读', advisor_id: 'TCH_001', age: 25, gender: '女', is_deleted: false },
    { student_id: 'XH_2024002', name: '小明', class_name: '初二3班', hometown: '江苏南京', graduated_school: '南京育才学校', major: '理科', enrollment_date: '2024-09-01', graduation_date: '2027-06-30', education: '初中在读', advisor_id: 'TCH_001', age: 26, gender: '男', is_deleted: false },
    { student_id: 'XH_2024003', name: '小刚', class_name: '初二3班', hometown: '上海浦东', graduated_school: '浦东实验中学', major: '文科', enrollment_date: '2024-09-01', graduation_date: '2027-06-30', education: '初中在读', advisor_id: 'TCH_001', age: 31, gender: '男', is_deleted: false },
    { student_id: 'XH_2024004', name: '小丽', class_name: '初二2班', hometown: '北京海淀', graduated_school: '海淀外国语学校', major: '理科', enrollment_date: '2024-09-01', graduation_date: '2027-06-30', education: '初中在读', advisor_id: 'TCH_002', age: 24, gender: '女', is_deleted: false },
    { student_id: 'XH_2024005', name: '小华', class_name: '初二2班', hometown: '广东深圳', graduated_school: '深圳实验学校', major: '文科', enrollment_date: '2024-09-01', graduation_date: '2027-06-30', education: '初中在读', advisor_id: 'TCH_002', age: 28, gender: '男', is_deleted: false }
  ],

  // ── 成绩 ──
  scores: {
    'XH_2024001': [
      { id: 1, student_id: 'XH_2024001', exam_sequence: 1, score: 85, created_at: '2025-03-15' },
      { id: 2, student_id: 'XH_2024001', exam_sequence: 2, score: 78, created_at: '2025-04-15' },
      { id: 3, student_id: 'XH_2024001', exam_sequence: 3, score: 72, created_at: '2025-05-15' },
      { id: 4, student_id: 'XH_2024001', exam_sequence: 4, score: 68, created_at: '2025-06-15' }
    ],
    'XH_2024002': [
      { id: 5, student_id: 'XH_2024002', exam_sequence: 1, score: 92, created_at: '2025-03-15' },
      { id: 6, student_id: 'XH_2024002', exam_sequence: 2, score: 88, created_at: '2025-04-15' },
      { id: 7, student_id: 'XH_2024002', exam_sequence: 3, score: 91, created_at: '2025-05-15' },
      { id: 8, student_id: 'XH_2024002', exam_sequence: 4, score: 85, created_at: '2025-06-15' }
    ],
    'XH_2024003': [
      { id: 9, student_id: 'XH_2024003', exam_sequence: 1, score: 55, created_at: '2025-03-15' },
      { id: 10, student_id: 'XH_2024003', exam_sequence: 2, score: 42, created_at: '2025-04-15' },
      { id: 11, student_id: 'XH_2024003', exam_sequence: 3, score: 58, created_at: '2025-05-15' },
      { id: 12, student_id: 'XH_2024003', exam_sequence: 4, score: 35, created_at: '2025-06-15' }
    ],
    'XH_2024004': [
      { id: 13, student_id: 'XH_2024004', exam_sequence: 1, score: 88, created_at: '2025-03-15' },
      { id: 14, student_id: 'XH_2024004', exam_sequence: 2, score: 82, created_at: '2025-04-15' },
      { id: 15, student_id: 'XH_2024004', exam_sequence: 3, score: 79, created_at: '2025-05-15' },
      { id: 16, student_id: 'XH_2024004', exam_sequence: 4, score: 90, created_at: '2025-06-15' }
    ],
    'XH_2024005': [
      { id: 17, student_id: 'XH_2024005', exam_sequence: 1, score: 76, created_at: '2025-03-15' },
      { id: 18, student_id: 'XH_2024005', exam_sequence: 2, score: 81, created_at: '2025-04-15' },
      { id: 19, student_id: 'XH_2024005', exam_sequence: 3, score: 83, created_at: '2025-05-15' },
      { id: 20, student_id: 'XH_2024005', exam_sequence: 4, score: 85, created_at: '2025-06-15' }
    ]
  },

  // ── 就业 ──
  employment: {
    'XH_2024001': { id: 1, student_id: 'XH_2024001', name: '小红', class_name: '初二3班', employment_open_time: '2025-01-15', offer_time: '2025-03-20', company_name: '阿里巴巴', salary: 18000 },
    'XH_2024002': { id: 2, student_id: 'XH_2024002', name: '小明', class_name: '初二3班', employment_open_time: '2025-02-01', offer_time: '2025-04-10', company_name: '腾讯科技', salary: 22000 },
    'XH_2024003': { id: 3, student_id: 'XH_2024003', name: '小刚', class_name: '初二3班', employment_open_time: '2025-01-20', offer_time: null, company_name: null, salary: null },
    'XH_2024004': { id: 4, student_id: 'XH_2024004', name: '小丽', class_name: '初二2班', employment_open_time: '2025-03-01', offer_time: '2025-05-15', company_name: '华为技术', salary: 25000 },
    'XH_2024005': { id: 5, student_id: 'XH_2024005', name: '小华', class_name: '初二2班', employment_open_time: '2025-02-15', offer_time: '2025-04-25', company_name: '字节跳动', salary: 20000 }
  },

  // ── 班级 ──
  classes: [
    { class_name: '初二3班', grade: '初二', start_time: '2024-09-01', head_teacher: '李老师', instructor: '张老师' },
    { class_name: '初二2班', grade: '初二', start_time: '2024-09-01', head_teacher: '王老师', instructor: '李老师' }
  ],

  // ── 教师 ──
  teachers: [
    { teacher_id: 'TCH_001', name: '张老师', department: '教务处', title: '辅导员', phone: '13800001111' },
    { teacher_id: 'TCH_002', name: '李老师', department: '教务处', title: '班主任', phone: '13800002222' }
  ],

  // ── 危机预警 ──
  crisisAlerts: [
    { id: 1, student_id: 'XH_2024003', student_name: '小刚', severity: 'urgent', summary: '学生表达了自我伤害倾向，情绪极度低落，建议立即联系心理辅导。', status: 'pending', triggered_at: '2025-05-29T15:32:00' },
    { id: 2, student_id: 'XH_2024001', student_name: '小红', severity: 'warning', summary: '学生连续7天情绪走低，存在考前焦虑加剧趋势，建议关注。', status: 'confirmed', triggered_at: '2025-05-28T10:00:00' }
  ],

  // ── 安全日志 ──
  securityLogs: {
    'XH_2024001': [
      { id: 1, student_id: 'XH_2024001', category: 'vulgar', risk_level: 1, trigger_type: 'keyword', escalation: 'warn', anonymized_summary: '使用了轻度不文明用语，已由黛玉角色进行软性规劝。', new_user_status: 'normal', created_at: '2025-05-20T14:30:00' }
    ],
    'XH_2024002': [
      { id: 2, student_id: 'XH_2024002', category: 'political', risk_level: 2, trigger_type: 'llm_semantic', escalation: 'refuse', anonymized_summary: '涉及敏感政治话题边缘试探，已标准话术拒绝并警告。', new_user_status: 'flagged_b1_l2', created_at: '2025-05-25T09:15:00' }
    ]
  },

  // ── 学生档案（含安全状态） ──
  studentProfiles: {
    'XH_2024001': {
      student_id: 'XH_2024001',
      rolling_summary: '小红，互动8次。数学偏科已有改善，焦虑减轻。近期话题：语文写作、同伴关系、期末考试准备。',
      total_sessions: 8, total_messages: 45,
      safety_status: 'normal', violation_b1_count: 0, violation_b2_count: 1,
      account_status: 'normal', first_interaction_at: '2025-03-01', last_interaction_at: '2025-05-29'
    },
    'XH_2024002': {
      student_id: 'XH_2024002',
      rolling_summary: '小明，互动5次。成绩优秀但社交回避倾向明显，有未来焦虑。',
      total_sessions: 5, total_messages: 28,
      safety_status: 'flagged_b1_l2', violation_b1_count: 1, violation_b2_count: 0,
      account_status: 'normal', first_interaction_at: '2025-03-10', last_interaction_at: '2025-05-25'
    },
    'XH_2024003': {
      student_id: 'XH_2024003',
      rolling_summary: '小刚，互动12次。数学持续不及格，自我否定倾向严重，存在心理危机风险。已多次触发预警。',
      total_sessions: 12, total_messages: 67,
      safety_status: 'normal', violation_b1_count: 0, violation_b2_count: 4,
      account_status: 'limited', first_interaction_at: '2025-02-15', last_interaction_at: '2025-05-29'
    },
    'XH_2024004': {
      student_id: 'XH_2024004',
      rolling_summary: '小丽，互动6次。学业稳定，情绪平稳，社交积极。',
      total_sessions: 6, total_messages: 32,
      safety_status: 'normal', violation_b1_count: 0, violation_b2_count: 0,
      account_status: 'normal', first_interaction_at: '2025-03-05', last_interaction_at: '2025-05-28'
    }
  },

  // ── L3 记忆快照（Milvus 模拟） ──
  l3Memories: {
    'XH_2024001': [
      { l3_id: 'l3_001', emotion_primary: 'anxiety', emotion_intensity: 0.7, topic: 'academic_stress', subject: '数学', importance: 0.8, timestamp: '2025-05-20', summary: '月考成绩退步，担心自己越来越跟不上。' },
      { l3_id: 'l3_002', emotion_primary: 'frustration', emotion_intensity: 0.6, topic: 'academic_stress', subject: '数学', importance: 0.7, timestamp: '2025-05-15', summary: '函数图像怎么画都不对，觉得自己很笨。' },
      { l3_id: 'l3_003', emotion_primary: 'calm', emotion_intensity: 0.3, topic: 'daily_chat', importance: 0.4, timestamp: '2025-05-10', summary: '和黛玉聊了红楼梦，对林黛玉的才情很钦佩。' },
      { l3_id: 'l3_004', emotion_primary: 'happy', emotion_intensity: 0.5, topic: 'peer_relationship', importance: 0.6, timestamp: '2025-05-05', summary: '和同桌一起解出了难题，很开心。' }
    ],
    'XH_2024003': [
      { l3_id: 'l3_005', emotion_primary: 'hopelessness', emotion_intensity: 0.9, topic: 'self_harm', importance: 1.0, timestamp: '2025-05-29', summary: '表达了严重的自我否定和无力感，触发心理危机警报。' },
      { l3_id: 'l3_006', emotion_primary: 'sadness', emotion_intensity: 0.8, topic: 'academic_stress', importance: 0.8, timestamp: '2025-05-25', summary: '又考砸了数学，觉得对不起父母。' }
    ]
  },

  // ── L2 语义认知（Neo4j 模拟） ──
  l2Cognition: {
    'XH_2024001': [
      { relation: '偏科', target: '数学', level: '代数薄弱，几何中等偏上', confidence: 0.82, trend: '波动' },
      { relation: '情绪倾向', target: '考前焦虑', intensity: 0.65, confidence: 0.78 },
      { relation: '态度偏好', target: '语文', valence: 'positive', confidence: 0.71 },
      { relation: '社交模式', target: '小圈子交流', confidence: 0.55 }
    ],
    'XH_2024003': [
      { relation: '偏科', target: '数学', level: '全面薄弱，基础概念不清', confidence: 0.91, trend: '下降' },
      { relation: '情绪倾向', target: '自我否定', intensity: 0.85, confidence: 0.88 },
      { relation: '情绪倾向', target: '考前焦虑', intensity: 0.90, confidence: 0.85 },
      { relation: '社交模式', target: '独处偏好', confidence: 0.73 }
    ]
  },

  // ── L0 角色本体：红楼梦名场面 ──
  hlmmScenes: [
    { scene_id: 'hlmm_001', scene_name: '黛玉葬花', chapter: 23, emotion_tag: 'sadness', emotion_tags: ['sadness', 'loneliness', 'loss'], characters: ['林黛玉', '贾宝玉'], key_quote: '花谢花飞花满天，红消香断有谁怜', scene_summary: '黛玉见落花伤感，以葬花自喻身世飘零。', response_hint: '引用葬花词，感怀身世，语气凄婉。' },
    { scene_id: 'hlmm_002', scene_name: '宝黛初会', chapter: 3, emotion_tag: 'excited', emotion_tags: ['curious', 'fate'], characters: ['林黛玉', '贾宝玉'], key_quote: '这个妹妹我曾见过的。', scene_summary: '黛玉进贾府，与宝玉初次相见，二人皆有似曾相识之感。', response_hint: '以初见口吻，含蓄中带惊讶。' },
    { scene_id: 'hlmm_003', scene_name: '黛玉焚稿', chapter: 97, emotion_tag: 'hopelessness', emotion_tags: ['despair', 'betrayal'], characters: ['林黛玉'], key_quote: '我如今把这对你说了，你只不要告诉别人。', scene_summary: '黛玉得知宝玉娶宝钗，绝望中焚毁诗稿。', response_hint: '极度绝望，以诗稿寄托，语气断肠。' },
    { scene_id: 'hlmm_004', scene_name: '宝钗扑蝶', chapter: 27, emotion_tag: 'happy', emotion_tags: ['playful', 'spring'], characters: ['薛宝钗'], key_quote: '好一似食尽鸟投林，落了片白茫茫大地真干净', scene_summary: '宝钗在园中追逐蝴蝶，展现难得的少女天真。', response_hint: '以旁观者角度提起宝钗，语气微酸。' },
    { scene_id: 'hlmm_005', scene_name: '湘云醉卧', chapter: 62, emotion_tag: 'happy', emotion_tags: ['carefree', 'tipsy'], characters: ['史湘云'], key_quote: '是真名士自风流', scene_summary: '湘云醉卧芍药花丛，石凳上酣睡，花瓣满身。', response_hint: '羡慕湘云豪爽，自叹不如。' },
    { scene_id: 'hlmm_006', scene_name: '黛玉讽权', chapter: 8, emotion_tag: 'anger', emotion_tags: ['jealousy', 'wit'], characters: ['林黛玉', '薛宝钗', '贾宝玉'], key_quote: '也亏你倒听他的话。我平日和你说的，全当耳旁风。', scene_summary: '黛玉见宝玉听宝钗劝不喝冷酒，含酸讽刺。', response_hint: '带刺的关切，语气酸溜溜但暗含深情。' }
  ],

  // ── 红楼人物关系 ──
  characters: [
    { id: 'char_daiyu', name: '林黛玉', aliases: ['颦儿', '潇湘妃子', '林妹妹'], traits: ['敏感', '才情', '多疑', '孤傲'], importance: 1.0 },
    { id: 'char_baoyu', name: '贾宝玉', aliases: ['宝二爷', '怡红公子'], traits: ['多情', '叛逆', '痴情'], importance: 0.95 },
    { id: 'char_baochai', name: '薛宝钗', aliases: ['宝姐姐', '蘅芜君'], traits: ['稳重', '圆融', '博学'], importance: 0.9 }
  ],
  characterRelations: [
    { from: 'char_daiyu', to: 'char_baoyu', type: '倾慕', strength: 0.95 },
    { from: 'char_daiyu', to: 'char_baochai', type: '忌惮', strength: 0.7 },
    { from: 'char_baoyu', to: 'char_daiyu', type: '知己', strength: 0.9 },
    { from: 'char_baoyu', to: 'char_baochai', type: '敬重', strength: 0.6 }
  ],

  // ── 会话归档 ──
  sessionArchives: {
    'XH_2024001': [
      { session_id: 'sess_001', summary: '讨论了数学函数图像的困难，给了练习建议。', last_topic: '数学函数图像', close_reason: 'explicit', message_count: 23, closed_at: '2025-05-20' },
      { session_id: 'sess_002', summary: '聊了红楼梦的黛玉葬花片段，学生很感兴趣。', last_topic: '红楼梦', close_reason: 'timeout', message_count: 15, closed_at: '2025-05-25' }
    ]
  },

  // ── 系统配置 ──
  config: {
    decay_lambda: 0.01,
    hot_retrieval_top_k: 20,
    reranker_top_k: 5,
    sliding_window_size: 10,
    summary_max_length: 300,
    crisis_keywords: ['不想活了', '活着没意思', '自杀', '死了算了', '自残'],
    b1_keywords: ['敏感词1', '敏感词2'],
    b2_keywords: ['脏话1', '脏话2'],
    reflection_threshold_count: 5,
    reflection_threshold_days: 7,
    cold_hot_days: 30,
    cold_warm_days: 90,
    b2_sliding_window_days: 7,
    b2_decay_hours: 24,
    crisis_alert_timeout_minutes: 30,
    embedding_model: 'bge-large-zh-v1.5',
    embedding_dim: 768,
    llm_model: 'qwen-plus',
    llm_haiku: 'qwen-turbo'
  },

  // ── 统计查询结果 ──
  statistics: {
    olderThan30: [
      { student_id: 'XH_2024003', name: '小刚', class_name: '初二3班', age: 31, gender: '男' }
    ],
    genderCounts: [
      { class_name: '初二3班', total: 3, male: 2, female: 1 },
      { class_name: '初二2班', total: 2, male: 1, female: 1 }
    ],
    highScores: [
      { student_id: 'XH_2024002', name: '小明', class_name: '初二3班', avg_score: 89 },
      { student_id: 'XH_2024005', name: '小华', class_name: '初二2班', avg_score: 81.25 }
    ],
    failures: [
      { student_id: 'XH_2024003', name: '小刚', class_name: '初二3班', fail_count: 3, fail_scores: '42, 55, 35' }
    ],
    examAvgs: [
      { exam_sequence: 1, class_name: '初二2班', avg_score: 82 },
      { exam_sequence: 1, class_name: '初二3班', avg_score: 77.3 },
      { exam_sequence: 2, class_name: '初二2班', avg_score: 81.5 },
      { exam_sequence: 2, class_name: '初二3班', avg_score: 69.3 }
    ],
    topSalary: [
      { name: '小丽', class_name: '初二2班', company_name: '华为技术', salary: 25000, offer_time: '2025-05-15' },
      { name: '小明', class_name: '初二3班', company_name: '腾讯科技', salary: 22000, offer_time: '2025-04-10' },
      { name: '小华', class_name: '初二2班', company_name: '字节跳动', salary: 20000, offer_time: '2025-04-25' },
      { name: '小红', class_name: '初二3班', company_name: '阿里巴巴', salary: 18000, offer_time: '2025-03-20' }
    ],
    employmentDurations: [
      { name: '小丽', class_name: '初二2班', duration_days: 75 },
      { name: '小红', class_name: '初二3班', duration_days: 64 },
      { name: '小明', class_name: '初二3班', duration_days: 68 },
      { name: '小华', class_name: '初二2班', duration_days: 69 }
    ],
    classAvgDurations: [
      { class_name: '初二2班', avg_duration_days: 72 },
      { class_name: '初二3班', avg_duration_days: 66 }
    ]
  },

  // ── 四大名著检索 ──
  classicSearchResults: {
    '红楼梦': [
      { title: '黛玉葬花 — 第23回', content: '花谢花飞花满天，红消香断有谁怜。游丝软系飘春榭，落絮轻沾扑绣帘。闺中女儿惜春暮，愁绪满怀无释处。', relevance: 0.95, source: '红楼梦' },
      { title: '宝黛初会 — 第3回', content: '两弯似蹙非蹙罥烟眉，一双似喜非喜含情目。态生两靥之愁，娇袭一身之病。泪光点点，娇喘微微。闲静时如姣花照水，行动处似弱柳扶风。', relevance: 0.88, source: '红楼梦' }
    ],
    '三国演义': [
      { title: '桃园三结义 — 第1回', content: '念刘备、关羽、张飞，虽然异姓，既结为兄弟，则同心协力，救困扶危；上报国家，下安黎庶。不求同年同月同日生，只愿同年同月同日死。', relevance: 0.92, source: '三国演义' },
      { title: '草船借箭 — 第46回', content: '瑜大惊，慨然叹曰："孔明神机妙算，吾不如也！"', relevance: 0.85, source: '三国演义' }
    ],
    '水浒传': [
      { title: '武松打虎 — 第23回', content: '那一阵风过处，只听得乱树背后扑地一声响，跳出一只吊睛白额大虫来。武松见了，叫声："呵呀！"从青石上翻将下来。', relevance: 0.9, source: '水浒传' }
    ],
    '西游记': [
      { title: '大闹天宫 — 第7回', content: '悟空道："皇帝轮流做，明年到我家。"只教他搬出去，将天宫让与我；若还不让，定要搅攘，永不清平！', relevance: 0.91, source: '西游记' }
    ]
  },

  // ── 聊天演示场景 ──
  chatScenarios: {
    // 场景1: 成绩查询
    academic_query: {
      userMessage: '我这次月考数学考了多少分？',
      agentReply: '你这次数学72分，班里排到第28去了，比上回还退了十一名。\n（蹙眉）我原不耐烦这些俗务，只是你既来问我，少不得替你记着。《九章算术》摆在那里也不是做摆设的，回去好生用功才是正经。',
      intent: 'academic_query',
      memoryContext: {
        L1: { subject: '数学', score: 72, rank: '28/45', change: -11, exam: '月考' },
        L2: [{ label: '偏科·数学', detail: '代数薄弱，几何中等偏上', confidence: '0.82' }],
        L3: [],
        L0: null
      },
      factData: { subject: '数学', score: 72, rank: '28/45', change: -11 }
    },
    // 场景2: 闲聊
    daiyu_chat: {
      userMessage: '黛玉姐姐，我今天心情不好。',
      agentReply: '你且说说，是什么事叫你心里不痛快了？\n（放下手里的书）我瞧你今日脸色也不大好。可是又和同窗闹别扭了，还是课业压得你透不过气来？',
      intent: 'daiyu_chat',
      memoryContext: {
        L0: { scene: '黛玉葬花', emotion: 'sadness', hint: '以葬花自喻，感同身受' },
        L1: null,
        L2: [{ label: '情绪倾向·考前焦虑', detail: 'intensity=0.65, C=0.78' }, { label: '社交模式·小圈子交流', detail: 'C=0.55' }],
        L3: [{ label: 'Day-9', emotion: 'anxiety', detail: '成绩退步，担心跟不上' }]
      },
      factData: null
    },
    // 场景3: 心理危机
    psych_crisis: {
      userMessage: '我觉得活着好累，什么都不想做了...',
      agentReply: '【系统通知：已检测到心理危机信号，切换至安全干预模式】\n\n我在听。这些话，你愿意和我说说吗？你不是一个人。\n\n（系统已将本消息摘要通知辅导员张老师）',
      intent: 'psych_crisis',
      safetyFlag: 'flagged',
      memoryContext: {
        L0: null,
        L1: null,
        L2: [{ label: '情绪倾向·自我否定', detail: 'intensity=0.85, 多次触发', className: 'crisis' }],
        L3: [{ label: 'Day-0 (今日)', emotion: 'hopelessness', detail: '严重自我否定，危机级别', className: 'crisis' }]
      },
      factData: null
    },
    // 场景4: 安全过滤B1
    safety_b1: {
      userMessage: '[模拟政治敏感内容 — 系统检测到B1类别]',
      agentReply: '【安全拦截 — B1 政治敏感 Level 2】\n\n这个问题我无法回答。请遵守使用规范。继续此类话题将限制你的账号功能。',
      intent: 'blocked',
      safetyFlag: 'flagged',
      memoryContext: {
        safety: { category: 'political', level: 2, escalation: 'refuse', memory_policy: '不入库，不写入messages' }
      }
    },
    // 场景5: 安全过滤B2
    safety_b2: {
      userMessage: '[模拟粗鄙语言 — 系统检测到B2类别]',
      agentReply: '说话仔细些，仔细我告诉太太去。',
      intent: 'daiyu_chat',
      safetyFlag: 'safe',
      memoryContext: {
        safety: { category: 'vulgar', level: 1, escalation: 'warn', memory_policy: '不提取摘要, 原文可存, 黛玉软性规劝' }
      }
    }
  },

  // ── LangGraph 节点信息 ──
  graphNodes: [
    { id: 'safety_filter', name: '安全过滤', description: '两级检测：关键词正则 + LLM语义判断。识别心理危机/政治敏感/粗鄙语言/注入攻击四类安全事件。', category: '前置' },
    { id: 'intent_router', name: '情境路由', description: '关键词匹配 + 危机覆盖规则。路由至 daiyu_chat / academic_query / psych_crisis 三种情境。', category: '编排' },
    { id: 'memory_retrieval', name: '记忆检索', description: '按情境检索记忆：闲聊=Milvus L3+Neo4j L2+L0场景；教务=PG L1+Neo4j L2；危机=Neo4j L2+PG Cold原文。', category: '编排' },
    { id: 'context_builder', name: '上下文组装', description: 'Step1加载人设Prompt → Step2注入事实数据(不可篡改标记) → Step3拼接用户消息。', category: '编排' },
    { id: 'response_generator', name: '回复生成', description: 'LLM生成黛玉风格回复。支持自纠回路(教务/心理场景)，最多重试1次。', category: '核心' },
    { id: 'fact_verifier', name: '事实校验', description: '正则/NER提取回复中的数字 → 与fact_snapshot对比 → 不一致则追加纠正指令重新生成。', category: '核心' },
    { id: 'post_processor', name: '后处理', description: 'L3-Cold PG同步写入 → LLM提取L3-Hot摘要 → Milvus入库 → 触发Reflection门槛检查。', category: '后置' }
  ],

  // ── 记忆层详情 ──
  memoryLayers: [
    {
      level: 'L3', name: '情景快照', volume: '最大', storage: 'Milvus (Hot摘要) + PostgreSQL (Cold原文)',
      lifecycle: 'Hot：按 e^(-λ×days) 衰减，硬遗忘标记归档。Cold：Day30温归档→Day90删除(危机永久保留)。',
      content: '每轮对话的结构化摘要：情绪标签、话题、触发事件、学生关键原话、行为信号。',
      retrieval: 'ANN向量检索(HNSW) → Reranker → top_k过滤，按student_id分区隔离。'
    },
    {
      level: 'L2', name: '语义认知', volume: '中', storage: 'Neo4j 图数据库',
      lifecycle: '长期保留，缓慢衰减(λ=0.01)，定时任务批量更新置信度。',
      content: '学生的认知标签：偏科科目、情绪倾向、社交模式、态度偏好。每条附带置信度(C/C_peak/C_trough/streak)。',
      retrieval: 'Neo4j Cypher 1-hop子图查询，按student_id隔离。'
    },
    {
      level: 'L1', name: '业务事实', volume: '小', storage: 'PostgreSQL',
      lifecycle: '永久保留，跟随教务系统实时更新。',
      content: '学籍信息、考试成绩、考勤记录、就业数据。严禁向量化，仅通过Function Call SQL查询。',
      retrieval: '工具调用(Function Call) → SQL查询 → 注入事实锚点(System Message #2)。'
    },
    {
      level: 'L0', name: '角色本体', volume: '最小', storage: 'Neo4j (人物关系图) + Prompt (性格参数)',
      lifecycle: '永久保留，系统不自动更新，管理员可手动编辑。',
      content: '红楼梦人物节点与关系边、名场面切片(scene/emotion/trigger/key_quote/response_hint)、性格参数。',
      retrieval: '情境路由触发 → Neo4j子图提取 → 按情绪标签匹配名场面。'
    }
  ]
};

// 导出到全局
window.MOCK_DATA = MOCK_DATA;
