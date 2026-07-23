"""
EasyWiki — Product Knowledge Base Module
OrionStar product catalog: 21 products + 8 solutions + 12 material types
"""
import json, uuid
from typing import Dict, List, Optional, Set
from orgmind.db import get_db, OrgMindDB

# === Product schema ===
PRODUCT_SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL,
    product_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL, name_zh TEXT, description TEXT,
    region TEXT DEFAULT 'overseas', category TEXT, keywords TEXT,
    status TEXT DEFAULT 'active', sort_order INTEGER DEFAULT 0,
    assets TEXT DEFAULT '{}', highlights TEXT DEFAULT '[]',
    specifications TEXT DEFAULT '{}', scenes TEXT DEFAULT '[]',
    cases TEXT DEFAULT '[]', solutions TEXT DEFAULT '[]',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS solutions (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL,
    name TEXT NOT NULL, name_zh TEXT, description TEXT,
    category TEXT, products TEXT DEFAULT '[]',
    assets TEXT DEFAULT '{}', created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS content_templates (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL,
    name TEXT NOT NULL, article_type TEXT NOT NULL,
    category TEXT, model_family TEXT DEFAULT 'article',
    prompt_template TEXT NOT NULL, description TEXT,
    icon TEXT DEFAULT 'document', created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS generated_outputs (
    id TEXT PRIMARY KEY, org_id TEXT NOT NULL, user_id TEXT NOT NULL,
    article_type TEXT, model_used TEXT, language TEXT DEFAULT 'zh',
    prompt TEXT, content TEXT NOT NULL,
    product_id TEXT, template_id TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
"""


def ensure_product_tables(db: OrgMindDB):
    try:
        db.execute("SELECT 1 FROM products LIMIT 1")
        db.execute("SELECT 1 FROM content_templates LIMIT 1")
        db.execute("SELECT 1 FROM generated_outputs LIMIT 1")
    except Exception:
        pass


def get_products(org_id: str, category: str = None, region: str = None, keyword: str = None) -> List[Dict]:
    db = get_db()
    sql = "SELECT * FROM products WHERE org_id=? AND status='active'"
    params = [org_id]
    if category: sql += " AND category=?"; params.append(category)
    if region: sql += " AND region=?"; params.append(region)
    if keyword: sql += " AND keywords LIKE ?"; params.append(f"%{keyword}%")
    sql += " ORDER BY sort_order, name"
    rows = db.execute(sql, tuple(params)).fetchall()
    return [_product_dict(r) for r in rows]


def get_product(org_id: str, product_key: str) -> Optional[Dict]:
    db = get_db()
    row = db.execute("SELECT * FROM products WHERE org_id=? AND product_key=? AND status='active'", (org_id, product_key)).fetchone()
    return _product_dict(row) if row else None


def search_products(org_id: str, query: str) -> List[Dict]:
    db = get_db()
    rows = db.execute("SELECT * FROM products WHERE org_id=? AND status='active' AND (name LIKE ? OR name_zh LIKE ? OR description LIKE ? OR keywords LIKE ?) ORDER BY sort_order LIMIT 30",
        (org_id, f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")).fetchall()
    return [_product_dict(r) for r in rows]


def get_templates(org_id: str) -> List[Dict]:
    db = get_db()
    rows = db.execute("SELECT * FROM content_templates WHERE org_id=? ORDER BY article_type", (org_id,)).fetchall()
    return [dict(r) for r in rows]


def save_output(org_id: str, user_id: str, article_type: str, model_used: str, language: str, prompt: str, content: str, product_id: str = None, template_id: str = None) -> Dict:
    db = get_db()
    oid = str(uuid.uuid4())
    db.execute("INSERT INTO generated_outputs (id, org_id, user_id, article_type, model_used, language, prompt, content, product_id, template_id) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (oid, org_id, user_id, article_type, model_used, language, prompt, content, product_id, template_id))
    db.commit()
    return {"id": oid, "status": "saved"}


def get_outputs(org_id: str, user_id: str = None, limit: int = 20) -> List[Dict]:
    db = get_db()
    sql = "SELECT id, article_type, model_used, language, content, product_id, created_at FROM generated_outputs WHERE org_id=?"
    params = [org_id]
    if user_id: sql += " AND user_id=?"; params.append(user_id)
    sql += " ORDER BY created_at DESC LIMIT ?"; params.append(limit)
    rows = db.execute(sql, tuple(params)).fetchall()
    return [dict(r) for r in rows]


def seed_orionstar_products(org_id: str) -> Dict:
    db = get_db()
    existing = db.execute("SELECT COUNT(*) as cnt FROM products WHERE org_id=?", (org_id,)).fetchone()
    if existing['cnt'] > 0:
        return {"seeded": False, "count": existing['cnt'], "message": "Products already exist"}

    products = [
        {"key":"cleanibot-s55pro","name":"CleaniBot S55 Pro","name_zh":"S55 Pro清洁机器人","desc":"Flagship commercial cleaning robot. 旗舰商用清洁机器人","region":"overseas","cat":"clean","kw":"S55 Pro CleaniBot cleaning 商用 清洁","highlights":["Wash+sweep+vacuum all-in-one","LiDAR obstacle avoidance","Large water tank","<65 dB quiet"],"specs":{"Cleaning":"Wash+Sweep+Vacuum","Navigation":"LiDAR+SLAM","Coverage":"3000+ sqm/h"}},
        {"key":"cleanibot-m1","name":"CleaniBot M1","name_zh":"M1清洁机器人","desc":"Compact cleaning robot. 紧凑型清洁机器人","region":"overseas","cat":"clean","kw":"M1 CleaniBot cleaning 清洁","highlights":["Compact for narrow spaces","Visual SLAM","Auto scheduling"],"specs":{"Type":"Compact Floor Cleaning","Coverage":"1500+ sqm/h","Battery":"6 hours"}},
        {"key":"cleanibot-k1","name":"CleaniBot K1","name_zh":"K1清洁机器人","desc":"K series cleaning robot","region":"overseas","cat":"clean","kw":"K1 CleaniBot cleaning","highlights":["Large venue platform","AI path planning","Fleet management"],"specs":{"Series":"K Series","Modes":"Dry+Wet","Battery":"8 hours"}},
        {"key":"cleanibot-c5","name":"CleaniBot C5","name_zh":"C5清洁机器人","desc":"C series flagship cleaning robot","region":"overseas","cat":"clean","kw":"C5 CleaniBot cleaning","highlights":["Flagship large-venue","4x manual efficiency","40L tanks"],"specs":{"Series":"C Series","Width":"85 cm","Tank":"40L/40L","Coverage":"3500+ sqm/h"}},
        {"key":"cleanibot-yj","name":"CleaniBot YJ Series","name_zh":"YJ系列清洁机器人","desc":"YJ series cleaning robot","region":"overseas","cat":"clean","kw":"YJ CleaniBot cleaning","highlights":["YJ series"],"specs":{}},
        {"key":"cleaning-roadmap","name":"Cleaning Robot Family Roadmap","name_zh":"清洁机器人路线图","desc":"Full cleaning product line roadmap","region":"overseas","cat":"clean","kw":"cleaning roadmap","highlights":["Full line"],"specs":{}},
        {"key":"luckibot","name":"LuckiBot","name_zh":"招财豹","desc":"Signature delivery robot with 5 work modes","region":"overseas","cat":"delivery","kw":"LuckiBot delivery 招财豹","highlights":["5 Work Modes","V-SLAM2.0","Smart Summon"],"specs":{"Modes":"5 modes","Navigation":"V-SLAM2.0","Tray":"3 trays, 30 kg"}},
        {"key":"luckibot-pro","name":"LuckiBot Pro","name_zh":"招财豹Pro","desc":"Upgraded delivery robot with Smart Dish Detection","region":"overseas","cat":"delivery","kw":"LuckiBot Pro Smart Dish","highlights":["Smart Dish Detection","V-SLAM2.0","4 trays 40 kg"],"specs":{"Modes":"5 modes","Smart":"Dish Detection","Tray":"4 trays, 40 kg"}},
        {"key":"luckibot-pro-autodoor","name":"LuckiBot Pro Autodoor","name_zh":"招财豹Pro自动门版","desc":"Auto-door integrated delivery robot","region":"overseas","cat":"delivery","kw":"LuckiBot Pro Autodoor","highlights":["Auto-door integration","Cross-floor delivery"],"specs":{"Base":"LuckiBot Pro","Feature":"Auto-door"}},
        {"key":"carrybot","name":"CarryBot","name_zh":"搬运豹","desc":"World's First MFC Logistics Robot","region":"overseas","cat":"delivery","kw":"CarryBot MFC 搬运豹","highlights":["MFC logistics robot","Precision positioning","3x efficiency"],"specs":{"Type":"MFC Logistics","Payload":"100 kg","Speed":"1.5 m/s"}},
        {"key":"greetingbot-mini","name":"GreetingBot Mini","name_zh":"豹小秘Mini海外版","desc":"Compact service robot with 44 languages","region":"overseas","cat":"voice","kw":"GreetingBot Mini 44 languages","highlights":["44 languages","Compact design","7 scene types"],"specs":{"Type":"Compact Service","Voice":"44 languages"}},
        {"key":"greetingbot-nova","name":"GreetingBot Nova","name_zh":"豹小秘2海外版","desc":"Smart shopping guide robot","region":"overseas","cat":"voice","kw":"GreetingBot Nova Office Reception","highlights":["Office Reception","Exhibition Hall","44 languages"],"specs":{"Type":"Advanced Voice","Voice":"44 languages"}},
        {"key":"greetingbot-ad","name":"GreetingBot AD","name_zh":"豹小秘AD大屏版","desc":"Mobile ad robot with dual screens","region":"overseas","cat":"voice","kw":"GreetingBot AD dual screen advertising","highlights":["14+21.5 dual screens","Qualcomm AI","6-mic array"],"specs":{"Screens":"14+21.5 dual","Chip":"Qualcomm AI","Mapping":"50000 sqm"}},
        {"key":"agentos","name":"AgentOS","name_zh":"AgentOS机器人操作系统","desc":"Robot OS: develop a robot in 10 minutes","region":"overseas","cat":"platform","kw":"AgentOS OS robot system","highlights":["10-min development","Agent Store","44 languages"],"specs":{"Platform":"AgentOS","Dev":"10 minutes","Languages":"44"}},
        {"key":"lucki-button","name":"Lucki-Button","name_zh":"招财豹智能呼叫按钮","desc":"Smart wireless call button","region":"overseas","cat":"platform","kw":"Lucki-Button call button","highlights":["One-press summon","No app needed"],"specs":{"Type":"Wireless Button","Battery":"1-year standby"}},
        {"key":"mowibot","name":"MowiBot","name_zh":"MowiBot移动机器人","desc":"Mobile service robot platform","region":"overseas","cat":"delivery","kw":"MowiBot mobile","highlights":["Versatile platform"],"specs":{}},
        {"key":"ufactory-xarm","name":"UFactory xArm","name_zh":"xArm协作机械臂","desc":"6-axis collaborative robotic arm","region":"overseas","cat":"platform","kw":"xArm collaborative arm","highlights":["6-axis collaborative"],"specs":{}},
        {"key":"orionstar-x1","name":"OrionStar X1","name_zh":"X1清洁机器人","desc":"Next-gen flagship cleaning robot","region":"overseas","cat":"clean","kw":"X1 cleaning robot","highlights":["Next-gen flagship"],"specs":{}},
        {"key":"baoxiaomipro","name":"豹小秘Pro","name_zh":"豹小秘Pro","desc":"新一代AI接待机器人，大模型语音交互","region":"domestic","cat":"voice","kw":"豹小秘Pro AI 接待","highlights":["大模型AI对话","27寸触摸屏","多语言支持"],"specs":{"尺寸":"520x470x1450mm","屏幕":"27寸","续航":"12小时"}},
        {"key":"baoxiaomilite","name":"豹小秘Lite","name_zh":"豹小秘Lite","desc":"轻量级AI接待机器人","region":"domestic","cat":"voice","kw":"豹小秘Lite","highlights":["轻量级设计"],"specs":{}},
        {"key":"baoxiaomimini","name":"豹小秘Mini","name_zh":"豹小秘Mini","desc":"迷你型AI接待机器人","region":"domestic","cat":"voice","kw":"豹小秘Mini","highlights":["迷你尺寸"],"specs":{}},
    ]

    for i, p in enumerate(products):
        pid = str(uuid.uuid4())
        db.execute("INSERT INTO products (id,org_id,product_key,name,name_zh,description,region,category,keywords,sort_order,highlights,specifications) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (pid, org_id, p['key'], p['name'], p['name_zh'], p['desc'], p['region'], p['cat'], p['kw'], i, json.dumps(p['highlights'], ensure_ascii=False), json.dumps(p['specs'], ensure_ascii=False)))
    db.commit()

    # 10 content templates
    templates = [
        ("新闻稿","press_release","article","你是资深科技记者。基于以下产品信息写一篇800-1500字中文新闻稿。标题醒目、导语精炼、3-5小标题。\n{context}"),
        ("GEO优化文章","geo_article","article","你是SEO专家。基于以下产品信息写GEO优化中文文章。含关键词、H2/H3层级、内链建议。\n{context}"),
        ("SEO Article","seo_article","article","Write SEO-optimized article. Include keywords, H2/H3, meta description.\n{context}"),
        ("视频脚本","video_script","article","你是视频编导。写60-90秒产品宣传视频脚本。场景号|画面|旁白|时长。\n{context}"),
        ("海报文案","poster_copy","image","你是广告文案。创作5组海报文案：主标题(10字)+副标题(20字)+行动号召(8字)。\n{context}"),
        ("PPT大纲","ppt_outline","article","你是商务演示专家。生成15页PPT大纲：页标题+核心要点3条+建议配图。\n{context}"),
        ("Social Post","social_post","article","Create 5 social media posts under 280 chars each with hashtags.\n{context}"),
        ("竞品对比","comparison","article","你是产品分析师。写竞品对比文章：参数对比表+优劣势+场景推荐。\n{context}"),
        ("客户案例","case_study","article","你是商业撰稿人。写客户成功案例：背景+挑战+方案+成果+评价。\n{context}"),
        ("产品手册","product_manual","article","你是技术文档工程师。写产品使用手册：概述+规格+入门+功能+FAQ。\n{context}"),
    ]
    for name, atype, family, prompt in templates:
        tid = str(uuid.uuid4())
        db.execute("INSERT INTO content_templates (id,org_id,name,article_type,category,model_family,prompt_template,description) VALUES (?,?,?,?,?,?,?,?)",
            (tid, org_id, name, atype, family[:20], family, prompt, ""))
    db.commit()

    return {"seeded": True, "count": len(products), "templates": len(templates)}


def _product_dict(row) -> Dict:
    d = dict(row)
    for f in ['assets','highlights','specifications','scenes','cases','solutions']:
        if f in d and isinstance(d[f], str):
            try: d[f] = json.loads(d[f])
            except: pass
    return d
