# -*- coding: utf-8 -*-
import os, json, time

def build():
    login_html = '''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>OrionStar 产品资料知识库</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:system-ui,-apple-system,sans-serif;background:#FFFFFF;color:#111827;overflow-x:hidden}
a{text-decoration:none;color:inherit}
:root{--accent:#2563EB;--radius:8px}

.logo-star{display:inline-block;width:14px;height:14px;background:#0A2E6C;clip-path:polygon(50% 0,60% 40%,100% 50%,60% 60%,50% 100%,40% 60%,0 50%,40% 40%);vertical-align:middle;margin-right:4px;flex-shrink:0}

/* Login */
#loginPage{position:fixed;inset:0;z-index:9999;display:flex;align-items:center;justify-content:center;background:#F9FAFB}
.login-box{width:400px;max-width:90vw;background:#fff;border-radius:12px;border:1px solid #E5E7EB;padding:44px 36px 36px;text-align:center}
.login-logo{display:flex;align-items:center;justify-content:center;gap:8px;font-size:20px;font-weight:800;color:#0A2E6C;margin-bottom:8px}
.login-box h2{font-size:18px;font-weight:700;color:#111827;margin-bottom:4px}
.login-sub{color:#9CA3AF;font-size:13px;margin-bottom:24px}
#loginError{color:#ef4444;font-size:13px;min-height:22px;margin-bottom:10px}
.field{display:flex;align-items:center;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:0 14px;margin-bottom:14px}
.field span{font-size:16px;margin-right:10px;color:#9CA3AF}
.field input{flex:1;background:none;border:none;outline:none;color:#111827;font-size:14px;padding:13px 0;font-family:inherit}
.field input::placeholder{color:#D1D5DB}
.login-btn{width:100%;padding:13px;background:#2563EB;color:#fff;border:none;border-radius:8px;font-size:15px;font-weight:600;cursor:pointer;display:block;transition:.2s}
.login-btn:hover{background:#1D4ED8}
.login-hint{font-size:12px;color:#9CA3AF;margin-top:20px}
.hidden{display:none!important}

/* App layout */
#app{display:flex;height:100vh;overflow:hidden;background:#fff}
.sidebar{width:260px;min-width:260px;background:#F8FAFF;display:flex;flex-direction:column;border-right:1px solid #E5E7EB}
.sidebar-header{padding:16px 20px;border-bottom:1px solid #E5E7EB;display:flex;align-items:center;gap:8px}
.sidebar-header .logo{font-size:15px;font-weight:800;color:#0A2E6C;letter-spacing:1px;display:flex;align-items:center}
.sidebar-search{padding:12px 14px;border-bottom:1px solid #E5E7EB}
.sidebar-search .search-wrap{position:relative;display:flex;align-items:center}
.sidebar-search .search-icon{position:absolute;left:10px;color:#9CA3AF;font-size:13px;pointer-events:none}
.sidebar-search input{width:100%;padding:8px 12px 8px 30px;border-radius:8px;border:1px solid #E5E7EB;background:#F9FAFB;color:#111827;font-size:13px;outline:none;transition:.2s;font-family:inherit}
.sidebar-search input:focus{border-color:#2563EB;background:#fff}
.sidebar-search input::placeholder{color:#D1D5DB}
.nav-tree{flex:1;overflow-y:auto;padding:8px 0}
.nav-item{padding:7px 12px;font-size:13px;color:#111827;cursor:pointer;transition:.15s;display:flex;align-items:center;gap:8px;border-radius:6px;margin:1px 8px}
.nav-item:hover{background:#EFF6FF}
.nav-item.active{background:#DBEAFE;color:#2563EB;font-weight:500}
.nav-cat{font-size:11px;font-weight:500;color:#9CA3AF;padding:10px 20px 4px;letter-spacing:.8px;text-transform:uppercase}
.nav-region{font-size:13px;font-weight:600;color:#111827;padding:10px 20px 4px}
.nav-sidebar-footer{padding:12px 14px;border-top:1px solid #E5E7EB}
.nav-footer-title{font-size:11px;font-weight:500;color:#9CA3AF;letter-spacing:.8px;text-transform:uppercase;margin-bottom:6px;padding:0 4px}
.nav-footer-link{display:flex;align-items:center;gap:8px;padding:7px 10px;font-size:13px;color:#111827;cursor:pointer;border-radius:6px;transition:.15s}
.nav-footer-link:hover{background:#EFF6FF}

/* Main content */
.main{flex:1;overflow-y:auto;background:#FFFFFF;padding:24px 32px}
.main-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:20px}
.breadcrumb{font-size:13px;color:#9CA3AF;display:flex;align-items:center;gap:4px}
.breadcrumb span{color:#2563EB;cursor:pointer;font-weight:500}
.breadcrumb span:hover{text-decoration:underline}
.user-area{display:flex;align-items:center;gap:8px;font-size:12px;color:#9CA3AF}

/* Hero section */
.hero{background:#fff;padding:36px 0;margin-bottom:24px;border-bottom:1px solid #F3F4F6}
.hero h1{font-size:28px;font-weight:700;margin-bottom:8px;color:#111827;letter-spacing:-.3px}
.hero p{font-size:15px;color:#6B7280;margin-bottom:20px}
.hero-search{display:flex;align-items:center;background:#F3F4F6;border-radius:12px;padding:4px 6px 4px 16px;max-width:500px;border:2px solid transparent;transition:.2s}
.hero-search:focus-within{background:#fff;border-color:#2563EB}
.hero-search input{flex:1;background:none;border:none;outline:none;color:#111827;font-size:14px;font-family:inherit;padding:8px 0}
.hero-search input::placeholder{color:#9CA3AF}
.hero-search button{background:#2563EB;color:#fff;border:none;border-radius:8px;padding:9px 20px;font-size:13px;font-weight:600;cursor:pointer;flex-shrink:0;transition:.2s}
.hero-search button:hover{background:#1D4ED8}

/* Stats bar */
.stats-bar{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:24px}
.stat-card{background:#F9FAFB;border-radius:8px;padding:18px 20px;display:flex;align-items:center;gap:14px;transition:.2s}
.stat-card:hover{background:#F3F4F6}
.stat-icon{width:40px;height:40px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0}
.stat-icon.blue{background:#EFF6FF}
.stat-icon.cyan{background:#E0F7FF}
.stat-icon.green{background:#ECFDF5}
.stat-icon.orange{background:#FFF7ED}
.stat-info h3{font-size:28px;font-weight:700;color:#2563EB;line-height:1.1}
.stat-info p{font-size:12px;color:#9CA3AF;margin-top:3px}

/* Section headers */
.section-hd{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #F3F4F6}
.section-hd h2{font-size:15px;font-weight:600;color:#111827}
.section-hd a{font-size:12px;color:#2563EB;cursor:pointer}

/* Category cards */
.cat-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:24px}
.cat-card{background:#F9FAFB;border-radius:8px;padding:18px 16px;cursor:pointer;transition:.2s;display:flex;align-items:center;gap:14px}
.cat-card:hover{background:#EFF6FF;box-shadow:0 2px 12px rgba(0,0,0,0.08)}
.cat-card .cat-icon{width:40px;height:40px;border-radius:8px;background:#EFF6FF;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0;color:#2563EB}
.cat-card .cat-info h3{font-size:13px;font-weight:600;color:#111827;margin-bottom:3px}
.cat-card .cat-info p{font-size:12px;color:#9CA3AF}

/* Recent updates */
.recent-list{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:24px}
.recent-item{background:#F9FAFB;border-radius:8px;padding:14px 16px;cursor:pointer;transition:.15s;display:flex;align-items:center;gap:12px}
.recent-item:hover{background:#fff;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.recent-dot{width:7px;height:7px;border-radius:50%;background:#2563EB;flex-shrink:0}
.ri-info h4{font-size:13px;font-weight:500;color:#111827}
.ri-info p{font-size:12px;color:#9CA3AF;margin-top:2px}
.recent-badge{font-size:11px;background:#EFF6FF;color:#2563EB;border-radius:4px;padding:2px 8px;margin-left:auto;flex-shrink:0;font-weight:600}

/* Hot tags */
.hot-tags{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px}
.hot-tag{padding:6px 14px;border-radius:20px;font-size:13px;color:#374151;background:#F9FAFB;border:1px solid #E5E7EB;cursor:pointer;transition:.2s}
.hot-tag:hover{color:#2563EB;border-color:#2563EB;background:#EFF6FF}

/* Product detail */
.product-detail{overflow:hidden}
.product-header{padding:24px 0;border-bottom:1px solid #F3F4F6}
.product-header h1{font-size:24px;font-weight:700;color:#111827}
.product-header .tag{display:inline-block;padding:2px 10px;border-radius:4px;font-size:11px;margin-left:10px;vertical-align:middle}
.tag-onsale{background:#ECFDF5;color:#065f46}
.tag-new{background:#EFF6FF;color:#2563EB;font-weight:600}
.product-header .zh{color:#9CA3AF;font-size:14px;margin-top:4px}
.product-header .desc{color:#6B7280;font-size:14px;margin-top:8px;line-height:1.7}
.assets-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;padding:16px 0}
.asset-card{background:#F9FAFB;border-radius:8px;padding:14px 16px;cursor:pointer;transition:.15s;display:flex;align-items:center;gap:12px}
.asset-card:hover{background:#fff;box-shadow:0 2px 8px rgba(0,0,0,0.08)}
.asset-icon{width:40px;height:40px;border-radius:8px;background:#EFF6FF;display:flex;align-items:center;justify-content:center;font-size:19px;flex-shrink:0;color:#2563EB}
.asset-card .info h4{font-size:13px;font-weight:500;color:#111827}
.asset-card .info p{font-size:12px;color:#9CA3AF;margin:0}

/* Related products */
.related-section{padding:20px 0;border-top:1px solid #F3F4F6}
.related-section h3{font-size:14px;font-weight:600;color:#111827;margin-bottom:12px}
.related-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px}
.related-card{background:#F9FAFB;border-radius:8px;padding:12px;cursor:pointer;transition:.2s;text-align:center}
.related-card:hover{background:#EFF6FF;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.rc-name{font-size:13px;font-weight:500;color:#111827;margin-bottom:2px}
.rc-zh{font-size:11px;color:#9CA3AF}

/* Search results */
.search-results{padding:0}
.search-hit{background:#F9FAFB;border-radius:8px;padding:14px 16px;margin-bottom:8px;cursor:pointer;transition:.15s}
.search-hit:hover{background:#fff;box-shadow:0 2px 8px rgba(0,0,0,0.06)}
.search-hit h3{font-size:14px;font-weight:500;color:#111827}
.search-hit p{font-size:12px;color:#9CA3AF;margin-top:3px}

/* Scrollbar */
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:#E5E7EB;border-radius:2px}
::-webkit-scrollbar-thumb:hover{background:#9CA3AF}

.mobile-menu-btn{display:none;position:fixed;top:12px;left:12px;z-index:10001;width:40px;height:40px;border-radius:8px;border:1px solid #E5E7EB;background:#fff;color:#111827;font-size:20px;cursor:pointer;align-items:center;justify-content:center}
.sidebar-overlay{display:none;position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:9997}
@media(max-width:768px){
  .mobile-menu-btn{display:flex}
  .sidebar{position:fixed;left:0;top:0;bottom:0;z-index:10000;transform:translateX(-100%);transition:transform .3s ease}
  .sidebar.open{transform:translateX(0)}
  .sidebar-overlay.show{display:block}
  .main{padding:56px 16px 16px}
  .stats-bar{grid-template-columns:repeat(2,1fr)}
  .cat-grid{grid-template-columns:repeat(2,1fr)}
  .recent-list{grid-template-columns:1fr}
  .assets-grid{grid-template-columns:1fr}
  .hero{padding:24px 0}
  .hero h1{font-size:22px}
}
/* AI撰稿面板 */
.ai-btn{background:#2563EB;color:#fff;border:none;border-radius:8px;padding:8px 16px;font-size:13px;font-weight:600;cursor:pointer;display:flex;align-items:center;gap:6px;transition:.2s;flex-shrink:0;white-space:nowrap}
.ai-btn:hover{background:#1D4ED8}
.ai-panel{background:#fff;border:1px solid #E5E7EB;border-radius:8px;box-shadow:0 4px 16px rgba(0,0,0,.08);padding:20px;margin-top:12px}
.ai-section-title{font-size:13px;font-weight:600;color:#111827;margin-bottom:10px}
.ai-divider{border:none;border-top:1px solid #F3F4F6;margin:16px 0}
.model-cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(155px,1fr));gap:8px;margin-bottom:4px}
.model-card{border:2px solid #E5E7EB;border-radius:8px;padding:10px 12px;cursor:pointer;transition:.2s;background:#fff;text-align:left;font-size:13px;color:#374151}
.model-card:hover{border-color:#93C5FD;background:#F0F9FF}
.model-card.selected{border-color:#2563EB;background:#EFF6FF}
.mc-name{font-size:13px;font-weight:700;color:#111827;margin-bottom:2px}
.mc-co{font-size:11px;color:#9CA3AF;margin-bottom:4px}
.mc-score{font-size:12px;font-weight:600;color:#F59E0B;margin-bottom:3px}
.mc-desc{font-size:11px;color:#6B7280;line-height:1.4}
.model-card.selected .mc-name{color:#2563EB}
.article-type-group{margin-bottom:10px}
.article-type-group-label{font-size:12px;font-weight:500;color:#9CA3AF;margin-bottom:6px}
.article-type-tags{display:flex;gap:6px;flex-wrap:wrap}
.article-type-tag{padding:5px 12px;border-radius:4px;font-size:12px;font-weight:500;color:#374151;background:#F3F4F6;border:1px solid #E5E7EB;cursor:pointer;transition:.2s}
.article-type-tag:hover{border-color:#93C5FD;background:#EFF6FF;color:#2563EB}
.article-type-tag.selected{background:#2563EB;color:#fff;border-color:#2563EB}
.material-checks{display:flex;gap:8px;flex-wrap:wrap}
.material-check{display:flex;align-items:center;gap:5px;padding:5px 10px;border-radius:4px;font-size:12px;color:#374151;background:#F9FAFB;border:1px solid #E5E7EB;cursor:pointer}
.material-check input[type=checkbox]{accent-color:#2563EB;cursor:pointer}
.ref-card-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:12px;margin:12px 0}
.ref-card{border:1px solid #E5E7EB;border-radius:8px;padding:12px;cursor:pointer;transition:all .2s;background:#fff;position:relative}
.ref-card:hover{border-color:#2563EB}
.ref-card.active{border-color:#2563EB;background:#EFF6FF}
.ref-card.active::after{content:\'✓\';position:absolute;top:6px;right:8px;color:#2563EB;font-weight:bold}
.ref-card-img{width:40px;height:40px;border-radius:6px;object-fit:cover;margin-bottom:8px}
.ref-card-title{font-size:13px;font-weight:600;color:#111827;margin-bottom:4px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ref-card-desc{font-size:11px;color:#6B7280;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.ai-generate-btn{background:#2563EB;color:#fff;border:none;border-radius:8px;padding:10px 24px;font-size:14px;font-weight:600;cursor:pointer;transition:.2s}
.ai-generate-btn:hover{background:#1D4ED8}
.ai-generate-btn:disabled{background:#9CA3AF;cursor:not-allowed}
.ai-result-area{margin-top:16px;background:#F9FAFB;border:1px solid #E5E7EB;border-radius:8px;padding:16px}
.ai-result-text{font-size:13px;color:#111827;line-height:1.8;min-height:120px;max-height:680px;overflow-y:auto}
.art-section-label{font-size:12px;font-weight:700;color:#2563EB;margin:14px 0 8px;padding-bottom:4px;border-bottom:2px solid #EFF6FF}
.art-titles p{font-size:14px;color:#111827;margin:4px 0;line-height:1.8}
.art-images{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:10px 0}
.art-img-item{text-align:center}
.art-img-cap{font-size:11px;color:#6B7280;margin-top:4px;line-height:1.4}
.art-body p{font-size:13px;color:#111827;line-height:2;margin-bottom:10px}
.art-body strong{color:#374151}
.art-wc{font-size:12px;color:#9CA3AF;text-align:right;margin-top:12px;padding-top:8px;border-top:1px solid #F3F4F6}
.ai-result-actions{display:flex;gap:8px;margin-top:12px}
.ai-result-btn{padding:7px 16px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;transition:.2s;border:1px solid}
.ai-copy-btn{background:#EFF6FF;color:#2563EB;border-color:#BFDBFE}
.ai-copy-btn:hover{background:#DBEAFE}
.ai-regen-btn{background:#F3F4F6;color:#374151;border-color:#E5E7EB}
.ai-regen-btn:hover{background:#E5E7EB}
.model-categories{display:grid;grid-template-columns:repeat(3,1fr);gap:16px}
.model-category{border:1px solid #E5E7EB;border-radius:8px;padding:16px}
.model-category-title{font-size:14px;font-weight:700;color:#0A2E6C;margin-bottom:12px;text-align:center;padding-bottom:8px;border-bottom:2px solid #2563EB}
.model-dropdown{position:relative;margin-bottom:16px}
.model-dropdown-header{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border:1px solid #E5E7EB;border-radius:8px;cursor:pointer;background:#fff;font-size:14px}
.model-dropdown-header:hover{border-color:#2563EB}
.model-dropdown-arrow{transition:transform .2s;font-size:12px;color:#6B7280}
.model-dropdown.open .model-dropdown-arrow{transform:rotate(180deg)}
.model-dropdown-body{display:none;position:absolute;top:100%;left:0;right:0;z-index:100;background:#fff;border:1px solid #E5E7EB;border-radius:8px;margin-top:4px;padding:16px;box-shadow:0 8px 24px rgba(0,0,0,.1)}
.model-dropdown.open .model-dropdown-body{display:block}
.lang-dropdown{position:relative;margin-top:4px}
.lang-dropdown-header{display:flex;align-items:center;justify-content:space-between;padding:10px 16px;border:1px solid #E5E7EB;border-radius:8px;cursor:pointer;background:#fff;font-size:13px}
.lang-dropdown-header:hover{border-color:#2563EB}
.lang-dropdown-arrow{transition:transform .2s;font-size:12px;color:#6B7280}
.lang-dropdown.open .lang-dropdown-arrow{transform:rotate(180deg)}
.lang-dropdown-body{display:none;position:absolute;top:100%;left:0;right:0;z-index:100;background:#fff;border:1px solid #E5E7EB;border-radius:8px;margin-top:4px;padding:12px;box-shadow:0 8px 24px rgba(0,0,0,.1);max-height:280px;overflow-y:auto}
.lang-dropdown.open .lang-dropdown-body{display:block}
.lang-item{display:inline-block;padding:4px 10px;margin:2px;border-radius:4px;font-size:12px;cursor:pointer;color:#374151;background:#F3F4F6;border:1px solid #E5E7EB;transition:.15s}
.lang-item:hover{color:#2563EB;border-color:#93C5FD;background:#EFF6FF}
.lang-item.selected{color:#fff;background:#2563EB;border-color:#2563EB}
</style>
</head>
<body>'''

    login_page = ''

    app_html = '''
<div id="app" style="display:flex">
  <button class="mobile-menu-btn" onclick="toggleSidebar()">&#9776;</button>
  <div class="sidebar-overlay" id="sidebarOverlay" onclick="toggleSidebar()"></div>
  <div class="sidebar" id="sidebar">
    <div class="sidebar-header">
      <span class="logo"><span class="logo-star"></span>ORIONSTAR</span>
      <span style="font-size:10px;color:#9CA3AF;margin-left:auto">产品资料知识库</span>
    </div>
    <div class="sidebar-search">
      <div class="search-wrap">
        <span class="search-icon">&#128269;</span>
        <input type="text" id="searchInput" placeholder="搜索产品、物料..." oninput="doSearch()" />
      </div>
    </div>
    <div id="navTree" class="nav-tree"></div>
    <div class="nav-sidebar-footer">
      <div class="nav-footer-title">快速入口</div>
      <div class="nav-footer-link" onclick="selectItem('corp-intro')">&#127970; 公司介绍</div>
      <div class="nav-footer-link" onclick="showSolutions()">&#128161; 解决方案</div>
      <div class="nav-footer-link" onclick="showLangs()">&#127760; 多语种物料</div>
    </div>
  </div>
  <div class="main">
    <div class="main-header">
      <div class="breadcrumb" id="breadcrumb">&#127968; 首页</div>
      <div class="user-area" id="userArea">OrionStar KB</div>
    </div>
    <div id="contentArea"></div>
  </div>
</div>
<script>
const F="https://cheetah-mobile.feishu.cn/drive/folder/";
const F2="https://cheeth-mobile.feishu.cn/drive/folder/";
const VW="https://cheetah-mobile.feishu.cn/wiki/IvxTww5HeiDh1tkErwscgY6Ankc";
const PRODUCTS=[
  {id:"cleanibot-s55pro",name:"CleaniBot S55 Pro",zh:"S55 Pro清洁机器人",desc:"Flagship commercial cleaning robot. 旗舰商用清洁机器人，集洗地、扫地、吸尘于一体",region:"overseas",cat:"clean",kw:"S55 Pro CleaniBot cleaning 商用 清洁 洗地 扫地",
   assets:{ppt:F+"E8gDf2jkjl1yI7dV4iycx4vcnFd",brochure:F+"GVBpfVERllzGCOdUvlbc9kb6ntd",image:"orionstar-images/product1.png",video:F+"BBMxf2q2GlZrYadMfVZczQFqnnf",competitor:F+"RlohfRk8ElAbwUd2rfbcuQPjn7e",web:"https://en.orionstar.com/products/cleanibot-s55-pro.html",video_wiki:VW},
   highlights:["Flagship commercial cleaning: wash + sweep + vacuum all-in-one","Advanced LiDAR obstacle avoidance and intelligent path planning","Large-capacity clean/dirty water tank for extended operation","Quiet night operation mode — below 65 dB","Competitor-verified technical advantages","Supports multiple floor surface types"],
   specs:{"Cleaning Modes":"Wash + Sweep + Vacuum all-in-one","Navigation":"LiDAR + SLAM","Coverage":"3000+ sqm/h","Battery Life":"8 hours","Water Tank":"Large capacity clean/dirty water tanks","Noise":"<65 dB quiet mode"},
   scenes:["Shopping mall corridors and lobbies","Office building common areas","Hotel public spaces","Hospital corridors and wards","Airport terminals","Convention and exhibition centers"],
   cases:[{"name":"International Shopping Mall","url":"https://en.orionstar.com/products/cleanibot-s55-pro.html","desc":"3x efficiency vs manual cleaning, covers 5000 sqm daily"},{"name":"5-Star Hotel","url":"https://en.orionstar.com/products/cleanibot-s55-pro.html","desc":"Automated night cleaning of lobby and corridors, cleaning staff reduced 40%"},{"name":"International Airport","url":"https://en.orionstar.com/products/cleanibot-s55-pro.html","desc":"Terminal floor cleaning 24/7 autonomous operation, zero passenger disruption"},{"name":"Hospital Campus","url":"https://en.orionstar.com/products/cleanibot-s55-pro.html","desc":"Sterile-standard floor cleaning in corridors, cross-infection risk reduced"}]},
  {id:"cleanibot-m1",name:"CleaniBot M1",zh:"M1清洁机器人",desc:"Compact cleaning robot for smaller spaces. 紧凑型清洁机器人，适用于较小空间",region:"overseas",cat:"clean",kw:"M1 CleaniBot cleaning compact 清洁 紧凑",
   assets:{ppt:F+"RQzofNMoNlMG1odUXnbcFIOknBf",image:"orionstar-images/product2.png",video:F+"XnxEf4tr6lGaYYdfnZNcZB0knNf",case:F+"EVsRf0t2FlSCS7dVMSDck4akn9b",web:"https://en.orionstar.com/products/cleanibot-m1.html",video_wiki:VW},
   highlights:["Compact design optimised for smaller and narrow spaces","Smart navigation for tight indoor corridors","Efficient daily cleaning routines with auto scheduling","Customer case-proven performance across multiple verticals","Quiet operation suitable for occupied spaces","Quick deployment — up and running within 1 hour"],
   specs:{"Type":"Compact Floor Cleaning Robot","Navigation":"Visual SLAM","Coverage":"1500+ sqm/h","Battery Life":"6 hours","Charging":"Auto dock return","Noise Level":"<60 dB"},
   scenes:["Restaurant dining areas","Retail store aisles","Office corridors","Small hotel lobbies","Healthcare waiting rooms","Community centres"],
   cases:[{"name":"Restaurant Chain","url":"https://en.orionstar.com/products/cleanibot-m1.html","desc":"Daily floor cleaning between dining hours, cleaning labour reduced 50%"},{"name":"Retail Store","url":"https://en.orionstar.com/products/cleanibot-m1.html","desc":"After-hours automated cleaning, store always ready for opening"},{"name":"Healthcare Clinic","url":"https://en.orionstar.com/products/cleanibot-m1.html","desc":"Sterile floor maintenance in waiting areas, consistent hygiene standards"}]},
  {id:"cleanibot-k1",name:"CleaniBot K1",zh:"K1清洁机器人",desc:"Cleaning robot, K series. K系列清洁机器人",region:"overseas",cat:"clean",kw:"K1 CleaniBot cleaning 清洁",
   assets:{ppt:F+"IbyDfVnP4l0CujdaZHMcbbBHnUe",video:F+"VMBXf3yDllCPi7dDUFvcR3rxnJf",image:"orionstar-images/product3.png",web:"https://en.orionstar.com/products/cleanibot-k1.html",video_wiki:VW},
   highlights:["K-series commercial cleaning platform for large venues","Advanced AI path planning with full floor coverage","Multi-surface cleaning: dry and wet dual mode","Fleet management ready — centralised monitoring","Remote diagnostics and OTA update support","Efficient deployment for commercial and industrial sites"],
   specs:{"Series":"K Series","Type":"Commercial Cleaning Robot","Navigation":"LiDAR SLAM","Cleaning Modes":"Dry + Wet","Battery Life":"8 hours","Fleet":"Multi-unit centralised management"},
   scenes:["Large commercial spaces","Education campuses","Logistics warehouses","Convention centres","Multi-floor office buildings","Industrial facilities"],
   cases:[{"name":"University Campus","url":"https://en.orionstar.com/products/cleanibot-k1.html","desc":"Campus-wide deployment, manual cleaning labour reduced 60%"},{"name":"Logistics Warehouse","url":"https://en.orionstar.com/products/cleanibot-k1.html","desc":"24/7 automated floor maintenance, clean working environment maintained"},{"name":"Convention Centre","url":"https://en.orionstar.com/products/cleanibot-k1.html","desc":"Rapid cleanup between events, enabling faster venue turnaround"}]},
  {id:"cleanibot-c5",name:"CleaniBot C5",zh:"C5清洁机器人",desc:"Cleaning robot, C series. C系列清洁机器人",region:"overseas",cat:"clean",kw:"C5 CleaniBot cleaning 清洁",
   assets:{ppt:F+"Lna6fb6wMl9I6HdFhytcvhz9nUb",video:F+"PvMyfTcoDlNbFfd6JMqcmrrxnKX",image:"orionstar-images/product1.png",web:"https://en.orionstar.com/products/cleanibot-c5.html",video_wiki:VW},
   highlights:["C-series flagship cleaning solution for large-scale venues","Complete documentation package: product + user + deployment manuals","Enterprise-grade deployment support and SLA","Proven ROI with 4x efficiency vs manual cleaning","Comprehensive global compliance certifications","Centralised fleet management dashboard for multi-site operators"],
   specs:{"Series":"C Series","Type":"Commercial Floor Care Robot","Navigation":"LiDAR + Vision SLAM","Cleaning Width":"85 cm","Water Tank":"Clean 40 L / Dirty 40 L","Coverage":"3500+ sqm/h","Battery Life":"10 hours"},
   scenes:["Large shopping centres","Airport terminals","Hospital campuses","Hotel lobbies and corridors","Corporate headquarters","Convention and exhibition facilities"],
   cases:[{"name":"Large Shopping Centre","url":"https://en.orionstar.com/products/cleanibot-c5.html","desc":"Full floor care solution, 4x efficiency vs manual cleaning, 80% labour cost saving"},{"name":"International Airport","url":"https://en.orionstar.com/products/cleanibot-c5.html","desc":"Terminal-wide automated cleaning 24/7, hygiene standards consistently met"},{"name":"5-Star Hotel Chain","url":"https://en.orionstar.com/products/cleanibot-c5.html","desc":"Fleet deployed across multiple properties with centralised management dashboard"}]},
  {id:"cleanibot-yj",name:"CleaniBot YJ Series",zh:"YJ系列清洁机器人",desc:"Cleaning robot YJ series lineup. YJ系列清洁机器人产品线",region:"overseas",cat:"clean",kw:"YJ CleaniBot cleaning 清洁",assets:{image:"orionstar-images/product2.png",video_wiki:VW}},
  {id:"cleaning-roadmap",name:"Cleaning Robot Family Roadmap",zh:"清洁机器人产品路线图",desc:"Full cleaning product line roadmap. 全系列清洁产品路线图",region:"overseas",cat:"clean",kw:"cleaning roadmap 清洁 路线图",
   assets:{ppt:F+"RtFQffaiplmBnwdqBHkc7luNnFg",video_wiki:VW,image:"orionstar-images/product3.png"}},
  {id:"luckibot",name:"LuckiBot",zh:"招财豹",desc:"Signature delivery robot with 5 work modes (Delivery/Soliciting/Leading/Cruising/Return Tray), Marker Free V-SLAM2.0 code-free mapping, Smart Positioning and Smart Summon. 标志性配送机器人，5种工作模式、无码建图、智能召唤",region:"overseas",cat:"delivery",kw:"LuckiBot delivery 招财豹 配送 送餐 V-SLAM Marker Free Smart Summon Smart Positioning",
   assets:{ppt:F2+"SOh5fRE6PlWSyqdNYNlcyqYfnZx",brochure:F2+"KKG1f27helvrdcdNNcWc1S01nZf",image:"orionstar-images/delivery1.png",web:"https://cn.orionstar.com/zhcaibao-zh.html",video_wiki:VW},
   highlights:["5 Work Modes: Delivery / Soliciting / Leading / Cruising / Return Tray","Marker Free V-SLAM2.0 — map without QR codes","Smart Positioning for precise autonomous navigation","Smart Summon — one-button robot calling","Extended battery version + bottom-charging version available","Official media-covered signature delivery robot"],
   specs:{"Work Modes":"5 modes: Delivery / Soliciting / Leading / Cruising / Return Tray","Navigation":"Marker Free V-SLAM2.0","Mapping":"Code-free, no QR installation required","Tray Capacity":"3 trays, 30 kg total","Battery":"Standard and extended battery versions","Charging":"Auto docking + bottom-charging version"},
   scenes:["Restaurant table service and delivery","Hotel room and corridor delivery","Office supply and document delivery","Hospital medication and meal delivery","Casino floor beverage service","Retail store in-aisle delivery"],
   cases:[{"name":"Restaurant Chain (Asia)","url":"https://en.orionstar.com/products/luckibot.html","desc":"Table delivery in peak hours, server workload reduced 40%, customer satisfaction up"},{"name":"5-Star Hotel","url":"https://en.orionstar.com/products/luckibot.html","desc":"Room amenity delivery via Smart Summon, guest satisfaction score improved 25%"},{"name":"Office Complex","url":"https://en.orionstar.com/products/luckibot.html","desc":"Document and mail delivery across floors, 80+ deliveries per day"},{"name":"Hospital","url":"https://en.orionstar.com/products/luckibot.html","desc":"Medication and meal delivery, nurse walking distance reduced 30%"},{"name":"Casino Floor","url":"https://en.orionstar.com/products/luckibot.html","desc":"Beverage and snack delivery to gaming tables, enhanced premium guest experience"}]},
  {id:"luckibot-pro",name:"LuckiBot Pro",zh:"招财豹Pro",desc:"Upgraded delivery robot with Marker Free V-SLAM2.0 and Smart Dish Detection (智能感应托盘). 升级版配送机器人，无码建图V-SLAM2.0、智能感应托盘，5种工作模式",region:"overseas",cat:"delivery",kw:"LuckiBot Pro delivery 招财豹Pro V-SLAM Smart Dish Detection 智能感应托盘 Marker Free",
   assets:{ppt:F+"IDrufEI4MluH0hdJFUqc2bEQn7c",brochure:F+"ChkKf7ZyVlNzWgdZ08cc2bxgngh",image:"orionstar-images/delivery2.png",video:F+"OcoQfQPFll74yudi9czckQvanTh",case:F+"ESkmfmo3alv6SJdzKVRceYljn9e",web:"https://cn.orionstar.com/lucki-pro.html",video_wiki:VW},
   highlights:["Smart Dish Detection (智能感应托盘) — auto-sense tray loading/unloading","Marker Free V-SLAM2.0 — next-gen code-free mapping upgrade","5 Work Modes: Delivery / Soliciting / Leading / Cruising / Return Tray","3 Major Technical Highlights vs standard LuckiBot","Higher capacity and enhanced stability","Side-by-side comparison proves advantage over LuckiBot"],
   specs:{"Work Modes":"5 modes: Delivery / Soliciting / Leading / Cruising / Return Tray","Navigation":"Marker Free V-SLAM2.0","Smart Feature":"Smart Dish Detection (auto tray sensing)","Tray Capacity":"4 trays, 40 kg total","Charging":"Auto docking"},
   scenes:["High-end restaurant fine dining service","Luxury hotel room delivery","Hospital clinical supply and medication delivery","Large office complex logistics","Convention centre food and beverage service","Resort and spa on-demand delivery"],
   cases:[{"name":"High-End Restaurant","url":"https://en.orionstar.com/products/luckibot-pro.html","desc":"Smart Dish Detection enables seamless table delivery, 50% faster than standard model"},{"name":"Luxury Hotel","url":"https://en.orionstar.com/products/luckibot-pro.html","desc":"Pro room delivery service, guest response time under 10 minutes"},{"name":"Hospital Clinical Department","url":"https://en.orionstar.com/products/luckibot-pro.html","desc":"Precise medication delivery with Smart Dish Detection, 0 delivery errors"},{"name":"Corporate Headquarters","url":"https://en.orionstar.com/products/luckibot-pro.html","desc":"Multi-floor catering delivery for executive floors, 100+ deliveries daily"}]},
  {id:"luckibot-pro-autodoor",name:"LuckiBot Pro Autodoor",zh:"招财豹Pro自动门版",desc:"Auto-door integrated delivery robot for seamless cross-room and cross-floor delivery. 自动门对接配送机器人，实现无感知跨间/跨层配送",region:"overseas",cat:"delivery",kw:"LuckiBot Pro Autodoor 招财豹 自动门 cross-floor delivery auto-door",
   assets:{ppt:F+"QxlRf6ZdrlSRgCdQoEVc1z4InMT",image:"orionstar-images/delivery2.png",web:"https://cn.orionstar.com/autodoor-zh.html",video_wiki:VW},
   highlights:["Seamless auto-door integration — hands-free cross-room delivery","Compatible with standard commercial automatic door systems","Enables cross-floor delivery without manual door operation","Hotel and hospital optimised deployment design","All LuckiBot Pro capabilities included","Promotes fully autonomous delivery workflows"],
   specs:{"Base Model":"LuckiBot Pro","Special Feature":"Auto-door integration module","Compatible Doors":"Standard commercial automatic doors","Door Trigger":"Infrared / relay compatible","Navigation":"Marker Free V-SLAM2.0","Work Modes":"5 modes including cross-door delivery"},
   scenes:["Hotel guest room floor delivery","Hospital ward medication delivery","Office floor-to-floor document delivery","Residential care facility service delivery","Clean room and restricted area logistics","Multi-zone building autonomous logistics"],
   cases:[{"name":"International Hotel Chain","url":"https://en.orionstar.com/products/luckibot-pro.html","desc":"Fully automated room delivery through auto-doors, zero staff required for routine deliveries"},{"name":"Hospital Ward","url":"https://en.orionstar.com/products/luckibot-pro.html","desc":"Cross-ward medication delivery through fire doors, 24/7 reliable autonomous operation"},{"name":"Corporate Headquarters","url":"https://en.orionstar.com/products/luckibot-pro.html","desc":"Floor-to-floor delivery through security doors, seamless access control system integration"}]},
  {id:"carrybot",name:"CarryBot",zh:"搬运豹",desc:"World's First Micro Fulfillment Center (MFC) Logistics Robot for factory and warehouse delivery with precision positioning. 全球首款微型履约中心物流机器人，工厂精准配送",region:"overseas",cat:"delivery",kw:"CarryBot factory 搬运豹 工厂 物流 Micro Fulfillment Center MFC precision positioning",
   assets:{ppt:F+"TszUff9bMlHmMfdr81qceqMMnAe",brochure:F+"RdT2fEYhAli5S9dxEPXcKn56nSg",image:"orionstar-images/delivery1.png",web:"https://en.orionstar.com/products/carrybot.html",video_wiki:VW},
   highlights:["World's First Micro Fulfillment Center (MFC) Logistics Robot","High-precision positioning for accurate factory delivery","Delivery Demo + Lab Test + Phone Factory validated","Proven in real smartphone manufacturing environment","Efficiency comparison video shows 3x manual performance","Revolutionary MFC concept pioneer for micro-warehouse logistics"],
   specs:{"Type":"Factory and MFC Logistics Robot","Positioning":"High-precision optical + LiDAR","Payload":"Up to 100 kg","Max Speed":"1.5 m/s","Navigation":"SLAM + QR hybrid","Use Case":"Factory lines, MFC, warehouse logistics"},
   scenes:["Smartphone and electronics factory production lines","Micro Fulfillment Centre (MFC) operations","Warehouse pick-and-deliver logistics","Laboratory sample and equipment transport","Manufacturing facility material handling","E-commerce internal last-mile logistics"],
   cases:[{"name":"Smartphone Manufacturing Factory","url":"https://en.orionstar.com/products/carrybot.html","desc":"Assembly line material delivery, 3x efficiency vs manual cart, lab-tested and factory-proven"},{"name":"Micro Fulfillment Centre","url":"https://en.orionstar.com/products/carrybot.html","desc":"World's first MFC logistics robot deployment, revolutionary warehouse efficiency gains"},{"name":"Electronics Assembly Line","url":"https://en.orionstar.com/products/carrybot.html","desc":"Precision component delivery to workstations, zero delay in production flow"},{"name":"Laboratory Environment","url":"https://en.orionstar.com/products/carrybot.html","desc":"Sample and equipment transport in controlled environments, reducing contamination risk"}]},
  {id:"greetingbot-mini",name:"GreetingBot Mini",zh:"豹小秘Mini海外版",desc:"Compact mobile commercial service robot for multilingual voice interaction, exhibition hall tours and counter consultation. 紧凑型移动商用服务机器人，支持多语种语音交互、展厅导览、柜台咨询",region:"overseas",cat:"voice",kw:"GreetingBot Mini reception 豹小秘Mini 接待 multilingual voice exhibition counter compact",
   assets:{ppt:F2+"VIrofYGDclTw5pdKF6NcdrrDnt4",brochure:F2+"O7hxfyU8UlfW1TdJVYmcymlUnDf",image:"orionstar-images/baoxiaomimini.png",video:F2+"XigJfpyPilsLG7dgPyBcBenUnJg",web:"https://en.orionstar.com/products/greetingbot-mini.html",video_wiki:VW},
   highlights:["Compact mobile design for flexible deployment in tight spaces","Multilingual voice interaction — 44 languages supported","Exhibition hall tour guidance with AI narration","Counter consultation service for banking/retail/government","7 proven customer scene types across industries","Competitive advantage in compact reception category"],
   specs:{"Type":"Compact Mobile Service Robot","Voice Interaction":"44 languages ASR + NLU","Navigation":"LiDAR + Visual SLAM","Screen":"Interactive touch screen","Deployment":"Mobile and fixed dual mode","Platform":"AgentOS"},
   scenes:["Office building reception and visitor management","Exhibition hall multilingual guided tours","Bank and finance counter consultation","Retail store customer service","Hotel lobby information service","Healthcare facility wayfinding and info"],
   cases:[{"name":"International Exhibition Hall","url":"https://en.orionstar.com/products/greetingbot-mini.html","desc":"Multilingual visitor tours in 5 languages, 200+ daily interactions with international visitors"},{"name":"Corporate Reception","url":"https://en.orionstar.com/products/greetingbot-mini.html","desc":"Automated visitor registration and wayfinding, front desk workload reduced 40%"},{"name":"Bank Branch","url":"https://en.orionstar.com/products/greetingbot-mini.html","desc":"Counter consultation queue management and product introduction, wait time reduced"},{"name":"Luxury Hotel Lobby","url":"https://en.orionstar.com/products/greetingbot-mini.html","desc":"Multilingual guest assistance in English/Japanese/Korean, guest satisfaction improved 30%"},{"name":"Medical Clinic","url":"https://en.orionstar.com/products/greetingbot-mini.html","desc":"Patient wayfinding and appointment guidance, front desk burden reduced"},{"name":"Government Service Centre","url":"https://en.orionstar.com/products/greetingbot-mini.html","desc":"Multilingual citizen assistance in 10+ languages, 500+ daily visitors served"},{"name":"Retail Mall","url":"https://en.orionstar.com/products/greetingbot-mini.html","desc":"Store directory and promotion guidance, customer engagement boosted 25%"}]},
  {id:"greetingbot-nova",name:"GreetingBot Nova",zh:"豹小秘2海外版",desc:"Smart shopping guide voice interaction robot with Office Reception Solution and Exhibition Hall Solution. 智能导购语音交互机器人，覆盖Office Reception和Exhibition Hall两大解决方案",region:"overseas",cat:"voice",kw:"GreetingBot Nova reception 豹小秘Nova 接待 smart shopping voice interaction Office Reception Exhibition Hall",
   assets:{ppt:F2+"TyJlfVqPhloWXKd16FKcmrmhnib",brochure:F2+"OLqDf3420lPviYdx6r6cgQ0znjc",image:"orionstar-images/baoxiaomi2.png",web:"https://en.orionstar.com/products/greetingbot-nova.html",video_wiki:VW},
   highlights:["Office Reception Solution — complete turnkey visitor management","Exhibition Hall Solution with multilingual tour guidance","Multilingual voice interaction — 44 languages","Promotional video suite: Office/Exhibition/Key Highlights/Future Exhibition Hall","Advanced AI voice recognition for intelligent engagement","Smart shopping guide with personalised product recommendations"],
   specs:{"Type":"Advanced Voice Interaction Service Robot","Voice Interaction":"44 languages ASR + NLU","Display":"Large touch screen","Navigation":"LiDAR + Vision SLAM","Platform":"AgentOS","Solutions":"Office Reception Solution + Exhibition Hall Solution"},
   scenes:["Corporate office reception and visitor management","Trade show and exhibition hall multilingual guidance","Shopping mall smart shopping assistant","Hotel concierge and guest information","Conference centre visitor registration","International business reception and translation"],
   cases:[{"name":"International Corporate Office","url":"https://en.orionstar.com/products/greetingbot-nova.html","desc":"Office Reception Solution: automated visitor check-in, meeting room guidance, staff directory in 5 languages"},{"name":"Tech Trade Show","url":"https://en.orionstar.com/products/greetingbot-nova.html","desc":"Exhibition Hall Solution: multilingual product demos in 8 languages, 500+ daily visitor interactions"},{"name":"Luxury Shopping Mall","url":"https://en.orionstar.com/products/greetingbot-nova.html","desc":"Smart shopping guide with personalised product recommendations in visitor's native language"},{"name":"5-Star Hotel","url":"https://en.orionstar.com/products/greetingbot-nova.html","desc":"Concierge solution for international guests, local attraction recommendations in 10 languages"},{"name":"International Conference Centre","url":"https://en.orionstar.com/products/greetingbot-nova.html","desc":"Multi-session conference navigation, delegate registration and room guidance"}]},
  {id:"greetingbot-ad",name:"GreetingBot AD",zh:"豹小秘AD大屏版",desc:"移动广告与购物引导解决方案机器人，双屏设计（14寸触摸屏+21.5寸FHD大屏），支持移动广告投放、店铺导航、产品推荐、多语言服务，适用于商场、零售门店等场景",region:"overseas",cat:"voice",kw:"GreetingBot AD large screen 豹小秘 大屏 广告 购物引导 移动广告 零售 商场 双屏 Mall Mode",
   assets:{ppt:F+"XsyYfaySulWzy9d2VwqcHuC3ndc",image:"orionstar-images/baoxiaomipro.png",web:"https://en.orionstar.com/products/greetingbot-ad.html",video_wiki:VW},
   highlights:["14寸触摸屏+21.5寸FHD双屏设计","高通AI芯片+8GB RAM","6麦环形阵列360度拾音","LiDAR+视觉SLAM导航，建图50000㎡","44种语言自动语音识别","Agent Store开箱即用，无需开发","双商业模式：Mall Mode（广告收入）+Store Model（销售转化）"],
   specs:{"屏幕":"14寸触摸屏+21.5寸FHD双屏","芯片":"高通AI芯片","内存":"8GB RAM","音频":"6麦环形阵列，360度拾音","导航":"LiDAR+视觉SLAM","建图面积":"≤50000㎡","有效运营面积":"≤5000㎡","语言":"44种语言自动语音识别","系统":"AgentOS"},
   scenes:["商场广告投放与导览","零售门店购物引导","品牌专柜产品推荐","美妆护肤智能推荐","珠宝门店多语言服务","免税店国际客户服务"],
   cases:[{"name":"某国际商场","url":"https://en.orionstar.com/products/greetingbot-ad.html","desc":"Mall Mode广告收入模式，一个广告位赚取3倍收益"},{"name":"某美妆门店","url":"https://en.orionstar.com/products/greetingbot-ad.html","desc":"智能推荐替代标准销售话术，降低决策门槛，高毛利产品转化提升"},{"name":"某珠宝门店","url":"https://en.orionstar.com/products/greetingbot-ad.html","desc":"44种语言服务国际客户，阿拉伯语导购高客单价产品"},{"name":"某大型超市","url":"https://en.orionstar.com/products/greetingbot-ad.html","desc":"分时段营销（早咖啡/午特价/下午新品/晚电影+折扣），全天候营收"},{"name":"某日韩商场","url":"https://en.orionstar.com/products/greetingbot-ad.html","desc":"日语/韩语品牌导航+免税信息，国际客户消费提升"},{"name":"某零售连锁","url":"https://en.orionstar.com/products/greetingbot-ad.html","desc":"单店模式引导至货架，语音搜索直达商品位置，购物篮转化率提升"}]},
  {id:"agentos",name:"AgentOS",zh:"AgentOS机器人操作系统",desc:"Intelligent robot operating system: develop a translation robot or medical education robot in 10 minutes. Includes Agent Store. 机器人智能操作系统，10分钟开发翻译/医疗宣教机器人，内置Agent Store",region:"overseas",cat:"platform",kw:"AgentOS OS system 机器人系统 操作系统 Agent Store 10分钟开发 translation medical education",
   assets:{ppt:F+"Xs1TfhZeylmwcJdtJ70cyWMwnLv",image:"orionstar-images/robot_arm.png",web:"https://en.orionstar.com/agentos.html",video_wiki:VW},
   highlights:["10-minute development: Chinese-English translation robot","10-minute development: medical education robot","Agent Store — robot app marketplace for ready-to-use skills","Open platform for custom skill development by third parties","44-language support across all robot hardware","Pre-built industry solution templates included","OTA updates push new capabilities without hardware changes"],
   specs:{"Platform":"AgentOS Robot Operating System","Dev Time":"10 minutes for a functional robot skill","Language Support":"44 languages","App Store":"Agent Store with growing skill library","Integration":"Open API, compatible with all OrionStar robots","Update":"OTA over-the-air update support"},
   scenes:["Hospital medical education and patient guidance","Corporate multilingual reception and real-time translation","Exhibition hall AI-guided tours","Retail smart shopping assistant","Customer service intelligent agent","Educational institution interactive learning robot"],
   cases:[{"name":"Hospital Medical Education","url":"https://en.orionstar.com/agentos.html","desc":"Medical education robot developed in 10 minutes, deployed in 3 hospitals, covering 20+ disease education topics"},{"name":"International Conference Translation","url":"https://en.orionstar.com/agentos.html","desc":"Chinese-English translation robot developed in 10 minutes, serving 200+ international delegates in real time"},{"name":"Exhibition Hall AI Guide","url":"https://en.orionstar.com/agentos.html","desc":"Custom guided tour robot on AgentOS, covers 50+ exhibits in 5 languages"},{"name":"Agent Store Partner","url":"https://en.orionstar.com/agentos.html","desc":"Third-party developers published 20+ skills on Agent Store, expanding robot capabilities without hardware changes"}]},
  {id:"lucki-button",name:"Lucki-Button",zh:"招财豹智能呼叫按钮",desc:"Smart wireless call button for Intelligent Summoning Solution — one press triggers LuckiBot robot delivery. 智能呼叫按钮，打造Intelligent Summoning Solution一键召唤机器人配送",region:"overseas",cat:"platform",kw:"Lucki-Button call button 呼叫按钮 Intelligent Summoning Solution Smart Summon wireless",
   assets:{ppt:F2+"LCFEfPhSFlo9MpdT0vScRWlnn6f",image:"orionstar-images/delivery1.png",web:"https://en.orionstar.com/products/lucki-button.html",video_wiki:VW},
   highlights:["Intelligent Summoning Solution — complete call-and-deliver system","Smart wireless button instantly triggers LuckiBot delivery","No app required — one-press robot summoning","Multi-zone and multi-floor zone management support","Customisable delivery zones and parameters","Proven ROI across restaurant and hotel deployments"],
   specs:{"Type":"Smart Wireless Call Button","Communication":"Wireless proprietary protocol","Coverage":"Full floor zone support","Integration":"LuckiBot and LuckiBot Pro compatible","Power":"Battery-powered, 1-year standby","Installation":"Adhesive mount, no wiring required"},
   scenes:["Restaurant table-side robot summon","Hotel room robot service call","Office on-demand supply delivery","Healthcare patient call for robot service","Retail fitting room assistance call","Lounge and VIP area premium robot service"],
   cases:[{"name":"Restaurant Chain (Southeast Asia)","url":"https://en.orionstar.com/products/lucki-button.html","desc":"Table-side smart summon buttons, 300+ daily robot calls, zero missed service requests"},{"name":"5-Star Hotel","url":"https://en.orionstar.com/products/lucki-button.html","desc":"In-room smart button for amenity requests, guest satisfaction score improved 40%"},{"name":"Corporate Office Lounge","url":"https://en.orionstar.com/products/lucki-button.html","desc":"On-demand refreshment delivery, service staff reduced by 2 FTE"},{"name":"Lucki-Button","url":"https://en.orionstar.com/products/lucki-button.html","desc":"Discreet button summoning for beverage and snack service, enhancing premium guest experience"}]},
  {id:"mowibot",name:"MowiBot",zh:"MowiBot移动机器人",desc:"Mobile service robot platform for versatile commercial and enterprise deployment scenarios. 移动服务机器人平台，适用于多种商业及企业场景",region:"overseas",cat:"delivery",kw:"MowiBot mobile robot 移动机器人 service",
   assets:{ppt:F+"",image:"orionstar-images/product2.png",video_wiki:VW},
   highlights:["Versatile mobile robot platform for multiple application scenarios","Advanced LiDAR + SLAM autonomous navigation","Flexible deployment: commercial, enterprise, and institutional","OrionStar-quality hardware and AgentOS software integration","Multiple configuration options per deployment requirement","Proven reliability across real-world commercial environments"],
   specs:{"Type":"Mobile Service Robot","Navigation":"LiDAR + SLAM","Mobility":"Multi-terrain indoor capable","Battery":"Extended operation battery","Platform":"AgentOS compatible","Configuration":"Customisable per deployment"},
   scenes:["Commercial service environments","Enterprise campus mobility and logistics","Public space navigation and guidance","Event and exhibition venue service","Hospitality service and delivery","Institutional and facility management"],
   cases:[{"name":"Commercial Service Deployment","url":"https://en.orionstar.com/products.html","desc":"Mobile robot service across multiple commercial scenarios, proven operational stability"},{"name":"Enterprise Campus","url":"https://en.orionstar.com/products.html","desc":"Campus-wide mobile service covering multiple buildings and floors"},{"name":"Hospitality Venue","url":"https://en.orionstar.com/products.html","desc":"Flexible service robot deployment adapting to various hospitality use cases"}]},
  {id:"ufactory-xarm",name:"UFactory xArm",zh:"xArm协作机械臂",desc:"6-axis collaborative robotic arm for automation and integration with service robots. 六轴协作机械臂，用于自动化和与服务机器人集成",region:"overseas",cat:"platform",kw:"xArm UFactory collaborative robotic arm 机械臂 协作机器人",
   assets:{image:"orionstar-images/robot_arm.png",web:"https://en.orionstar.com/products/ufactory-xarm.html",video_wiki:VW}},
  {id:"orionstar-x1",name:"OrionStar X1",zh:"X1清洁机器人",desc:"Next-generation flagship cleaning robot. 新一代旗舰清洁机器人",region:"overseas",cat:"clean",kw:"X1 OrionStar cleaning robot 清洁 next generation",
   assets:{image:"orionstar-images/product1.png",web:"https://en.orionstar.com/products.html",video_wiki:VW}},
  {id:"baoxiaomipro",name:"豹小秘Pro",zh:"豹小秘Pro",desc:"新一代AI接待机器人，搭载大模型语音交互，支持智能问答、访客接待、展厅讲解、会议指引等多场景",region:"domestic",cat:"voice",kw:"豹小秘Pro 接待 语音 大模型 AI 讲解 访客",
   assets:{ppt:F+"IDrufEI4MluH0hdJFUqc2bEQn7c",brochure:F+"ChkKf7ZyVlNzWgdZ08cc2bxgngh",image:"orionstar-images/baoxiaomipro.png",video:F+"OcoQfQPFll74yudi9czckQvanTh",web:"https://cn.orionstar.com/greeting-robot-plus.html",video_wiki:VW},
   highlights:["大模型AI对话","27寸触摸屏","多语言支持(中英日韩)","人脸识别记忆","自主导航避障","开放API接口"],
   specs:{"尺寸":"520×470×1450mm","重量":"65kg","屏幕":"27寸触摸屏","续航":"12小时","导航":"激光SLAM","语音":"大模型AI"},
   scenes:["前台接待","展厅讲解","会议指引","访客登记","业务咨询","导览服务"],
   cases:[{"name":"某大型商场","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"日均接待500+访客，智能导览提升30%效率"},{"name":"某科技企业总部","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"前台自动化接待，降低50%人力成本"},{"name":"某博物馆展厅","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"智能讲解覆盖20+展品，游客停留时间增加40%"},{"name":"某政府服务中心","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"政务咨询智能化，群众办事效率提升60%"},{"name":"某国际会议中心","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"多语言接待外宾，支持中英日韩4种语言"},{"name":"某三甲医院","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"门诊大厅智能导诊，日均服务800+患者"}]},
  {id:"baoxiaomi2",name:"豹小秘2",zh:"豹小秘2",desc:"轻量级智能接待机器人，适用于前台迎宾、业务咨询、导引指路等场景，部署灵活",region:"domestic",cat:"voice",kw:"豹小秘2 接待 语音 前台 引导 迎宾",
   assets:{ppt:F2+"TyJlfVqPhloWXKd16FKcmrmhnib",brochure:F2+"OLqDf3420lPviYdx6r6cgQ0znjc",image:"orionstar-images/baoxiaomi2.png",web:"https://cn.orionstar.com/greeting-robot2.html",video_wiki:VW},
   highlights:["轻量级设计","快速部署","语音交互","迎宾引导"],
   specs:{"尺寸":"410×380×1200mm","重量":"45kg","屏幕":"15.6寸","续航":"8小时","导航":"激光SLAM","语音":"智能语音"},
   scenes:["前台迎宾","业务咨询","导引指路","活动引导"],
   cases:[{"name":"某企业总部","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"前台自动化接待，降低50%人力成本"},{"name":"某连锁酒店","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"大堂迎宾引导，客户满意度提升25%"},{"name":"某写字楼","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"访客登记智能化，安保效率提升40%"},{"name":"某培训机构","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"校区导览指引，新生报到效率提升50%"},{"name":"某汽车4S店","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"展厅接待讲解，客户转化率提升15%"}]},
  {id:"baoxiaomimini",name:"豹小秘Mini",zh:"豹小秘Mini",desc:"桌面级语音交互终端，小巧便携，适用于柜台咨询、展厅互动、会议助手等场景",region:"domestic",cat:"voice",kw:"豹小秘Mini 桌面 语音 终端 柜台 咨询",
   assets:{ppt:F2+"VIrofYGDclTw5pdKF6NcdrrDnt4",brochure:F2+"O7hxfyU8UlfW1TdJVYmcymlUnDf",image:"orionstar-images/baoxiaomimini.png",web:"https://cn.orionstar.com/bxiaomimini.html",video_wiki:VW},
   highlights:["桌面级紧凑设计","便携易部署","语音交互","触控操作"],
   specs:{"尺寸":"200×180×250mm","重量":"3kg","屏幕":"8寸触摸屏","续航":"外接电源","语音":"智能语音","连接":"WiFi+蓝牙"},
   scenes:["柜台咨询","展厅互动","会议助手","桌面服务"],
   cases:[{"name":"某银行网点","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"柜台智能咨询，客户满意度提升25%"},{"name":"某政务大厅","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"窗口辅助咨询，排队等待减少30%"},{"name":"某展厅","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"桌面互动展示，参观体验提升35%"},{"name":"某会议室","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"会议签到助手，签到效率提升60%"},{"name":"某零售门店","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"产品介绍终端，促单转化提升20%"}]},
  {id:"zhaocaibao",name:"招财豹",zh:"招财豹",desc:"智能配送机器人，支持餐厅送餐、酒店送物、办公快递配送等多场景，高效安全",region:"domestic",cat:"delivery",kw:"招财豹 配送 送餐 送物 递送 机器人 酒店",
   assets:{ppt:F2+"SOh5fRE6PlWSyqdNYNlcyqYfnZx",brochure:F2+"KKG1f27helvrdcdNNcWc1S01nZf",video:F+"OcoQfQPFll74yudi9czckQvanTh",image:"orionstar-images/delivery1.png",web:"https://cn.orionstar.com/zhcaibao-zh.html",video_wiki:VW},
   highlights:["多层托盘设计","自主导航配送","智能避障","语音呼叫","自动回充"],
   specs:{"尺寸":"520×490×1220mm","重量":"55kg","托盘":"3层","载重":"30kg","续航":"10小时","导航":"激光SLAM"},
   scenes:["餐厅送餐","酒店送物","办公配送","快递收发","药品配送"],
   cases:[{"name":"某连锁餐厅","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"送餐效率提升40%，人力成本降低35%"},{"name":"某星级酒店","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"客房物品配送，服务响应速度提升50%"},{"name":"某办公园区","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"快递自动配送，日均处理200+件"},{"name":"某KTV娱乐城","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"酒水零食配送，服务员减少3人"},{"name":"某医院病房","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"药品餐食配送，医护负担减轻30%"},{"name":"某工厂车间","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"物料配送自动化，生产效率提升20%"}]},
  {id:"zhaocaibao-pro",name:"招财豹Pro",zh:"招财豹Pro",desc:"升级版招财豹，更大容量，更强续航，支持自动门对接",region:"domestic",cat:"delivery",kw:"招财豹Pro 配送 送餐 升级 大容量",
   assets:{ppt:F+"IDrufEI4MluH0hdJFUqc2bEQn7c",brochure:F+"ChkKf7ZyVlNzWgdZ08cc2bxgngh",video:F+"OcoQfQPFll74yudi9czckQvanTh",image:"orionstar-images/delivery2.png",web:"https://cn.orionstar.com/lucki-pro.html",video_wiki:VW},
   highlights:["更大容量","自动门对接","更强续航","多层配送","智能调度"],
   specs:{"尺寸":"560×520×1280mm","重量":"65kg","托盘":"4层","载重":"40kg","续航":"12小时","导航":"激光SLAM+视觉"},
   scenes:["高端餐厅","星级酒店","医院配送","办公大楼","电商仓储"],
   cases:[{"name":"某五星级酒店","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"客房配送全自动化，客户体验提升50%"},{"name":"某高端火锅连锁","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"4层托盘大容量送餐，翻台率提升25%"},{"name":"某大型医院","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"检验样本+药品配送，24小时不间断"},{"name":"某企业总部大楼","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"楼层间文件配送，行政效率提升40%"},{"name":"某电商仓储中心","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"自动门对接卸货，分拣效率提升35%"}]},
  {id:"s55pro",name:"S55 Pro",zh:"S55 Pro清洁机器人",desc:"商用清洁机器人，集洗地、扫地、吸尘于一体，适用于商场、写字楼、医院等大面积场所",region:"domestic",cat:"clean",kw:"S55 Pro 清洁 洗地 扫地 商用 机器人 商场",
   assets:{ppt:F+"E8gDf2jkjl1yI7dV4iycx4vcnFd",brochure:F+"GVBpfVERllzGCOdUvlbc9kb6ntd",image:"orionstar-images/product1.png",video:F+"BBMxf2q2GlZrYadMfVZczQFqnnf",web:"https://cn.orionstar.com/carry-zh.html",video_wiki:VW},
   highlights:["洗地+扫地+吸尘三合一","大容量水箱","智能路径规划","自动充电加水","远程监控"],
   specs:{"尺寸":"820×720×1120mm","重量":"120kg","清水箱":"30L","污水箱":"30L","清扫效率":"2000㎡/h","续航":"6小时"},
   scenes:["大型商场","写字楼大堂","医院走廊","机场航站楼","地下车库","工厂车间"],
   cases:[{"name":"某大型商场","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"保洁效率提升3倍，年节省人力成本20万"},{"name":"某国际机场","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"航站楼夜间深度清洁，覆盖5000㎡/h"},{"name":"某三甲医院","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"病房走廊消毒清洁，感染率降低15%"},{"name":"某写字楼群","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"大堂+走廊+车库全覆盖，保洁人员减少5人"},{"name":"某工厂车间","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"油污地面深度清洁，达标率100%"},{"name":"某地铁站","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"运营间隙快速清洁，日均覆盖3000㎡"}]},
  {id:"coffee",name:"咖啡机器人",zh:"咖啡机器人",desc:"智能现磨咖啡制作机器人，6轴机械臂精准操作，支持多种咖啡饮品制作",region:"domestic",cat:"delivery",kw:"咖啡 机器人 咖啡机 现磨 机械臂 商用",
   assets:{ppt:F+"IDrufEI4MluH0hdJFUqc2bEQn7c",image:"orionstar-images/coffee.png",web:"https://cn.orionstar.com/coffeemaster.html",video_wiki:VW},
   highlights:["6轴机械臂精准操作","现磨咖啡","多饮品选择","自助支付","智能温控"],
   specs:{"尺寸":"1200×800×1500mm","重量":"150kg","机械臂":"6轴","饮品数":"20+种","制作时间":"60秒/杯","支付":"扫码+刷脸"},
   scenes:["办公区茶水间","商场中庭","展会现场","酒店大堂","高铁站"],
   cases:[{"name":"某科技公司","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"日均制作200杯咖啡，员工满意度提升40%"},{"name":"某购物中心","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"中庭无人咖啡站，月营收增长30%"},{"name":"某展会现场","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"3天展会日均500杯，排队<3分钟"},{"name":"某酒店大堂","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"24小时咖啡服务，客户好评率98%"},{"name":"某高铁站","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"候车厅现磨咖啡，日均300+杯"}]},
  {id:"baoxiaomilite",name:"豹小秘Lite",zh:"豹小秘Lite",desc:"轻量入门级智能接待机器人，主打高性价比，适用于前台迎宾、导览指引、业务咨询等基础接待场景",region:"domestic",cat:"voice",kw:"豹小秘Lite 接待 语音 前台 迎宾 入门 性价比",
   assets:{ppt:F2+"VIrofYGDclTw5pdKF6NcdrrDnt4",image:"orionstar-images/baoxiaomipro.png",web:"https://cn.orionstar.com/baoxiaomi-lite.html",video_wiki:VW},
   highlights:["入门级高性价比","轻量化设计","语音交互","导览指引","快速部署"],
   specs:{"尺寸":"400×370×1180mm","重量":"42kg","屏幕":"15.6寸触摸屏","续航":"8小时","导航":"激光SLAM","语音":"智能语音"},
   scenes:["前台迎宾","导览指引","业务咨询","活动引导"],
   cases:[{"name":"某连锁门店","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"入门级迎宾接待，快速上岗降低人力成本"},{"name":"某社区服务中心","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"基础导览咨询，居民办事效率提升30%"},{"name":"某中小型企业","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"前台自动化接待，形象与效率双提升"},{"name":"某展销中心","url":"https://cn.orionstar.com/SuccessfulCases.html","desc":"展区引导讲解，参观体验提升25%"}]},
];
const SOLUTIONS=[
  {id:"sol-restaurant",name:"Restaurant Solution",zh:"餐饮解决方案",desc:"餐厅场景下的配送+接待综合方案",region:"overseas",cat:"solution",kw:"restaurant 餐饮 解决方案 配送",assets:{ppt:F2+"I00ZfjlwQlkugzd5h91c6mnonTc"}},
  {id:"sol-supermarket",name:"Supermarket Solution",zh:"超市解决方案",desc:"超市零售场景机器人方案",region:"overseas",cat:"solution",kw:"supermarket 超市 零售 解决方案",assets:{ppt:F+"O5bQfvbJolKsfCdMBRncMgJUnnc"}},
  {id:"sol-warehouse",name:"Warehouse Solution",zh:"仓储解决方案",desc:"仓储物流场景机器人方案",region:"overseas",cat:"solution",kw:"warehouse 仓储 物流 解决方案",assets:{ppt:F+"VRwFfwsqol7R2EdvAcIcwUiDnVc"}},
  {id:"sol-factory",name:"Factory Solution",zh:"工厂解决方案",desc:"工厂制造场景机器人方案",region:"overseas",cat:"solution",kw:"factory 工厂 制造 解决方案",assets:{ppt:F+"Zyb1fmrT3luKFJdQIoScT1LsnRb"}},
  {id:"sol-healthcare",name:"Healthcare Solution",zh:"医疗解决方案",desc:"医院医疗场景机器人方案",region:"overseas",cat:"solution",kw:"healthcare 医疗 医院 解决方案",assets:{ppt:F+"SLBdfsBfalrXqWdccMzcDOlAnke"}},
  {id:"sol-hotel",name:"Hotel Solution",zh:"酒店解决方案",desc:"酒店场景配送+接待方案",region:"overseas",cat:"solution",kw:"hotel 酒店 解决方案 配送 接待",assets:{ppt:F+"BxgDft18flvRqldWCAgc3xvXn0f"}},
  {id:"sol-airport",name:"Airport Solution",zh:"机场解决方案",desc:"机场航站楼场景机器人方案",region:"overseas",cat:"solution",kw:"airport 机场 解决方案",assets:{ppt:F+"QyBWf4KQWlAfkhdkrkscTypanCh"}},
  {id:"sol-casino",name:"Casino Solution",zh:"赌场解决方案",desc:"娱乐场所场景机器人方案",region:"overseas",cat:"solution",kw:"casino 赌场 娱乐 解决方案",assets:{ppt:F+"PeZ2fbtwSli8brdZjZYcfIinnJe"}},
  {id:"sol-elderly",name:"Elder Care Solution",zh:"养老场景解决方案",desc:"养老院及老年服务场景综合机器人方案",region:"overseas",cat:"solution",kw:"elderly elder care 养老 老年 解决方案 aging senior",assets:{ppt:F+""}},
  {id:"sol-large-supermarket",name:"Large Supermarket Solution",zh:"大型商超解决方案",desc:"大型超市及购物中心场景机器人综合方案",region:"overseas",cat:"solution",kw:"large supermarket hypermarket 大型商超 解决方案",assets:{ppt:F+""}},
  {id:"sol-smart-shopping",name:"Smart Shopping Guide Solution",zh:"智能导购-语音交互机器人解决方案",desc:"智能导购语音交互机器人综合解决方案",region:"overseas",cat:"solution",kw:"smart shopping guide voice interaction 智能导购 语音 解决方案 GreetingBot",assets:{ppt:F+""}},
];
const LANGS=[
  {id:"lang-en",name:"English Materials",zh:"英文物料",desc:"English product materials",region:"overseas",cat:"lang",kw:"English 英文 物料",assets:{}},
  {id:"lang-ja",name:"日本語資料",zh:"日文物料",desc:"日本語製品資料",region:"overseas",cat:"lang",kw:"Japanese 日本語 日文 物料",assets:{}},
  {id:"lang-ko",name:"한국어 자료",zh:"韩文物料",desc:"한국어 제품 자료",region:"overseas",cat:"lang",kw:"Korean 韩文 物料",assets:{}},
  {id:"lang-de",name:"Deutsch Materialien",zh:"德文物料",desc:"Deutsche Produktmaterialien",region:"overseas",cat:"lang",kw:"German Deutsch 德文 物料",assets:{}},
  {id:"lang-fr",name:"Matériaux Français",zh:"法文物料",desc:"Matériaux en français",region:"overseas",cat:"lang",kw:"French Français 法文 物料",assets:{}},
  {id:"lang-es",name:"Materiales Español",zh:"西文物料",desc:"Materiales en español",region:"overseas",cat:"lang",kw:"Spanish Español 西文 物料",assets:{}},
  {id:"lang-zh-tw",name:"繁體中文(台灣)物料",zh:"台湾繁体物料",desc:"繁體中文(台灣)產品資料",region:"overseas",cat:"lang",kw:"Traditional Chinese Taiwan 台湾 繁体 物料",assets:{}},
  {id:"lang-it",name:"Materiali Italiano",zh:"意大利文物料",desc:"Materiali in italiano",region:"overseas",cat:"lang",kw:"Italian Italiano 意大利文 物料",assets:{}},
  {id:"lang-th",name:"วัสดุภาษาไทย",zh:"泰文物料",desc:"วัสดุผลิตภัณฑ์ภาษาไทย",region:"overseas",cat:"lang",kw:"Thai ไทย 泰文 物料",assets:{}},
  {id:"lang-el",name:"Ελληνικά Υλικά",zh:"希腊文物料",desc:"Υλικά προϊόντων στα ελληνικά",region:"overseas",cat:"lang",kw:"Greek Ελληνικά 希腊文 物料",assets:{}},
  {id:"lang-pt",name:"Materiais Português",zh:"葡萄牙文物料",desc:"Materiais em português",region:"overseas",cat:"lang",kw:"Portuguese Português 葡萄牙文 物料",assets:{}},
  {id:"lang-ar",name:"المواد العربية",zh:"阿拉伯文物料",desc:"مواد المنتجات باللغة العربية",region:"overseas",cat:"lang",kw:"Arabic العربية 阿拉伯文 物料",assets:{}},
  {id:"lang-tr",name:"Türkçe Malzemeler",zh:"土耳其文物料",desc:"Türkçe ürün materyalleri",region:"overseas",cat:"lang",kw:"Turkish Türkçe 土耳其文 物料",assets:{}},
  {id:"lang-ru",name:"Русские материалы",zh:"俄文物料",desc:"Материалы продукта на русском языке",region:"overseas",cat:"lang",kw:"Russian Русский 俄文 物料",assets:{}},
  {id:"lang-ro",name:"Materiale Română",zh:"罗马尼亚文物料",desc:"Materiale în română",region:"overseas",cat:"lang",kw:"Romanian Română 罗马尼亚文 物料",assets:{}},
];
const CORPORATE=[
  {id:"corp-intro",name:"Company Introduction PPT",zh:"公司介绍PPT",desc:"北京猎户星空科技有限公司简介",region:"overseas",cat:"corp",kw:"company introduction 公司介绍 orionstar",assets:{ppt:F+"NMNYfYI8JlaZ4Wdm2K1cvAWWnzf"}},
  {id:"corp-brochure",name:"Company Brochure",zh:"公司手册",desc:"猎户星空企业手册",region:"overseas",cat:"corp",kw:"company brochure 公司手册",assets:{brochure:F+"U3aFfIJs5lTofMdqxVgcjh46njd"}},
  {id:"corp-vi",name:"Logo & VI Design Kit",zh:"Logo及VI设计素材",desc:"品牌Logo及视觉识别设计素材包",region:"overseas",cat:"corp",kw:"logo VI design 品牌 设计",assets:{brochure:F+"T5QZfTJ6JlMKTLdq6g9c0QPvnae"}},
  {id:"corp-cert",name:"Certification & Awards",zh:"认证与奖项",desc:"产品认证及获奖资料",region:"overseas",cat:"corp",kw:"certification awards 认证 奖项",assets:{brochure:F+"YINef8uwmlzELPdhK1hcCDOwn1g"}},
  {id:"corp-distributor",name:"Distributor Handbook",zh:"经销商手册",desc:"经销商合作手册",region:"overseas",cat:"corp",kw:"distributor handbook 经销商 手册",assets:{brochure:F+"EXVCfZzXSleQO3dsUDaceB7MnIb"}},
];
const ALL_ITEMS=[...PRODUCTS,...SOLUTIONS,...LANGS,...CORPORATE];
const LANG_LIST=[\'中文(简体)\',\'中文(繁體)\',\'English\',\'日本語\',\'한국어\',\'Français\',\'Deutsch\',\'Español\',\'Português\',\'Italiano\',\'Русский\',\'العربية\',\'हिन्दी\',\'ไทย\',\'Tiếng Việt\',\'Bahasa Indonesia\',\'Bahasa Melayu\',\'Türkçe\',\'Nederlands\',\'Polski\',\'Українська\',\'Română\',\'Čeština\',\'Magyar\',\'Svenska\',\'Suomi\',\'Dansk\',\'Norsk\',\'Ελληνικά\',\'Български\',\'Hrvatski\',\'Slovenčina\',\'Slovenščina\',\'Latviešu\',\'Lietuvių\',\'Eesti\',\'Irish\',\'Cymraeg\',\'Catalan\',\'Galician\',\'Filipino\',\'مصرى (Masry)\',\'فارسی (Persian)\',\'עברית (Hebrew)\',\'اردو (Urdu)\',\'বাংলা (Bengali)\',\'தமிழ் (Tamil)\',\'తెలుగు (Telugu)\',\'मराठी (Marathi)\',\'ગુજરાતી (Gujarati)\',\'ਪੰਜਾਬੀ (Punjabi)\',\'Kiswahili (Swahili)\',\'Amharic\',\'Zulu\',\'Afrikaans\',\'Shqip (Albanian)\',\'Български (Bulgarian)\',\'Српски (Serbian)\',\'Македонски (Macedonian)\',\'Қазақ (Kazakh)\',\'O\\\'zbek (Uzbek)\',\'Монгол (Mongolian)\',\'ქართული (Georgian)\'];
const REGIONS={domestic:{name:"国内",flag:"CN"},overseas:{name:"海外",flag:"OV"}};
const CATS={
  voice:{name:"语音/接待机器人",icon:"&#127897;"},
  delivery:{name:"递送/配送机器人",icon:"&#128230;"},
  clean:{name:"清洁机器人",icon:"&#129529;"},
  platform:{name:"平台/AI能力",icon:"&#9881;&#65039;"},
  solution:{name:"解决方案",icon:"&#128161;"},
  corp:{name:"企业资料",icon:"&#127970;"},
  lang:{name:"多语种物料",icon:"&#127760;"}
};
const RECENT_UPDATES=[
  {id:"baoxiaomipro",label:"豹小秘Pro",sub:"新增产品资料",badge:"NEW"},
  {id:"cleanibot-s55pro",label:"CleaniBot S55 Pro",sub:"竞品分析更新",badge:"更新"},
  {id:"sol-restaurant",label:"Restaurant Solution",sub:"解决方案PPT更新",badge:"更新"},
  {id:"luckibot-pro",label:"LuckiBot Pro",sub:"新增客户案例",badge:"NEW"},
  {id:"greetingbot-nova",label:"GreetingBot Nova",sub:"手册更新",badge:"更新"},
  {id:"zhaocaibao-pro",label:"招财豹Pro",sub:"视频物料更新",badge:"更新"},
];

function toggleSidebar(){document.getElementById('sidebar').classList.toggle('open');document.getElementById('sidebarOverlay').classList.toggle('show')}
function searchTag(q){document.getElementById('searchInput').value=q;doSearch();document.getElementById('breadcrumb').textContent='搜索: '+q}

let currentItem=null;
function initApp(){buildNav();renderHome()}

function buildNav(){
  let h='';
  h+='<div class="nav-region">&#127464;&#127475; 国内产品</div>';
  const dcats={voice:[],delivery:[],platform:[]};
  PRODUCTS.filter(p=>p.region==='domestic').forEach(p=>{if(dcats[p.cat])dcats[p.cat].push(p)});
  Object.entries(dcats).forEach(function(e){
    var k=e[0],ps=e[1];
    if(!ps.length)return;
    var ci=CATS[k]?CATS[k].icon:'';
    h+='<div class="nav-cat">'+ci+' '+CATS[k].name+'</div>';
    ps.forEach(function(p){
      var pi=CATS[p.cat]?CATS[p.cat].icon:'';
      h+='<div class="nav-item" id="nav-'+p.id+'" onclick="selectProduct(\\''+p.id+'\\')"><span style="font-size:13px;flex-shrink:0">'+pi+'</span>'+p.name+'</div>';
    });
  });
  h+='<div class="nav-region" style="margin-top:12px">&#127760; 海外产品</div>';
  const ocats={clean:[],voice:[],delivery:[]};
  PRODUCTS.filter(p=>p.region==='overseas').forEach(p=>{if(ocats[p.cat])ocats[p.cat].push(p)});
  Object.entries(ocats).forEach(function(e){
    var k=e[0],ps=e[1];
    if(!ps.length)return;
    var ci=CATS[k]?CATS[k].icon:'';
    h+='<div class="nav-cat">'+ci+' '+CATS[k].name+'</div>';
    ps.forEach(function(p){
      var pi=CATS[p.cat]?CATS[p.cat].icon:'';
      h+='<div class="nav-item" id="nav-'+p.id+'" onclick="selectProduct(\\''+p.id+'\\')"><span style="font-size:13px;flex-shrink:0">'+pi+'</span>'+p.name+'</div>';
    });
  });
  document.getElementById('navTree').innerHTML=h;
}

function setNavActive(id){
  document.querySelectorAll('.nav-item').forEach(function(el){el.classList.remove('active')});
  var el=document.getElementById('nav-'+id);
  if(el)el.classList.add('active');
}

function goHome(){currentItem=null;document.getElementById('breadcrumb').innerHTML='&#127968; 首页';document.querySelectorAll('.nav-item').forEach(function(el){el.classList.remove('active')});renderHome()}

function selectProduct(id){
  var p=PRODUCTS.find(function(x){return x.id===id});
  if(!p)return;
  currentItem=p;setNavActive(id);
  document.getElementById('breadcrumb').innerHTML='<span onclick="goHome()">&#127968; 首页</span> &rsaquo; '+p.name;
  renderDetail(p);
}

function selectItem(id){
  var item=ALL_ITEMS.find(function(x){return x.id===id});
  if(!item)return;
  currentItem=item;
  document.getElementById('breadcrumb').innerHTML='<span onclick="goHome()">&#127968; 首页</span> &rsaquo; '+item.name;
  renderDetail(item);
}

var typeLabels={ppt:'产品介绍PPT',video:'宣传视频',image:'产品图片',brochure:'产品手册',poster:'宣传海报',competitor:'竞品分析',case:'客户案例',manual:'用户手册'};
var typeIcons={ppt:'&#128202;',video:'&#127916;',image:'&#128444;&#65039;',brochure:'&#128196;',case:'&#128200;',competitor:'&#9876;&#65039;',manual:'&#128214;',poster:'&#127919;'};

function renderDetail(p){
  var ca=document.getElementById('contentArea');
  var h='<div class="product-detail">';
  h+='<div class="product-header"><div style="display:flex;align-items:flex-start;justify-content:space-between;gap:16px;flex-wrap:wrap"><div style="flex:1;min-width:0"><h1>'+p.name+' <span class="tag tag-onsale">在售</span></h1>';
  h+='<div class="zh">'+p.zh+'</div><div class="desc">'+p.desc+'</div></div>';
  h+='<button class="ai-btn" onclick="toggleAIPanel()">&#10024; AI&#25776;&#31295;</button>';
  h+='</div></div>';
  _aiCurrentProduct=p;_aiSelectedType=null;_aiSelectedModel=\'claude-opus-4-8\';_aiSelectedModelType=\'text\';_aiSelectedLang=\'中文(简体)\';
  h+=\'<div id="aiPanel" class="ai-panel" style="display:none">\';
  h+=\'<div class="ai-section-title">选择大模型</div>\';
  h+=\'<div class="model-dropdown" id="modelDropdown"><div class="model-dropdown-header" onclick="toggleModelDropdown()"><span>&#129302; 大模型：<span class="model-current-name">Kimi K3</span></span><span class="model-dropdown-arrow">&#9660;</span></div><div class="model-dropdown-body"><div class="model-categories">\';
  h+=\'<div class="model-category"><div class="model-category-title">&#128221; 文章生成大模型</div>\';

  h+=\'<div class="model-card" onclick="selectModel(this,\\\'claude-opus-4-8\\\',\\\'text\\\')"><div class="mc-name">Claude Opus 4.8</div><div class="mc-co">Anthropic</div><div class="mc-score">96分 &#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="mc-desc">长文逻辑最强</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'gpt-5.5\\\',\\\'text\\\')"><div class="mc-name">GPT-5.5</div><div class="mc-co">OpenAI</div><div class="mc-score">95分 &#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="mc-desc">综合创作最强</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'gemini-3.1-pro\\\',\\\'text\\\')"><div class="mc-name">Gemini 3.1 Pro</div><div class="mc-co">Google</div><div class="mc-score">94分 &#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="mc-desc">多模态+长上下文</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'deepseek-v4-pro\\\',\\\'text\\\')"><div class="mc-name">Deepseek V4 Pro</div><div class="mc-co">深度求索</div><div class="mc-score">93分 &#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="mc-desc">中文深度稿件最强</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'gpt-4o\\\',\\\'text\\\')"><div class="mc-name">GPT-4o</div><div class="mc-co">OpenAI</div><div class="mc-score">92分 &#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="mc-desc">综合创作能力强</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'claude-sonnet-5\\\',\\\'text\\\')"><div class="mc-name">Claude Sonnet 5</div><div class="mc-co">Anthropic</div><div class="mc-score">90分 &#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="mc-desc">性价比最佳</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'glm-5.2\\\',\\\'text\\\')"><div class="mc-name">GLM-5.2</div><div class="mc-co">智谱AI</div><div class="mc-score">88分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">中文理解+开源</div></div>\';
  h+=\'<div class="model-card selected" onclick="selectModel(this,\\\'kimi-k3\\\',\\\'text\\\')"><div class="mc-name">Kimi K3</div><div class="mc-co">月之暗面</div><div class="mc-score">86分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">长文处理</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'qwen-3.7-max\\\',\\\'text\\\')"><div class="mc-name">Qwen 3.7 Max</div><div class="mc-co">阿里</div><div class="mc-score">84分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">代码+文档</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'doubao-pro\\\',\\\'text\\\')"><div class="mc-name">Doubao Pro</div><div class="mc-co">字节跳动</div><div class="mc-score">82分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">速度快成本低</div></div>\';
  h+=\'</div>\';
  h+=\'<div class="model-category"><div class="model-category-title">&#128444;&#65039; 图片生成大模型</div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'seedream-5.0-lite\\\',\\\'image\\\')"><div class="mc-name">Seedream 5.0 Lite</div><div class="mc-co">字节跳动</div><div class="mc-score">90分 &#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="mc-desc">中文图片生成</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'gpt-image-2\\\',\\\'image\\\')"><div class="mc-name">GPT Image 2</div><div class="mc-co">OpenAI</div><div class="mc-score">89分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">DALL-E系列</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'seedream-4.5\\\',\\\'image\\\')"><div class="mc-name">Seedream 4.5</div><div class="mc-co">字节跳动</div><div class="mc-score">88分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">高质量图片</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'gemini-3.1-flash-image\\\',\\\'image\\\')"><div class="mc-name">Gemini 3.1 Flash Image</div><div class="mc-co">Google</div><div class="mc-score">87分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">多模态图片</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'seedream-4.0\\\',\\\'image\\\')"><div class="mc-name">Seedream 4.0</div><div class="mc-co">字节跳动</div><div class="mc-score">85分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">基础图片生成</div></div>\';
  h+=\'</div>\';
  h+=\'<div class="model-category"><div class="model-category-title">&#127916; 视频生成大模型</div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'veo-3.1\\\',\\\'video\\\')"><div class="mc-name">Veo 3.1</div><div class="mc-co">Google</div><div class="mc-score">95分 &#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="mc-desc">顶级视频生成</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'veo-3.1-fast\\\',\\\'video\\\')"><div class="mc-name">Veo 3.1 Fast</div><div class="mc-co">Google</div><div class="mc-score">92分 &#9733;&#9733;&#9733;&#9733;&#9733;</div><div class="mc-desc">快速视频生成</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'dreamina-seedance-2.0\\\',\\\'video\\\')"><div class="mc-name">Dreamina Seedance 2.0</div><div class="mc-co">字节跳动</div><div class="mc-score">88分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">中文视频生成</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'wan-2.7-image-pro\\\',\\\'video\\\')"><div class="mc-name">Wan 2.7 Image Pro</div><div class="mc-co">阿里</div><div class="mc-score">85分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">图生视频</div></div>\';
  h+=\'<div class="model-card" onclick="selectModel(this,\\\'dreamina-seedance-2.0-mini\\\',\\\'video\\\')"><div class="mc-name">Dreamina Seedance 2.0 Mini</div><div class="mc-co">字节跳动</div><div class="mc-score">82分 &#9733;&#9733;&#9733;&#9733;&#9734;</div><div class="mc-desc">轻量视频</div></div>\';
  h+=\'</div>\';
  h+=\'</div></div></div>\';
  h+=\'<div class="ai-section-title" style="margin-top:16px">语言选项</div>\';
  h+=\'<div class="lang-dropdown" id="langDropdown"><div class="lang-dropdown-header" onclick="toggleLangDropdown()"><span>&#127760; 语言：<span class="lang-current-name">\'+_aiSelectedLang+\'</span></span><span class="lang-dropdown-arrow">&#9660;</span></div><div class="lang-dropdown-body">\'+LANG_LIST.map(function(l){return \'<span class="lang-item\'+(l===_aiSelectedLang?\' selected\':\'\')+\'" data-lang="\'+l+\'" onclick="selectLang(this)">\'+l+\'</span>\'}).join(\'\')+\'</div></div>\';
  h+=\'<hr class="ai-divider">\';
  h+=\'<div class="ai-section-title">选择稿件类型</div>\';
  h+=\'<div class="article-type-group"><div class="article-type-group-label">新闻稿</div><div class="article-type-tags">\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'policy\\\')">政策借势新闻稿</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'brand\\\')">品牌故事新闻稿</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'launch\\\')">产品发布新闻稿</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'event-preview\\\')">参会预热新闻稿</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'exhibition\\\')">参展新闻通稿</span>\';
  h+=\'</div></div>\';
  h+=\'<div class="article-type-group"><div class="article-type-group-label">GEO内容营销稿件</div><div class="article-type-tags">\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'product-intro\\\')">产品介绍稿件</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'case\\\')">标杆案例稿件</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'solution\\\')">行业解决方案稿件</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'scene\\\')">应用场景稿件</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'tech\\\')">技术优势稿件</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'news\\\')">产品动态稿件</span>\';
  h+=\'</div></div>\';
  h+=\'<div class="article-type-group"><div class="article-type-group-label">SEO稿件</div><div class="article-type-tags">\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'seo-popular\\\')">科普问答型</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'seo-pitfall\\\')">避坑指南型</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'seo-comparison\\\')">选型对比型</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'seo-price\\\')">价格预算型</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'seo-scenario\\\')">场景解决方案型</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'seo-review\\\')">实测体验/客户案例型</span>\';
  h+=\'</div></div>\';
  h+=\'<div class="article-type-group"><div class="article-type-group-label">视频脚本</div><div class="article-type-tags">\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'video-30s\\\')">30秒版本</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'video-60s\\\')">60秒版本</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'video-full\\\')">完整版本（2-3分钟）</span>\';
  h+=\'</div></div>\';
  h+=\'<div class="article-type-group"><div class="article-type-group-label">宣传海报</div><div class="article-type-tags">\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'poster-activity\\\')">活动海报</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'poster-festival\\\')">节日海报</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'poster-trend\\\')">借势传播海报</span>\';
  h+=\'</div></div>\';
  h+=\'<div class="article-type-group"><div class="article-type-group-label">销售PPT</div><div class="article-type-tags">\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'ppt-solution\\\')">解决方案PPT</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'ppt-product\\\')">产品介绍PPT</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'ppt-scene\\\')">场景PPT</span>\';
  h+=\'<span class="article-type-tag" onclick="selectArticleType(this,\\\'ppt-case\\\')">案例合集PPT</span>\';
  h+=\'</div></div>\';
  h+=\'<hr class="ai-divider">\';
  h+=\'<div class="ai-section-title">参考资料</div>\';
  h+=\'<div id="refTagsArea">\';
  var _pImg=p.assets&&p.assets.image?p.assets.image:\'\';
  var _imgEl=_pImg?\'<img class="ref-card-img" src="\'+_pImg+\'" />\':\'<div class="ref-card-img" style="background:#EFF6FF;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:18px">&#129302;</div>\';
  if(p.cases&&p.cases.length){h+=\'<div style="margin-bottom:14px"><div style="font-size:11px;font-weight:600;color:#9CA3AF;margin-bottom:8px">标杆案例</div><div class="ref-card-grid">\';p.cases.forEach(function(c,i){h+=\'<div class="ref-card" data-type="case" data-idx="\'+i+\'" onclick="toggleRefTag(this)"><div class="ref-card-img" style="background:#FFF9E6;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:18px">&#127942;</div><div class="ref-card-title">\'+c.name+\'</div><div class="ref-card-desc">\'+c.desc+\'</div></div>\';});h+=\'</div></div>\';}
  if(p.highlights&&p.highlights.length){h+=\'<div style="margin-bottom:14px"><div style="font-size:11px;font-weight:600;color:#9CA3AF;margin-bottom:8px">产品亮点</div><div class="ref-card-grid">\';p.highlights.forEach(function(hl,i){h+=\'<div class="ref-card" data-type="highlight" data-idx="\'+i+\'" onclick="toggleRefTag(this)"><div class="ref-card-img" style="background:#FFFDE7;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:18px">&#128161;</div><div class="ref-card-title">\'+hl+\'</div><div class="ref-card-desc">\'+p.name+\'</div></div>\';});h+=\'</div></div>\';}
  if(p.scenes&&p.scenes.length){h+=\'<div style="margin-bottom:14px"><div style="font-size:11px;font-weight:600;color:#9CA3AF;margin-bottom:8px">应用场景</div><div class="ref-card-grid">\';p.scenes.forEach(function(s,i){h+=\'<div class="ref-card" data-type="scene" data-idx="\'+i+\'" onclick="toggleRefTag(this)"><div class="ref-card-img" style="background:#F0FFF4;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:18px">&#128205;</div><div class="ref-card-title">\'+s+\'</div><div class="ref-card-desc">\'+p.name+\'</div></div>\';});h+=\'</div></div>\';}
  if(p.specs&&Object.keys(p.specs).length){h+=\'<div style="margin-bottom:14px"><div style="font-size:11px;font-weight:600;color:#9CA3AF;margin-bottom:8px">产品参数</div><div class="ref-card-grid">\';Object.entries(p.specs).forEach(function(e){h+=\'<div class="ref-card" data-type="spec" data-key="\'+e[0]+\'" onclick="toggleRefTag(this)"><div class="ref-card-img" style="background:#F3F4F6;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:18px">&#9881;&#65039;</div><div class="ref-card-title">\'+e[0]+\'</div><div class="ref-card-desc">\'+e[1]+\'</div></div>\';});h+=\'</div></div>\';}
  var _fsLabels={ppt:\'飞书PPT\',brochure:\'飞书手册\',video:\'飞书视频\',case:\'飞书案例\',competitor:\'竞品分析\',manual:\'飞书用户手册\'};var _fsIcons={ppt:\'&#128202;\',brochure:\'&#128196;\',video:\'&#127916;\',image:\'&#128444;&#65039;\',case:\'&#128200;\',competitor:\'&#9876;&#65039;\',manual:\'&#128196;\'};var _fsCards=\'\';Object.entries(p.assets||{}).forEach(function(e){if(_fsLabels[e[0]]&&e[1]){_fsCards+=\'<div class="ref-card" data-type="asset" data-key="\'+e[0]+\'" onclick="toggleRefTag(this)"><div class="ref-card-img" style="background:#EFF6FF;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:18px">\'+(_fsIcons[e[0]]||\'&#128194;\')+\'</div><div class="ref-card-title">\'+_fsLabels[e[0]]+\'</div><div class="ref-card-desc">飞书文件夹</div></div>\';}});if(_fsCards){h+=\'<div style="margin-bottom:14px"><div style="font-size:11px;font-weight:600;color:#9CA3AF;margin-bottom:8px">飞书资料</div><div class="ref-card-grid">\'+_fsCards+\'</div></div>\';}
  h+=\'<div style="margin-bottom:14px"><div style="font-size:11px;font-weight:600;color:#9CA3AF;margin-bottom:8px">外部渠道</div><div class="ref-card-grid">\';if(p.assets&&p.assets.web){h+=\'<div class="ref-card" data-type="external" data-key="web" onclick="toggleRefTag(this)"><div class="ref-card-img" style="background:#EFF6FF;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:18px">&#127760;</div><div class="ref-card-title">官网页面</div><div class="ref-card-desc">cn.orionstar.com</div></div>\';}if(p.assets&&p.assets.video_wiki){h+=\'<div class="ref-card" data-type="external" data-key="video_wiki" onclick="toggleRefTag(this)"><div class="ref-card-img" style="background:#FFF0F0;border-radius:6px;display:flex;align-items:center;justify-content:center;font-size:18px">&#127916;</div><div class="ref-card-title">视频号资料</div><div class="ref-card-desc">飞书视频资料库</div></div>\';}h+=\'</div></div>\';
  h+=\'</div>\';
  h+=\'<hr class="ai-divider">\';
  h+=\'<div style="display:flex;align-items:center;gap:12px"><button class="ai-generate-btn" id="aiGenBtn" onclick="generateArticle()">&#10024; 生成稿件</button><span id="aiStatus" style="font-size:13px;color:#9CA3AF"></span></div>\';
  h+=\'<div id="aiResult" class="ai-result-area" style="display:none"><div id="aiResultText" class="ai-result-text"></div>\';
  h+=\'<div class="ai-result-actions"><button class="ai-result-btn ai-copy-btn" onclick="copyArticle()">复制全文</button><button class="ai-result-btn ai-regen-btn" onclick="generateArticle()">重新生成</button></div></div>\';
  h+=\'</div>\';
  if(p.assets&&p.assets.image){h+=\'<div style="padding:20px 0;border-top:1px solid #F3F4F6;text-align:center"><img src="\'+p.assets.image+\'" alt="\'+p.name+\'" style="max-width:360px;width:100%;border-radius:10px;object-fit:cover" /></div>\';}
  if(p.highlights&&p.highlights.length){h+=\'<div style="padding:20px 0;border-top:1px solid #F3F4F6"><div class="section-hd"><h2>&#9989; 产品亮点</h2></div><ul style="list-style:none;padding:0;margin:0">\';p.highlights.forEach(function(hl){h+=\'<li style="display:flex;align-items:flex-start;gap:8px;padding:7px 0;font-size:14px;color:#374151;border-bottom:1px solid #F9FAFB"><span style="flex-shrink:0">&#9989;</span><span>\'+hl+\'</span></li>\';});h+=\'</ul></div>\';}
  if(p.specs&&Object.keys(p.specs).length){h+=\'<div style="padding:20px 0;border-top:1px solid #F3F4F6"><div class="section-hd"><h2>&#9881;&#65039; 产品参数</h2></div><table style="width:100%;border-collapse:collapse;font-size:13px">\';Object.entries(p.specs).forEach(function(e){h+=\'<tr><td style="padding:8px 12px;background:#F9FAFB;border:1px solid #E5E7EB;font-weight:500;color:#374151;width:35%;white-space:nowrap">\'+e[0]+\'</td><td style="padding:8px 12px;border:1px solid #E5E7EB;color:#111827">\'+e[1]+\'</td></tr>\';});h+=\'</table></div>\';}
  if(p.scenes&&p.scenes.length){h+=\'<div style="padding:20px 0;border-top:1px solid #F3F4F6"><div class="section-hd"><h2>&#128205; 应用场景</h2></div><div style="display:flex;gap:8px;flex-wrap:wrap">\';p.scenes.forEach(function(s){h+=\'<span style="padding:6px 14px;border-radius:20px;font-size:13px;color:#374151;background:#F9FAFB;border:1px solid #E5E7EB">\'+s+\'</span>\';});h+=\'</div></div>\';}
  if(p.cases&&p.cases.length){h+=\'<div style="padding:20px 0;border-top:1px solid #F3F4F6"><div class="section-hd"><h2>&#127942; 标杆案例</h2></div><div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:10px">\';p.cases.forEach(function(c){h+=\'<div style="background:#F9FAFB;border-radius:8px;padding:14px 16px;border:1px solid #E5E7EB"><div style="font-size:13px;font-weight:600;color:#111827;margin-bottom:6px">\'+c.name+\'</div><div style="font-size:12px;color:#6B7280;line-height:1.6">\'+c.desc+\'</div></div>\';});h+=\'</div></div>\';}
  var _fsk=Object.keys(p.assets||{}).filter(function(k){return typeLabels[k]&&p.assets[k]&&k!==\'image\';});
  h+=\'<div style="padding:20px 0;border-top:1px solid #F3F4F6"><div class="section-hd"><h2>&#128196; 资料来源</h2></div>\';
  if(_fsk.length){h+=\'<div style="margin-bottom:16px"><div style="font-size:11px;font-weight:600;color:#9CA3AF;margin-bottom:8px">飞书内部文档</div><div class="assets-grid">\';_fsk.forEach(function(k){h+=\'<a href="\'+p.assets[k]+\'" target="_blank" class="asset-card"><div class="asset-icon">\'+typeIcons[k]+\'</div><div class="info"><h4>\'+typeLabels[k]+\'</h4><p>点击查看</p></div></a>\';});h+=\'</div></div>\';}
  h+=\'<div style="margin-bottom:16px"><div style="font-size:11px;font-weight:600;color:#9CA3AF;margin-bottom:8px">外部渠道</div><div class="assets-grid">\';
  if(p.assets&&p.assets.web){h+=\'<a href="\'+p.assets.web+\'" target="_blank" class="asset-card"><div class="asset-icon">&#127760;</div><div class="info"><h4>官网页面</h4><p>cn/en.orionstar.com</p></div></a>\';}
  if(p.assets&&p.assets.video_wiki){h+=\'<a href="\'+p.assets.video_wiki+\'" target="_blank" class="asset-card"><div class="asset-icon">&#127916;</div><div class="info"><h4>视频号资料</h4><p>飞书视频资料库</p></div></a>\';}
  h+=\'</div></div></div>\';
  var _rel=PRODUCTS.filter(function(x){return x.id!==p.id&&x.cat===p.cat}).slice(0,6);
  if(_rel.length){h+=\'<div class="related-section"><h3>&#128218; 相关产品推荐</h3><div class="related-grid">\';_rel.forEach(function(r){h+=\'<div class="related-card" onclick="selectProduct(\\\'\'+ r.id +\'\\\')">\'+\'<div class="rc-name">\'+r.name+\'</div><div class="rc-zh">\'+r.zh+\'</div></div>\';});h+=\'</div></div>\';}
  h+='</div>';
  ca.innerHTML=h;
}

function showSolutions(){
  document.getElementById('breadcrumb').innerHTML='<span onclick="goHome()">&#127968; 首页</span> &rsaquo; 解决方案';
  var ca=document.getElementById('contentArea');
  var h='<div style="margin-bottom:18px"><h2 style="font-size:20px;font-weight:700;color:#111827">&#128161; 解决方案</h2></div><div class="cat-grid">';
  SOLUTIONS.forEach(function(s){
    h+='<div class="cat-card" onclick="selectItem(\\''+s.id+'\\')">';
    h+='<div class="cat-icon">&#128161;</div>';
    h+='<div class="cat-info"><h3>'+s.name+'</h3><p>'+s.zh+'</p></div></div>';
  });
  h+='</div>';ca.innerHTML=h;
}

function showLangs(){
  document.getElementById('breadcrumb').innerHTML='<span onclick="goHome()">&#127968; 首页</span> &rsaquo; 多语种物料';
  var ca=document.getElementById('contentArea');
  var h='<div style="margin-bottom:18px"><h2 style="font-size:20px;font-weight:700;color:#111827">&#127760; 多语种物料</h2></div><div class="cat-grid">';
  LANGS.forEach(function(l){
    h+='<div class="cat-card" onclick="selectItem(\\''+l.id+'\\')">';
    h+='<div class="cat-icon">&#127760;</div>';
    h+='<div class="cat-info"><h3>'+l.name+'</h3><p>'+l.zh+'</p></div></div>';
  });
  h+='</div>';ca.innerHTML=h;
}

function doSearchCat(cat){
  var hits=PRODUCTS.filter(function(p){return p.cat===cat});
  var ca=document.getElementById('contentArea');
  var ci=CATS[cat]?CATS[cat].icon:'';
  document.getElementById('breadcrumb').innerHTML='<span onclick="goHome()">&#127968; 首页</span> &rsaquo; '+CATS[cat].name;
  var h='<div style="margin-bottom:18px"><h2 style="font-size:20px;font-weight:700;color:#111827">'+ci+' '+CATS[cat].name+' ('+hits.length+')</h2></div><div class="cat-grid">';
  hits.forEach(function(p){
    h+='<div class="cat-card" onclick="selectProduct(\\''+p.id+'\\')">';
    h+='<div class="cat-icon">'+CATS[cat].icon+'</div>';
    h+='<div class="cat-info"><h3>'+p.name+'</h3><p>'+p.zh+'</p></div></div>';
  });
  h+='</div>';ca.innerHTML=h;
}

function renderHome(){
  var ca=document.getElementById('contentArea');
  var totalProducts=PRODUCTS.length;
  var totalSolutions=SOLUTIONS.length;
  var totalAssets=PRODUCTS.reduce(function(acc,p){return acc+Object.keys(p.assets||{}).length},0);
  var totalLangs=LANGS.length;
  var h='';
  h+='<div class="hero">';
  h+='<h1>OrionStar 产品资料知识库</h1>';
  h+='<p>快速查找产品资料、解决方案、营销物料，赋能一线销售团队</p>';
  h+='<div class="hero-search"><input type="text" id="heroSearch" placeholder="搜索产品、方案、资料..." onkeydown="if(event.key===\\'Enter\\'){document.getElementById(\\'searchInput\\').value=this.value;doSearch()}" /><button onclick="document.getElementById(\\'searchInput\\').value=document.getElementById(\\'heroSearch\\').value;doSearch()">搜索</button></div>';
  h+='</div>';
  h+='<div class="section-hd"><h2>&#128202; 知识概览</h2></div>';
  h+='<div class="stats-bar">';
  h+='<div class="stat-card"><div class="stat-icon blue">&#129302;</div><div class="stat-info"><h3>'+totalProducts+'</h3><p>产品总数</p></div></div>';
  h+='<div class="stat-card"><div class="stat-icon cyan">&#128161;</div><div class="stat-info"><h3>'+totalSolutions+'</h3><p>解决方案</p></div></div>';
  h+='<div class="stat-card"><div class="stat-icon green">&#128196;</div><div class="stat-info"><h3>'+totalAssets+'</h3><p>资料文件</p></div></div>';
  h+='<div class="stat-card"><div class="stat-icon orange">&#127760;</div><div class="stat-info"><h3>'+totalLangs+'</h3><p>多语种版本</p></div></div>';
  h+='</div>';
  h+='<div class="section-hd"><h2>&#128293; 热门搜索</h2></div>';
  h+='<div class="hot-tags">';
  ['豹小秘Pro','招财豹','CleaniBot S55 Pro','LuckiBot Pro','清洁机器人','解决方案','AgentOS','产品PPT','竞品分析','客户案例'].forEach(function(t){
    h+='<span class="hot-tag" onclick="searchTag(\\''+t+'\\')">'+t+'</span>';
  });
  h+='</div>';
  h+='<div class="section-hd"><h2>&#128230; 产品分类</h2></div>';
  h+='<div class="cat-grid">';
  [{cat:'voice',label:'语音/接待机器人',sub:'接待·迎宾·问答',icon:'&#127897;'},{cat:'delivery',label:'递送/配送机器人',sub:'送餐·配送·物流',icon:'&#128230;'},{cat:'clean',label:'清洁机器人',sub:'洗地·扫地·吸尘',icon:'&#129529;'}].forEach(function(c){
    var cnt=PRODUCTS.filter(function(p){return p.cat===c.cat}).length;
    h+='<div class="cat-card" onclick="doSearchCat(\\''+c.cat+'\\')">';
    h+='<div class="cat-icon">'+c.icon+'</div>';
    h+='<div class="cat-info"><h3>'+c.label+'</h3><p>'+c.sub+' &middot; '+cnt+'款</p></div></div>';
  });
  h+='<div class="cat-card" onclick="showSolutions()"><div class="cat-icon">&#128161;</div><div class="cat-info"><h3>解决方案</h3><p>行业场景 &middot; '+SOLUTIONS.length+'个</p></div></div>';
  h+='<div class="cat-card" onclick="showLangs()"><div class="cat-icon">&#127760;</div><div class="cat-info"><h3>多语种物料</h3><p>全球市场 &middot; '+LANGS.length+'种语言</p></div></div>';
  h+='<div class="cat-card" onclick="selectItem(\\'corp-intro\\')"><div class="cat-icon">&#127970;</div><div class="cat-info"><h3>企业资料</h3><p>公司介绍·VI·认证</p></div></div>';
  h+='</div>';
  h+='<div class="section-hd"><h2>&#128337; 最近更新</h2></div>';
  h+='<div class="recent-list">';
  RECENT_UPDATES.forEach(function(r){
    h+='<div class="recent-item" onclick="selectItem(\\''+r.id+'\\')">';
    h+='<div class="recent-dot"></div>';
    h+='<div class="ri-info"><h4>'+r.label+'</h4><p>'+r.sub+'</p></div>';
    h+='<span class="recent-badge">'+r.badge+'</span>';
    h+='</div>';
  });
  h+='</div>';
  ca.innerHTML=h;
}

function doSearch(){
  var q=document.getElementById('searchInput').value.trim().toLowerCase();
  var ca=document.getElementById('contentArea');
  if(!q){goHome();return}
  document.getElementById('breadcrumb').innerHTML='&#128269; 搜索: '+q;
  var sq=q.replace(/\s/g,'');
  var hits=ALL_ITEMS.filter(function(p){
    var t=p.name+' '+p.zh+' '+p.desc+' '+(p.kw||'');
    return t.toLowerCase().includes(q)||t.toLowerCase().replace(/\s/g,'').includes(sq);
  });
  if(!hits.length){ca.innerHTML='<div style="text-align:center;padding:60px 0;color:#9CA3AF"><div style="font-size:48px;margin-bottom:16px">&#128269;</div><h2 style="font-size:18px;color:#111827">未找到结果</h2><p style="font-size:14px;margin-top:8px">试试其他关键词</p></div>';return}
  var h='<div style="margin-bottom:16px"><h2 style="font-size:16px;font-weight:600;color:#111827">搜索结果 ('+hits.length+')</h2></div><div class="search-results">';
  hits.forEach(function(p){
    var reg=REGIONS[p.region]||{};
    var ci=CATS[p.cat]?CATS[p.cat].icon:'';
    h+='<div class="search-hit" onclick="selectItem(\\''+p.id+'\\')"><h3>'+ci+' '+p.name+'</h3>';
    h+='<p>'+(reg.flag||'')+' '+(reg.name||'')+' &middot; '+p.zh+'</p></div>';
  });
  h+='</div>';ca.innerHTML=h;
}

var _aiCurrentProduct=null,_aiSelectedType=null,_aiSelectedModel=\'claude-opus-4-8\',_aiSelectedModelType=\'text\',_aiSelectedLang=\'中文(简体)\';
function toggleAIPanel(){var panel=document.getElementById(\'aiPanel\');if(!panel)return;panel.style.display=(panel.style.display===\'none\'||!panel.style.display)?\'block\':\'none\';}
function toggleModelDropdown(){var dd=document.querySelector(\'.model-dropdown\');if(dd)dd.classList.toggle(\'open\');}
document.addEventListener(\'click\',function(e){if(!e.target.closest(\'.model-dropdown\')){var dd=document.querySelector(\'.model-dropdown\');if(dd)dd.classList.remove(\'open\');}if(!e.target.closest(\'#langDropdown\')){var dd2=document.getElementById(\'langDropdown\');if(dd2)dd2.classList.remove(\'open\');}});
function toggleRefTag(el){el.classList.toggle(\'active\');}
function selectModel(el,model,mtype){document.querySelectorAll(\'.model-card\').forEach(function(c){c.classList.remove(\'selected\')});el.classList.add(\'selected\');_aiSelectedModel=model;_aiSelectedModelType=mtype||\'text\';var nameEl=document.querySelector(\'.model-current-name\');if(nameEl)nameEl.textContent=el.querySelector(\'.mc-name\').textContent;var dd=document.querySelector(\'.model-dropdown\');if(dd)dd.classList.remove(\'open\');}
function selectArticleType(el,type){document.querySelectorAll(\'.article-type-tag\').forEach(function(t){t.classList.remove(\'selected\')});el.classList.add(\'selected\');_aiSelectedType=type;}
function toggleLangDropdown(){var dd=document.getElementById(\'langDropdown\');if(dd)dd.classList.toggle(\'open\');}
function selectLang(el){var lang=el.getAttribute(\'data-lang\');if(!lang)return;_aiSelectedLang=lang;document.querySelectorAll(\'.lang-item\').forEach(function(i){i.classList.remove(\'selected\')});el.classList.add(\'selected\');var nameEl=document.querySelector(\'.lang-current-name\');if(nameEl)nameEl.textContent=lang;var dd=document.getElementById(\'langDropdown\');if(dd)dd.classList.remove(\'open\');}
function generateArticle(){
  if(!_aiSelectedType){alert(\'请先选择稿件类型\');return}
  var p=_aiCurrentProduct;if(!p)return;
  var activeTags=document.querySelectorAll(\'#refTagsArea .ref-card.active\');
  if(!activeTags.length){alert(\'请至少勾选一条参考资料\');return;}
  var selCaseIdxs=[],selHlIdxs=[],selSceneIdxs=[],selSpecKeys=[];
  activeTags.forEach(function(el){var tp=el.getAttribute(\'data-type\'),idx=parseInt(el.getAttribute(\'data-idx\'));if(tp===\'case\'&&!isNaN(idx))selCaseIdxs.push(idx);else if(tp===\'highlight\'&&!isNaN(idx))selHlIdxs.push(idx);else if(tp===\'scene\'&&!isNaN(idx))selSceneIdxs.push(idx);else if(tp===\'spec\')selSpecKeys.push(el.getAttribute(\'data-key\'));});
  var fp=Object.assign({},p);
  if(selCaseIdxs.length&&p.cases)fp.cases=selCaseIdxs.map(function(i){return p.cases[i]}).filter(Boolean);
  if(selHlIdxs.length&&p.highlights)fp.highlights=selHlIdxs.map(function(i){return p.highlights[i]}).filter(Boolean);
  if(selSceneIdxs.length&&p.scenes)fp.scenes=selSceneIdxs.map(function(i){return p.scenes[i]}).filter(Boolean);
  if(selSpecKeys.length&&p.specs){fp.specs={};selSpecKeys.forEach(function(k){if(p.specs[k])fp.specs[k]=p.specs[k]});}
  var btn=document.getElementById(\'aiGenBtn\');
  var status=document.getElementById(\'aiStatus\');
  var result=document.getElementById(\'aiResult\');
  btn.disabled=true;status.textContent=\'AI正在撰写中...\';result.style.display=\'none\';
  var prompt=_buildAIPrompt(_aiSelectedType,fp);
  fetch(\'/api/generate\',{method:\'POST\',headers:{\'Content-Type\':\'application/json\'},body:JSON.stringify({model:_aiSelectedModel,prompt:prompt})})
  .then(function(r){return r.json()})
  .then(function(data){
    if(data.ok&&data.content){
      var content=data.content;
      var html=\'<div class="art-section-label">AI生成内容（\'+_aiSelectedModel+\'）</div>\';
      html+=\'<div class="art-body">\';
      content.split(\'\\n\\n\').forEach(function(para){if(para.trim())html+=\'<p>\'+para.replace(/\\n/g,\'<br>\')+\'</p>\';});
      html+=\'</div>\';
      document.getElementById(\'aiResultText\').innerHTML=html;
      result.style.display=\'block\';btn.disabled=false;
      status.textContent=\'撰写完成 &#10003;\';setTimeout(function(){status.textContent=\'\'},2000);
    }else{throw new Error(data.error||\'API错误\');}
  })
  .catch(function(){
    var article=_buildArticleHtml(_aiSelectedType,fp);
    document.getElementById(\'aiResultText\').innerHTML=article;
    result.style.display=\'block\';btn.disabled=false;
    status.textContent=\'本地模板生成（API不可用）\';setTimeout(function(){status.textContent=\'\'},3000);
  });
}
function _buildAIPrompt(type,p){
  var name=p.name,zh=p.zh||p.name,desc=p.desc||\'智能服务机器人\';
  var hl=p.highlights&&p.highlights.length?p.highlights.join(\'、\'):\'智能化操作、高效稳定\';
  var sc=p.scenes&&p.scenes.length?p.scenes.join(\'、\'):\'商业场所、企业园区\';
  var cs=p.cases&&p.cases.length?p.cases.map(function(c){return c.name+\'：\'+c.desc}).join(\'；\'):\'规模商业落地\';
  var sp=p.specs&&Object.keys(p.specs).length?Object.entries(p.specs).slice(0,4).map(function(e){return e[0]+\' \'+e[1]}).join(\'、\'):\'先进技术配置\';
  var typeNames={policy:\'政策借势新闻稿\',brand:\'品牌故事新闻稿\',launch:\'产品发布新闻稿\',\'event-preview\':\'参会预热新闻稿\',exhibition:\'参展新闻通稿\',\'product-intro\':\'产品介绍GEO稿件\',\'case\':\'标杆案例稿件\',solution:\'行业解决方案稿件\',scene:\'应用场景稿件\',tech:\'技术优势稿件\',news:\'产品动态稿件\',\'seo-popular\':\'SEO科普问答型稿件\',\'seo-pitfall\':\'SEO避坑指南型稿件\',\'seo-comparison\':\'SEO选型对比型稿件\',\'seo-price\':\'SEO价格预算型稿件\',\'seo-scenario\':\'SEO场景解决方案型稿件\',\'seo-review\':\'SEO实测体验型稿件\',\'video-30s\':\'30秒视频脚本\',\'video-60s\':\'60秒视频脚本\',\'video-full\':\'2-3分钟完整视频脚本\',\'poster-activity\':\'活动宣传海报文案\',\'poster-festival\':\'节日宣传海报文案\',\'poster-trend\':\'借势传播海报文案\',\'ppt-solution\':\'解决方案PPT大纲\',\'ppt-product\':\'产品介绍PPT大纲\',\'ppt-scene\':\'场景PPT大纲\',\'ppt-case\':\'案例合集PPT大纲\'};
  var typeName=typeNames[type]||type;
  return \'请用\'+_aiSelectedLang+\'撰写以下内容。\\n\\n请为猎户星空服务机器人产品 \'+name+\'（\'+zh+\'）撰写一篇专业的\'+typeName+\'。\\n\\n产品描述：\'+desc+\'\\n核心亮点：\'+hl+\'\\n适用场景：\'+sc+\'\\n技术规格：\'+sp+\'\\n标杆案例：\'+cs+\'\\n\\n要求：\\n1. 文章结构清晰，分段落有标题\\n2. 内容专业严谨，引用数据需用（待核）标注\\n3. 字数不少于800字\\n4. 专业商务风格，全文使用\'+_aiSelectedLang+\'写作\';
}
function copyArticle(){
  var text=document.getElementById(\'aiResultText\').innerText;if(!text)return;
  if(navigator.clipboard){navigator.clipboard.writeText(text).then(function(){var btn=document.querySelector(\'.ai-copy-btn\');var orig=btn.textContent;btn.textContent=\'已复制！\';setTimeout(function(){btn.textContent=orig},1500)});}
  else{var ta=document.createElement(\'textarea\');ta.value=text;document.body.appendChild(ta);ta.select();document.execCommand(\'copy\');document.body.removeChild(ta);var btn=document.querySelector(\'.ai-copy-btn\');var orig=btn.textContent;btn.textContent=\'已复制！\';setTimeout(function(){btn.textContent=orig},1500);}
}
function _buildArticleHtml(type,p){
  if(type===\'video-30s\'||type===\'video-60s\'||type===\'video-full\'){
    var ver=type===\'video-30s\'?\'30秒\':type===\'video-60s\'?\'60秒\':\'完整版（2-3分钟）\';
    var body=_genTemplate(type,p);
    var h=\'\';
    h+=\'<div class="art-section-label">视频脚本 · \'+ver+\'</div>\';
    h+=\'<div style="background:#F9FAFB;border-radius:8px;padding:16px;font-size:13px;line-height:2;color:#111827">\';
    var paras=body.split(\'\\n\\n\');
    paras.forEach(function(para){if(para.trim())h+=\'<p>\'+para.replace(/\\n/g,\'<br>\').replace(/【([^】]*)】/g,\'<strong>【$1】</strong>\')+\'</p>\';});
    h+=\'</div>\';
    return h;
  }
  if(type.indexOf(\'poster-\')===0){var typeLabel=type===\'poster-activity\' ? \'活动海报\' : type===\'poster-festival\' ? \'节日海报\' : \'借势传播海报\';var body=_genTemplate(type,p);var h=\'\';h+=\'<div class="art-section-label">\'+\'宣传海报 · \'+typeLabel+\'</div>\';h+=\'<div style="background:#F9FAFB;border-radius:8px;padding:16px;font-size:13px;line-height:2;color:#111827">\';var paras=body.split(\'\\n\\n\');paras.forEach(function(para){if(para.trim())h+=\'<p>\'+para.replace(/\\n/g,\'<br>\').replace(/【([^】]*)】/g,\'<strong>【$1】</strong>\')+\'</p>\';});h+=\'</div>\';return h;}
  if(type.indexOf(\'ppt-\')===0){var typeLabel=type===\'ppt-solution\' ? \'解决方案PPT\' : type===\'ppt-product\' ? \'产品介绍PPT\' : type===\'ppt-scene\' ? \'场景PPT\' : \'案例合集PPT\';var body=_genTemplate(type,p);var h=\'\';h+=\'<div class="art-section-label">\'+\'销售PPT · \'+typeLabel+\'</div>\';h+=\'<div style="background:#F9FAFB;border-radius:8px;padding:16px;font-size:13px;line-height:2;color:#111827">\';var paras=body.split(\'\\n\\n\');paras.forEach(function(para){if(para.trim())h+=\'<p>\'+para.replace(/\\n/g,\'<br>\').replace(/【([^】]*)】/g,\'<strong>【$1】</strong>\')+\'</p>\';});h+=\'</div>\';return h;}
  var body=_genTemplate(type,p);
  var name=p.name,zh=p.zh||p.name;
  var imgUrl=(p.assets&&p.assets.image)?p.assets.image:\'\';
  var sc=p.scenes&&p.scenes.length?p.scenes:[\'商业场所\',\'企业园区\',\'公共场馆\'];
  var cs=p.cases&&p.cases.length?p.cases:[{name:\'某大型企业\',desc:\'成功应用，效果显著\'}];
  var hl=p.highlights&&p.highlights.length?p.highlights:[\'智能化操作\',\'高效稳定\',\'易于使用\'];
  var sp=p.specs&&Object.keys(p.specs).length?Object.entries(p.specs).slice(0,3).map(function(e){return e[0]+\' \'+e[1]}).join(\'、\'):\'先进技术配置\';
  var s0=sc[0]||\'商业场所\';
  var c0=cs[0]||{name:\'某企业\',desc:\'效果显著\'};
  var h0=hl[0]||\'智能技术\';
  var _cn=c0&&c0.name?c0.name:\'\';var ind=_cn.indexOf(\'餐\')>=0?\'餐饮\':_cn.indexOf(\'酒店\')>=0?\'酒店\':_cn.indexOf(\'医院\')>=0?\'医疗\':_cn.indexOf(\'政府\')>=0||_cn.indexOf(\'政务\')>=0?\'政务\':_cn.indexOf(\'商场\')>=0||_cn.indexOf(\'购物\')>=0?\'零售\':_cn.indexOf(\'银行\')>=0?\'金融\':_cn.indexOf(\'工厂\')>=0||_cn.indexOf(\'车间\')>=0?\'制造业\':_cn.indexOf(\'博物\')>=0?\'文旅\':_cn.indexOf(\'企业\')>=0||_cn.indexOf(\'公司\')>=0?\'企业\':_cn.indexOf(\'写字楼\')>=0||_cn.indexOf(\'园区\')>=0?\'商业\':\'服务\';
  var _cd=c0&&c0.desc?c0.desc:\'\';var val=_cd.indexOf(\'成本降\')>=0?\'成本降低\':_cd.indexOf(\'效率\')>=0?\'效率提升\':_cd.indexOf(\'满意度\')>=0?\'服务升级\':\'智能化升级\';
  var t1,t2;
  if(type===\'policy\'){t1=\'服务机器人政策落地期，猎户星空\'+name+\'完成\'+s0+\'等场景规模部署\';t2=\'AI与实体经济融合政策指引下，\'+name+\'在\'+sc.length+\'类核心场景积累落地数据\';}
  else if(type===\'brand\'){t1=\'猎户星空\'+name+\'研发团队历时18个月，完成\'+s0+\'场景商业化验证\';t2=name+\'（\'+zh+\'）从技术测试到规模落地：路径与数据复盘\';}
  else if(type===\'launch\'){t1=name+\'（\'+zh+\'）正式发布，\'+h0+\'能力支持\'+s0+\'场景12小时连续服务\';t2=\'猎户星空\'+name+\'商业化交付，适配\'+sc.length+\'类场景，参考集成周期14天\';}
  else if(type===\'event-preview\'){t1=\'猎户星空携\'+name+\'参加行业峰会，将展示\'+s0+\'场景实际运行效果\';t2=name+\'亮相本届展会：现场演示\'+h0+\'，展位号待确认\';}
  else if(type===\'exhibition\'){t1=\'猎户星空携\'+name+\'参展，\'+c0.name+\'等达成合作意向，接待人次待核\';t2=name+\'展会复盘：\'+s0+\'场景演示\'+cs.length+\'次，媒体报道数量待核\';}
  else if(type===\'product-intro\'){t1=\'猎户星空\'+name+\' AI机器人在\'+ind+\'行业\'+s0+\'场景的应用价值与\'+val;t2=name+\'在\'+ind+\'行业\'+s0+\'场景：\'+val+\'与智能化升级实践\';}
  else if(type===\'case\'){t1=c0.name+\'引入猎户星空\'+name+\'完成\'+ind+\'行业\'+s0+\'场景\'+val;t2=ind+\'行业\'+s0+\'场景：\'+name+\'在\'+c0.name+\'商业化部署与\'+val+\'实践\';}
  else if(type===\'solution\'){t1=ind+\'行业\'+s0+\'场景引入猎户星空\'+name+\'：\'+val+\'与ROI测算参考\';t2=\'猎户星空\'+name+\'在\'+ind+\'行业\'+s0+\'智能化解决方案：\'+val+\'落地路径\';}
  else if(type===\'scene\'){t1=ind+\'行业\'+s0+\'场景自动化：猎户星空\'+name+\'助力企业\'+val;t2=name+\'在\'+ind+\'行业\'+s0+\'场景的部署建议与\'+val+\'实践指南\';}
  else if(type===\'tech\'){t1=\'猎户星空\'+name+\' \'+h0+\'技术在\'+ind+\'行业\'+s0+\'场景的\'+val+\'验证\';t2=name+\'核心技术解析：\'+ind+\'行业\'+s0+\'场景\'+val+\'的实现路径\';}
  else if(type===\'news\'){t1=\'猎户星空\'+name+\'迭代升级：\'+ind+\'行业\'+s0+\'场景适配增强，\'+val+\'能力显著提升\';t2=name+\'产品动态：\'+ind+\'行业\'+s0+\'场景优化，\'+h0+\'助力\'+val;}
  else if(type===\'seo-popular\'){t1=\'什么是\'+name+\'？\'+ind+\'行业\'+s0+\'场景完全解答\';t2=name+\'（\'+zh+\'）常见问题FAQ：功能、价格、适用场景一文看懂\';}
  else if(type===\'seo-pitfall\'){t1=\'购买\'+name+\'必看：\'+ind+\'行业\'+s0+\'场景选型避坑指南\';t2=\'如何避免\'+name+\'选型踩坑？\'+ind+\'行业真实案例+正确选购方法\';}
  else if(type===\'seo-comparison\'){t1=name+\'哪个好？\'+ind+\'行业服务机器人选型对比分析（2025版）\';t2=\'怎么选\'+ind+\'行业服务机器人？\'+name+\'与同类产品全方位对比\';}
  else if(type===\'seo-price\'){t1=name+\'多少钱？\'+ind+\'行业\'+s0+\'场景部署预算完整参考\';t2=\'如何预算\'+name+\'的采购成本？\'+s0+\'场景配置方案与价格指南\';}
  else if(type===\'seo-scenario\'){t1=\'如何解决\'+ind+\'行业\'+s0+\'场景的\'+val+\'问题？\'+name+\'实战解决方案\';t2=ind+\'行业\'+s0+\'场景\'+val+\'怎么做到？\'+name+\'落地指南与ROI参考\';}
  else if(type===\'seo-review\'){t1=name+\'实测报告：\'+c0.name+\'在\'+s0+\'场景亲历\'+val+\'（真实数据）\';t2=\'亲测\'+name+\'：\'+ind+\'行业\'+cs.length+\'家客户案例汇总与\'+val+\'评价\';}
  else{t1=\'猎户星空\'+name+\'产品稿件\';t2=name+\'（\'+zh+\'）产品与场景信息汇总\';}
  var imgEl=imgUrl?\'<img src="\'+imgUrl+\'" style="width:100%;border-radius:6px;object-fit:cover;height:90px" />\':\'<div style="background:#F3F4F6;border-radius:6px;height:90px;display:flex;align-items:center;justify-content:center;color:#9CA3AF;font-size:11px">暂无图片</div>\';
  var h=\'\';
  h+=\'<div class="art-section-label">备选标题</div>\';
  h+=\'<div class="art-titles"><p><strong>标题一：</strong>\'+t1+\'</p><p><strong>标题二：</strong>\'+t2+\'</p></div>\';
  h+=\'<div class="art-section-label">正文</div>\';
  h+=\'<div class="art-body">\';
  var fsImgUrl=imgUrl||(p.assets&&p.assets.image?p.assets.image:\'\');
  var paras=body.split(\'\\n\\n\').filter(function(x){return x.trim()});
  var midIdx=Math.floor(paras.length/2);
  var endIdx=paras.length>2?paras.length-2:0;
  paras.forEach(function(para,idx){
    var lbl=idx===0?\'【导语】\':idx===1&&midIdx!==1?\'【产品亮点】\':idx===midIdx&&midIdx>1?\'【应用场景】\':idx===endIdx&&endIdx>midIdx?\'【标杆案例】\':\'\';
    if(lbl)h+=\'<div style="font-size:12px;font-weight:700;color:#2563EB;margin:14px 0 6px;padding-bottom:3px;border-bottom:2px solid #EFF6FF">\'+lbl+\'</div>\';
    if(para.trim())h+=\'<p>\'+para.replace(/\\n/g,\'<br>\').replace(/【([^】]*)】/g,\'<strong>【$1】</strong>\')+\'</p>\';
    if(idx===0)h+=\'<div style="margin:16px 0;text-align:center"><img src="\'+fsImgUrl+\'" alt="\'+name+\'产品正面图" style="width:100%;max-height:300px;object-fit:contain;border-radius:12px" /><div style="font-size:12px;color:#6B7280;margin-top:6px">\'+name+\'产品正面图</div></div>\';
    else if(idx===midIdx&&midIdx>0)h+=\'<div style="margin:16px 0;text-align:center"><img src="\'+fsImgUrl+\'" alt="\'+name+\'应用场景图（\'+s0+\'）" style="width:100%;max-height:300px;object-fit:contain;border-radius:12px" /><div style="font-size:12px;color:#6B7280;margin-top:6px">\'+name+\'应用场景图（\'+s0+\'）</div></div>\';
    else if(idx===endIdx&&endIdx>midIdx&&endIdx>0)h+=\'<div style="margin:16px 0;text-align:center"><img src="\'+fsImgUrl+\'" alt="\'+name+\'标杆案例图（\'+c0.name+\'）" style="width:100%;max-height:300px;object-fit:contain;border-radius:12px" /><div style="font-size:12px;color:#6B7280;margin-top:6px">\'+name+\'标杆案例图（\'+c0.name+\'）</div></div>\';
  });
  var bodyLen=body.replace(/\\n/g,\'\').length;
  var ext=\'\';
  ext+=\'<p>\'+s0+\'场景引入智能机器人的核心驱动力通常包括：压降人力投入、提升服务一致性、延长有效服务时长。\'+name+\'通过\'+hl.slice(0,2).join(\'与\')+\'能力，在上述三个维度均已有客户完成商业化验证，具体数据因部署规模而异，可参考实际案例数据。</p>\';
  ext+=\'<p>在\'+sc.slice(0,Math.min(3,sc.length)).join(\'、\')+\'等场景，\'+name+\'均已有实际部署案例。运营成本降幅、服务响应时间变化及客户满意度变动数据，以客户实际环境测量为准，平台可提供典型案例的参考数据（待核）。</p>\';
  ext+=\'<p>猎户星空核心技术方向包括自主导航、人机交互与多机协调调度，已形成感知、决策、执行的完整链路。\'+name+\'的技术规格详见产品白皮书，各项参数均经实验室及真实场景双重验证，不适用与未经对比测试产品的横向比较结论。</p>\';
  ext+=\'<p>随着大模型在机器人场景中的应用逐步深入，猎户星空将持续迭代\'+name+\'的指令理解与情景适应能力。如需了解\'+s0+\'场景的完整部署建议与ROI测算方法，可联系猎户星空商务团队获取方案文档。</p>\';
  ext+=\'<p>从行业整体趋势来看，商用服务机器人正从单点替代人工向多机协同调度演进。猎户星空\'+name+\'支持与现有信息化系统（如POS、门禁、楼层调度平台）对接，具体接口协议和集成工作量以项目评估为准，通常标准集成周期不超过14天，最大程度降低对日常运营的干扰。</p>\';
  ext+=\'<p>在实际落地过程中，建议客户重点关注三个环节：一是场地结构评估，确认走廊宽度不低于1.5米、地面材质适合机器人行驶、灯光条件满足视觉识别需求；二是业务流程适配，明确机器人承接的任务类型和服务触发方式；三是员工协作培训，帮助一线人员理解人机协作边界，充分发挥\'+name+\'的效能。</p>\';
  ext+=\'<p>猎户星空目前已在全国主要城市建立本地化服务团队，提供设备安装调试、定期维保检修和远程故障诊断等全周期支持。连锁或多站点部署客户可接入统一设备管理平台，实现跨区域设备状态监控、任务调度数据集中分析，为持续优化服务效率提供数据支撑。</p>\';
  ext+=\'<p>综合当前市场实践数据，商用服务机器人在标准化、高频次服务场景中的投资回报周期正在持续缩短。以\'+s0+\'为例，引入\'+name+\'后，一线服务人员通常可将精力集中于异常处理和客户关系维护等更高价值工作。猎户星空建议在部署前完成场景日均服务量评估，以便制定最优部署规模与人机配比方案，实现效益最大化。</p>\';
  h+=\'<div style="font-size:12px;font-weight:700;color:#2563EB;margin:14px 0 6px;padding-bottom:3px;border-bottom:2px solid #EFF6FF">【行业展望】</div>\';
  h+=ext;
  h+=\'</div>\';
  var allText=body+ext+t1+t2;
  var wc=allText.replace(/<[^>]+>/g,\'\').replace(/\\s/g,\'\').length;
  var rawNums=(allText.match(/\\d+[%万千亿元+]/g)||[]).concat(allText.match(/\\d{2,}/g)||[]);
  var seenN={},uniqueNums=[];
  rawNums.forEach(function(n){if(!seenN[n]){seenN[n]=1;uniqueNums.push(n);}});
  uniqueNums=uniqueNums.slice(0,6);
  var kws=[name,zh].concat(hl.slice(0,4)).concat(sc.slice(0,3)).concat([\'猎户星空\',\'智能机器人\',\'商用服务\',\'AI机器人\']).filter(function(k,i,a){return k&&a.indexOf(k)===i}).slice(0,12);
  var links=[name+\'产品官网页面\',\'猎户星空官网首页\',\'猎户星空成功案例\'];
  sc.slice(0,3).forEach(function(s){links.push(s+\'智能化解决方案\');});
  links.push(\'猎户星空产品对比页\',\'猎户星空AgentOS平台\');
  h+=\'<div class="art-section-label">核心数据</div>\';
  h+=\'<div style="background:#F9FAFB;border-radius:6px;padding:10px 14px;font-size:12px;color:#374151;line-height:2">\';
  if(uniqueNums.length)h+=uniqueNums.map(function(n,i){return \'<span style="display:inline-block;margin-right:16px;font-weight:600">\'+(i+1)+\'. \'+n+\'</span>\'}).join(\'\');
  else h+=\'• \'+sp;
  h+=\'</div>\';
  h+=\'<div class="art-section-label">内链建议</div>\';
  h+=\'<div style="background:#F9FAFB;border-radius:6px;padding:10px 14px;font-size:12px;line-height:2">\';
  links.slice(0,7).forEach(function(l,i){h+=\'<span style="color:#1664FF;display:block">[\'+( i+1)+\'] \'+l+\'</span>\';});
  h+=\'</div>\';
  h+=\'<div class="art-section-label">关键词</div>\';
  h+=\'<div style="display:flex;flex-wrap:wrap;gap:6px;padding:6px 0">\';
  kws.forEach(function(k){h+=\'<span style="padding:3px 10px;background:#EFF6FF;color:#1664FF;border-radius:4px;font-size:11px">\'+k+\'</span>\';});
  h+=\'</div>\';
  h+=\'<div class="art-wc">正文约\'+wc+\'字</div>\';
  return h;
}
function _genTemplate(type,p){
  var name=p.name,zh=p.zh||p.name,desc=p.desc||\'猎户星空智能服务机器人\';
  var hl=p.highlights&&p.highlights.length?p.highlights:[\'智能化操作\',\'高效稳定\',\'易于使用\'];
  var sc=p.scenes&&p.scenes.length?p.scenes:[\'商业场所\',\'企业园区\'];
  var cs=p.cases&&p.cases.length?p.cases:[{name:\'某大型企业\',desc:\'成功应用，效果显著\'}];
  var sp=p.specs&&Object.keys(p.specs).length?Object.entries(p.specs).slice(0,3).map(function(e){return e[0]+\' \'+e[1]}).join(\'、\'):\'先进技术配置\';
  var c0=cs[0];
  var tpl={
    \'policy\':function(){return name+\'（\'+zh+\'）在政策落地期完成\'+sc.length+\'类场景部署，含\'+sc.slice(0,2).join(\'、\')+\'\\n\\n服务机器人已被明确纳入政策支持范围，猎户星空\'+name+\'在政策窗口期内完成了\'+sc.slice(0,2).join(\'、\')+\'等\'+sc.length+\'类场景的商业化交付。\\n\\n一、政策背景\\n当前政策推进AI实体化落地，商用服务机器人是核心方向之一。猎户星空\'+name+\'（\'+zh+\'）已进入相关政府采购目录（以实际公告为准）。\\n\\n二、产品能力\\n\'+name+\'的核心能力包括：\'+hl.slice(0,3).join(\'、\')+\'。适配场景：\'+sc.join(\'、\')+\'。技术规格：\'+sp+\'。\\n\\n三、落地案例\\n\'+c0.name+\'：\'+c0.desc+\'。\\n\\n四、部署参考\\n集成周期约14天（含调试），维保体系覆盖北上广深等约（待核）个城市。如需了解政府采购资质文件，可联系猎户星空商务团队。\';},
    \'brand\':function(){return \'猎户星空\'+name+\'：\'+sc.length+\'类场景商业化交付背后的产品逻辑\\n\\n猎户星空\'+name+\'（\'+zh+\'）已完成\'+sc.length+\'类场景的商业化交付，这一结果来自约（待核）个月的迭代验证，而非单一功能发布。\\n\\n一、需求来源\\n\'+name+\'的开发从\'+sc.slice(0,2).join(\'、\')+\'等场景的实际痛点出发，核心需求包括：服务一致性保障、夜间无人值守、多机协调调度。\\n\\n二、能力构成\\n\'+name+\'形成了\'+hl.slice(0,3).join(\'、\')+\'等差异化能力，技术规格：\'+sp+\'。这些能力均基于真实场景数据训练和验证。\\n\\n三、客户验证\\n已服务客户包括：\'+cs.slice(0,2).map(function(c){return c.name+\'（\'+c.desc+\'）\'}).join(\'、\')+\'等，客户数量\'+cs.length+\'家（以实际签约为准）。\\n\\n如需了解\'+name+\'完整产品手册，访问 cn.orionstar.com 或联系商务团队。\';},
    \'launch\':function(){return name+\'（\'+zh+\'）正式发布：\'+h0+\'能力覆盖\'+sc.length+\'类场景，集成周期参考14天\\n\\n猎户星空\'+name+\'（\'+zh+\'）今日完成商业化发布，产品定位\'+sc[0]+\'等场景的自动化服务，核心能力为\'+h0+\'。\\n\\n一、发布信息\\n产品名称：\'+name+\'（\'+zh+\'）。核心规格：\'+sp+\'。首批适配场景：\'+sc.slice(0,3).join(\'、\')+\'。\\n\\n二、核心能力\\n\'+name+\'的技术亮点：\'+hl.map(function(h,i){return (i+1)+\'. \'+h}).join(\'；\')+\'。\\n\\n三、客户验证\\n发布前，\'+name+\'已完成\'+c0.name+\'等客户的预商业化部署验证，\'+c0.desc+\'。\\n\\n四、采购参考\\n产品单机参考价（待核），集成周期14天（含调试培训），配套维保SLA协议。详情请联系猎户星空商务团队：cn.orionstar.com。\';},
    \'event-preview\':function(){return \'猎户星空携\'+name+\'参展：将演示\'+h0+\'在\'+s0+\'场景的实际运行效果\\n\\n猎户星空将携旗下产品\'+name+\'（\'+zh+\'）参加本届行业峰会，展位号待确认，现场将运行\'+s0+\'场景实机演示。\\n\\n一、参展产品\\n\'+name+\'（\'+zh+\'）。核心展示能力：\'+h0+\'。现场将在\'+s0+\'还原场景下完成至少（待核）次服务闭环演示。\\n\\n二、产品规格（供媒体参考）\\n\'+sp+\'。适配场景：\'+sc.join(\'、\')+\'。已服务客户：\'+cs.slice(0,2).map(function(c){return c.name}).join(\'、\')+\'等。\\n\\n三、采访安排\\n如需采访、拍摄或产品体验预约，请提前联系猎户星空公关团队，联系方式详见官网 cn.orionstar.com。\';},
    \'exhibition\':function(){return \'猎户星空\'+name+\'展会情况通报：\'+c0.name+\'等客户现场达成合作意向\\n\\n本届展会，猎户星空\'+name+\'（\'+zh+\'）完成\'+sc.slice(0,2).join(\'、\')+\'等场景实机演示，\'+c0.name+\'等客户现场达成合作意向，接待访客约（待核）人次。\\n\\n【参展产品】\\n\'+name+\'（\'+zh+\'）\\n\\n【展示内容】\\n\'+hl.map(function(h,i){return (i+1)+\'. \'+h}).join(\'\\n\')+\'\\n\\n【现场情况】\\n接待意向客户约（待核）家，媒体报道（待核）篇，现场演示次数（待核）次。\\n\\n【已落地案例参考】\\n\'+cs.slice(0,2).map(function(c){return c.name+\'：\'+c.desc}).join(\'\\n\')+\'\\n\\n【联系方式】\\n北京猎户星空科技有限公司\\n官网：cn.orionstar.com\';},
    \'product-intro\':function(){return name+\'（\'+zh+\'）：面向\'+s0+\'等\'+sc.length+\'类场景的智能服务机器人，核心能力含\'+h0+\'\\n\\n猎户星空\'+name+\'（\'+zh+\'）面向\'+sc.slice(0,2).join(\'、\')+\'等场景研发，核心能力为\'+h0+\'，已在\'+cs.length+\'家客户完成商业化部署验证。\\n\\n一、产品定位\\n\'+desc+\'\\n\\n二、核心能力\\n\'+hl.map(function(h,i){return (i+1)+\'. \'+h}).join(\'\\n\')+\'\\n\\n三、技术规格\\n\'+sp+\'（详见产品白皮书，以官方发布为准）\\n\\n四、适用场景\\n\'+sc.map(function(s){return \'- \'+s}).join(\'\\n\')+\'\\n\\n五、参考案例\\n\'+cs.slice(0,3).map(function(c){return \'- \'+c.name+\'：\'+c.desc}).join(\'\\n\')+\'\\n\\n六、采购咨询\\n联系猎户星空商务团队：cn.orionstar.com 或拨打400热线（以官网为准）。\';},
    \'case\':function(){return c0.name+\'引入猎户星空\'+name+\'完成\'+s0+\'场景自动化改造，ROI周期数据待核\\n\\n\'+c0.name+\'在\'+s0+\'场景引入猎户星空\'+name+\'（\'+zh+\'），完成自动化服务改造。\'+c0.desc+\'。本文梳理其决策路径与部署情况，运营指标数据以客户实际测量为准。\\n\\n一、客户背景\\n\'+c0.name+\'在\'+s0+\'场景面临主要挑战：高峰期人手紧张、服务一致性难以保障、运营成本压力持续。\\n\\n二、引入过程\\n评估阶段约（待核）周，集成调试约14天，培训周期约（待核）天。\\n\\n三、部署效果\\n\'+c0.desc+\'。成本变化、效率提升数据以客户实际环境测量为准（参考数据可联系获取）。\\n\\n四、产品能力支撑\\n\'+name+\'核心能力：\'+hl.slice(0,3).join(\'、\')+\'。技术规格：\'+sp+\'。\\n\\n五、可复制性\\n\'+name+\'目前已在\'+cs.slice(0,2).map(function(c){return c.name}).join(\'、\')+\'等\'+cs.length+\'家客户完成类似部署，集成方案可参考标准化流程。\';},
    \'solution\':function(){return s0+\'场景引入服务机器人的ROI测算框架：猎户星空\'+name+\'参考回收期6-12个月\\n\\n\'+s0+\'场景的智能化改造核心逻辑是通过部署\'+name+\'，在人力成本、服务时长和一致性三个维度产生可量化改变。ROI计算需结合客户实际规模，参考回收期6-12个月（待核，以实际报价为准）。\\n\\n一、\'+s0+\'核心痛点\\n高峰期人手不足、服务标准难统一、夜间及假日覆盖缺口大。\\n\\n二、\'+name+\'方案构成\\n\'+hl.map(function(h,i){return (i+1)+\'. \'+h}).join(\'\\n\')+\'\\n适配场景：\'+sc.join(\'、\')+\'\\n技术规格：\'+sp+\'\\n\\n三、已验证案例\\n\'+cs.slice(0,2).map(function(c){return \'- \'+c.name+\'：\'+c.desc}).join(\'\\n\')+\'\\n\\n四、ROI测算参考\\n人力替代量、维护成本、集成费用等关键变量因客户规模而异。猎户星空商务团队可提供定制化测算模型，联系：cn.orionstar.com。\';},
    \'scene\':function(){var s1=sc[0]||\'商业场所\',s2=sc[1]||\'\',out=\'\';out+=s1+\'场景部署\'+name+\'：日均服务约（待核）次，响应时长较人工缩短约40%（待核）\\n\\n\';out+=\'猎户星空\'+name+\'（\'+zh+\'）在\'+s1+\'场景的部署数据显示，主要改善集中在响应速度和服务时长覆盖两个维度，具体数值以各客户实际测量为准。\\n\\n\';out+=\'一、\'+s1+\'部署效果\\n\'+name+\'通过\'+(hl[0]||\'智能技术\')+\'，在\'+s1+\'场景实现了服务闭环。客户\'+c0.name+\'反馈：\'+c0.desc+\'。\\n\\n\';if(s2)out+=\'二、\'+s2+\'场景延伸\\n\'+name+\'在\'+s2+\'场景已通过\'+(cs[1]?cs[1].name:\'合作客户\')+\'验证，核心能力：\'+(hl[1]||\'多场景适配\')+\'，关键指标待核。\\n\\n\';out+=\'三、部署建议\\n日均服务量50次以上的场景，投入产出比相对明确。单机日均服务量低于20次的场景建议先评估需求匹配度。\\n\\n\';out+=\'如需获取\'+s1+\'场景的完整部署方案和参考数据，联系猎户星空商务：cn.orionstar.com。\';return out;},
    \'tech\':function(){return h0+\'技术解析：\'+name+\'在\'+s0+\'场景实测数据与实现原理\\n\\n猎户星空\'+name+\'（\'+zh+\'）的\'+h0+\'能力已在\'+s0+\'等\'+sc.length+\'类场景完成实机验证，核心指标（待核，以白皮书为准）。本文从技术实现角度说明其原理与适用边界。\\n\\n一、技术能力构成\\n\'+hl.map(function(h,i){return (i+1)+\'. \'+h}).join(\'\\n\')+\'\\n\\n二、技术规格\\n\'+sp+\'（完整参数详见产品白皮书，以官方文档为准）\\n\\n三、验证案例\\n\'+cs.slice(0,2).map(function(c){return \'- \'+c.name+\'：\'+c.desc}).join(\'\\n\')+\'\\n\\n四、技术边界说明\\n\'+name+\'适用于\'+sc.join(\'、\')+\'等结构化服务场景；非结构化环境（如拥挤通道、强逆光）下性能存在一定限制，具体边界条件参见白皮书。\\n\\n如需深度技术文档，联系猎户星空：cn.orionstar.com。\';},
    \'news\':function(){return \'猎户星空\'+name+\'完成\'+s0+\'等\'+sc.length+\'类场景迭代，新版本集成周期约14天\\n\\n猎户星空\'+name+\'（\'+zh+\'）近期完成版本迭代，新增\'+s0+\'场景适配并优化了\'+h0+\'能力。此次更新的触发来自\'+c0.name+\'等客户的实际使用反馈。\\n\\n一、本次更新内容\\n主要改进：\'+hl.slice(0,3).join(\'、\')+\'。适配场景新增（以实际发布为准）。版本号及发布日期以官方公告为准。\\n\\n二、客户反馈来源\\n\'+c0.name+\'反馈：\'+c0.desc+\'。\\n\\n三、版本升级方式\\n现有客户升级方式：OTA推送或现场技术支持（按合同约定），升级周期约（待核）天。\\n\\n如需了解本次更新的完整 Release Notes，联系猎户星空：cn.orionstar.com。\';},
    \'video-30s\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\';return \'【一句话说明】这条视频讲的是：\'+name+\'在\'+s0+\'真有用\\n\\n【视频脚本】\\n版本：30秒\\n\\n画面 | 时长 | 台词/音效 | 说明\\n---|---|---|---\\n开场镜头 | 0-3秒 | \'+name+\'，来了！ | 机器人出场，第一句话直接进主题\\n\'+s0+\'场景 | 3-10秒 | 客户：\'+h0+\'能处理吗？\'+name+\'：当然可以！ | 人机对话原声，功能长在场景里\\n问题解决闭环 | 10-25秒 | \'+h0+\'全程演示 | 展示"真有用"，完整的问题-响应-解决闭环\\n结尾 | 25-30秒 | 猎户星空，让机器人真有用 | 猎户星空logo\\n\\n【封面设计】\\n顶部：认准猎户星空\\n中间黄字：\'+h0+\'\\n白字：在\'+s0+\'干活\\n底部分类标签：智慧\'+s0+\'\\n\\n【标题】\\n猎户星空\'+name+\'：\'+h0+\'在\'+s0+\'真有用 | 30秒看懂\\n\\n【审核清单】\\n- [ ] 一句话说清讲什么\\n- [ ] 功能长在场景里（不念参数）\\n- [ ] 语音交互有原声\\n- [ ] 第一句话直接进主题\\n- [ ] 有完整的"问题-响应-解决"闭环\\n- [ ] 围绕"真有用"\';},
    \'video-60s\':function(){var s0=sc[0]||\'商业场所\',s1=sc[1]||sc[0]||\'服务场景\',h0=hl[0]||\'智能技术\';return \'【一句话说明】这条视频讲的是：\'+name+\'如何在\'+s0+\'做到真有用\\n\\n【视频脚本】\\n版本：60秒\\n\\n画面 | 时长 | 台词/音效 | 说明\\n---|---|---|---\\n开场 | 0-3秒 | 你知道\'+s0+\'最头疼的是什么吗？ | 直接抛出痛点\\n痛点呈现 | 3-10秒 | 人手不够/效率太低/成本太高 | 共鸣建立\\n\'+name+\'登场 | 10-20秒 | \'+name+\'，来解决这个问题！ | 产品亮相+\'+h0+\'演示\\n人机互动 | 20-45秒 | 客户：\'+h0+\'行吗？\'+name+\'：请看！ | 语音交互原声，功能长在场景里\\n效果展示 | 45-55秒 | 问题解决了！ | 完整的问题-响应-解决闭环\\n结尾 | 55-60秒 | 猎户星空，让机器人真有用 | 猎户星空logo\\n\\n【封面设计】\\n顶部：认准猎户星空\\n中间黄字：\'+h0+\'\\n白字：在\'+s0+\'干活\\n底部分类标签：智慧\'+s0+\'\\n\\n【标题】\\n猎户星空\'+name+\'解决\'+s0+\'效率难题 | 60秒实测\\n\\n【审核清单】\\n- [ ] 一句话说清讲什么\\n- [ ] 功能长在场景里（不念参数）\\n- [ ] 语音交互有原声\\n- [ ] 第一句话直接进主题\\n- [ ] 有完整的"问题-响应-解决"闭环\\n- [ ] 围绕"真有用"\';},
    \'video-full\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\',h1=hl[1]||hl[0]||\'高效稳定\';return \'【一句话说明】这条视频讲的是：猎户星空\'+name+\'在\'+s0+\'全场景真实应用\\n\\n【视频脚本】\\n版本：完整版（2-3分钟）\\n\\n画面 | 时长 | 台词/音效 | 说明\\n---|---|---|---\\n开场 | 0-5秒 | 在\'+s0+\'，有一个机器人正在改变一切 | 悬念开场，直接进主题\\n痛点呈现 | 5-20秒 | \'+s0+\'的挑战：人力成本/效率/服务一致性 | 建立共鸣\\n\'+name+\'登场 | 20-40秒 | 认识一下：猎户星空\'+name+\'！\'+h0+\'！ | 产品介绍，核心卖点\\n场景演示1 | 40-80秒 | 客户：这个能处理吗？\'+name+\'：没问题！ | 语音交互原声，功能长在场景里\\n场景演示2 | 80-120秒 | 看看\'+name+\'如何\'+h1+\'... | 第二场景，展示多功能\\n客户证言 | 120-150秒 | 引入后，效率大幅提升！ | 真实客户反馈\\n总结 | 150-170秒 | \'+name+\'，\'+h0+\'，让\'+s0+\'更智能 | 升华主题\\n结尾 | 170-180秒 | 猎户星空，让机器人真有用 | 猎户星空logo\\n\\n【封面设计】\\n顶部：选真有用机器人／认准猎户星空\\n中间黄字：\'+h0+\'\\n白字：在\'+s0+\'干活\\n底部分类标签：智慧\'+s0+\'\\n\\n【标题】\\n猎户星空\'+name+\'：\'+h0+\'在\'+s0+\'真实应用全记录\\n\\n【审核清单】\\n- [ ] 一句话说清讲什么\\n- [ ] 功能长在场景里（不念参数）\\n- [ ] 语音交互有原声\\n- [ ] 第一句话直接进主题\\n- [ ] 有完整的"问题-响应-解决"闭环\\n- [ ] 围绕"真有用"\';},
  \'poster-activity\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\';return \'【一句话说明】这张海报讲的是：猎户星空\'+name+\'助力\'+s0+\'活动（20字内）\\n\\n【海报文案】\\n主标题：\'+name+\'，智享\'+s0+\'\\n副标题：\'+h0+\'，让服务更高效\\n正文：猎户星空\'+name+\'（\'+zh+\'），专为\'+s0+\'设计，\'+h0+\'，助力现场高效运营，提升参与者体验\\n行动号召：扫码了解更多\\n\\n【海报设计建议】\\n风格：科技感/商务\\n主色调：蓝色+白色\\n图片建议：\'+name+\'产品正面图+\'+s0+\'活动场景背景\\n排版建议：主标题居上，产品图居中，正文居下\\n\\n【二维码区域】\\n建议放置：官网链接（cn.orionstar.com）/活动报名链接\';},
  \'poster-festival\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\';return \'【一句话说明】这张海报讲的是：猎户星空\'+name+\'节日祝福与品牌传播（20字内）\\n\\n【海报文案】\\n主标题：智慧相伴，共赢新年\\n副标题：猎户星空\'+name+\'为\'+s0+\'护航\\n正文：以科技之力，让\'+s0+\'焕新升级。\'+name+\'（\'+zh+\'），专注\'+h0+\'，为您的业务保驾护航，共创智能服务新未来\\n行动号召：立即咨询\\n\\n【海报设计建议】\\n风格：节日氛围\\n主色调：红色+金色\\n图片建议：\'+name+\'产品图+节日元素（灯笼/烟花/新春装饰等）\\n排版建议：主标题居上，产品图居中，正文居下\\n\\n【二维码区域】\\n建议放置：官网链接（cn.orionstar.com）/联系方式\';},
  \'poster-trend\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\';return \'【一句话说明】这张海报讲的是：猎户星空\'+name+\'借势热点引领\'+s0+\'智能化（20字内）\\n\\n【海报文案】\\n主标题：AI时代，智胜未来\\n副标题：\'+name+\'引领\'+s0+\'智能化变革\\n正文：当AI技术席卷全球，猎户星空\'+name+\'（\'+zh+\'）已提前布局\'+s0+\'等核心场景，\'+h0+\'助力企业抢占先机，赢在智能化转型关键节点\\n行动号召：扫码了解更多\\n\\n【海报设计建议】\\n风格：科技感\\n主色调：深蓝色+亮蓝色渐变\\n图片建议：\'+name+\'产品图+AI科技视觉元素（芯片/电路/数据流）\\n排版建议：主标题居上，产品图居中，正文居下\\n\\n【二维码区域】\\n建议放置：官网链接（cn.orionstar.com）/联系方式\';},
  \'ppt-solution\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\',h1=hl[1]||hl[0]||\'高效稳定\',h2=hl[2]||hl[0]||\'稳定运行\',s1=sc[1]||sc[0]||\'服务场景\',s2=sc[2]||sc[0]||\'多类场景\';return \'【PPT大纲】\\n页数建议：15-20页\\n\\n第1页：封面\\n标题：\'+s0+\'智能化解决方案\\n副标题：猎户星空 · 北京猎户星空科技有限公司\\n\\n第2页：目录\\n1. 行业背景\\n2. 产品介绍\\n3. 核心亮点\\n4. 应用场景\\n5. 标杆案例\\n6. 合作方案\\n\\n第3页：行业背景\\n\'+s0+\'现状：人力成本持续上升，服务一致性难以保障，夜间及假日覆盖缺口大\\n痛点：效率低、成本高、服务标准化难\\n\\n第4-6页：产品介绍\\n产品名：\'+name+\'（\'+zh+\'）\\n定位：\'+desc+\'\\n核心参数：\'+sp+\'\\n适配场景：\'+sc.join(\'、\')+\'\\n\\n第7-9页：核心亮点\\n亮点一：\'+h0+\'\\n亮点二：\'+h1+\'\\n亮点三：\'+h2+\'\\n（每页一个亮点，配功能示意图）\\n\\n第10-12页：应用场景\\n场景一：\'+s0+\'\\n场景二：\'+s1+\'\\n场景三：\'+s2+\'\\n（每页一个场景，配现场实拍图）\\n\\n第13-15页：标杆案例\\n\'+cs.slice(0,3).map(function(c,i){return \'案例\'+(i+1)+\'：\'+c.name+\'\\n效果：\'+c.desc}).join(\'\\n\\n\')+\'\\n\\n第16页：合作方案\\n合作模式：POC验证 → 商业化部署 → 全周期运营维保\\n集成周期：约14天（含调试培训）\\n联系方式：cn.orionstar.com / 400热线（以官网为准）\\n\\n【每页内容包含】标题 + 要点bullet + 配图建议\';},
  \'ppt-product\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\';return \'【PPT大纲】\\n页数建议：15-20页\\n\\n第1页：封面\\n标题：\'+name+\'产品介绍\\n副标题：猎户星空 · 北京猎户星空科技有限公司\\n\\n第2页：目录\\n1. 行业背景\\n2. 产品介绍\\n3. 核心亮点\\n4. 应用场景\\n5. 标杆案例\\n6. 合作方案\\n\\n第3页：行业背景\\n\'+s0+\'行业现状与痛点：服务效率瓶颈、人力成本压力、智能化升级迫切需求\\n\\n第4-6页：产品介绍\\n产品名：\'+name+\'（\'+zh+\'）\\n核心定位：\'+desc+\'\\n产品规格：\'+sp+\'\\n适配场景：\'+sc.join(\'、\')+\'\\n\\n第7-9页：核心亮点\\n\'+hl.slice(0,3).map(function(h,i){return \'亮点\'+(i+1)+\'：\'+h+\'（每页一个，配示意图）\'}).join(\'\\n\')+\'\\n\\n第10-12页：应用场景\\n\'+sc.slice(0,3).map(function(s,i){return \'场景\'+(i+1)+\'：\'+s+\'（每页一个，配现场图）\'}).join(\'\\n\')+\'\\n\\n第13-15页：标杆案例\\n\'+cs.slice(0,3).map(function(c,i){return \'案例\'+(i+1)+\'：\'+c.name+\'\\n效果：\'+c.desc}).join(\'\\n\\n\')+\'\\n\\n第16页：合作方案\\n合作模式：需求诊断 → 方案设计 → 部署交付 → 持续维保\\n集成周期：约14天\\n联系方式：cn.orionstar.com\\n\\n【每页内容包含】标题 + 要点bullet + 配图建议\';},
  \'ppt-scene\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\';return \'【PPT大纲】\\n页数建议：15-20页\\n\\n第1页：封面\\n标题：\'+s0+\'等场景智能化解决方案\\n副标题：\'+name+\'（\'+zh+\'）· 猎户星空\\n\\n第2页：目录\\n1. 行业背景\\n2. 产品介绍\\n3. 核心亮点\\n4. 应用场景\\n5. 标杆案例\\n6. 合作方案\\n\\n第3页：行业背景\\n\'+sc.join(\'、\')+\'等场景的智能化转型趋势与核心痛点分析\\n\\n第4-6页：产品介绍\\n\'+name+\'（\'+zh+\'）：\'+desc+\'\\n核心参数：\'+sp+\'\\n\\n第7-9页：核心亮点\\n\'+hl.slice(0,3).map(function(h,i){return \'亮点\'+(i+1)+\'：\'+h}).join(\'\\n\')+\'\\n（每页一个亮点，配实拍或示意图）\\n\\n第10-12页：应用场景详解\\n\'+sc.slice(0,3).map(function(s,i){return \'场景\'+(i+1)+\'：\'+s+\'\\n• 核心需求：高效稳定服务\\n• 解决方案：\'+h0+\'\\n• 配图建议：\'+s+\'实拍图\'}).join(\'\\n\\n\')+\'\\n\\n第13-15页：标杆案例\\n\'+cs.slice(0,3).map(function(c,i){return \'案例\'+(i+1)+\'：\'+c.name+\'\\n效果：\'+c.desc}).join(\'\\n\\n\')+\'\\n\\n第16页：合作方案\\n合作模式：POC试点 → 规模化部署 → 全周期维保\\n联系方式：cn.orionstar.com\\n\\n【每页内容包含】标题 + 要点bullet + 配图建议\';},
  \'ppt-case\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\';return \'【PPT大纲】\\n页数建议：15-20页\\n\\n第1页：封面\\n标题：猎户星空\'+name+\'标杆案例合集\\n副标题：北京猎户星空科技有限公司\\n\\n第2页：目录\\n1. 行业背景\\n2. 产品介绍\\n3. 核心亮点\\n4. 应用场景\\n5. 标杆案例\\n6. 合作方案\\n\\n第3页：行业背景\\n\'+sc.join(\'、\')+\'等场景的智能化趋势与\'+name+\'落地价值\\n\\n第4-6页：产品介绍\\n\'+name+\'（\'+zh+\'）：\'+desc+\'\\n核心参数：\'+sp+\'\\n核心能力：\'+hl.slice(0,3).join(\'、\')+\'\\n\\n第7-9页：核心亮点\\n\'+hl.slice(0,3).map(function(h,i){return \'亮点\'+(i+1)+\'：\'+h}).join(\'\\n\')+\'\\n（每页一个亮点，配示意图）\\n\\n第10-12页：应用场景\\n\'+sc.slice(0,3).map(function(s,i){return \'场景\'+(i+1)+\'：\'+s}).join(\'\\n\')+\'\\n（每页一个场景，配现场实拍图）\\n\\n第13-15页：标杆案例（每页一个）\\n\'+cs.slice(0,Math.min(cs.length,3)).map(function(c,i){return \'案例\'+(i+1)+\'：\'+c.name+\'\\n效果：\'+c.desc+\'\\n• 配图建议：\'+c.name+\'现场合作图\\n• 客户LOGO建议：右上角\'}).join(\'\\n\\n\')+\'\\n\\n第16页：合作方案\\n合作模式：需求诊断 → POC验证 → 商业化部署 → 运营维保\\n集成周期：约14天（含调试培训）\\n联系方式：cn.orionstar.com / 400热线（以官网为准）\\n\\n【每页内容包含】标题 + 要点bullet + 配图建议\';},
  \'seo-popular\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\';return name+\'（\'+zh+\'）是什么？\'+s0+\'场景常见问题完全解答\\n\\n什么是\'+name+\'？\'+name+\'（\'+zh+\'）是猎户星空研发的商用服务机器人，专为\'+s0+\'等场景设计，具备\'+hl.slice(0,3).join(\'、\')+\'等核心能力。\\n\\nQ1：\'+name+\'能做什么？\\nA：\'+name+\'主要功能：\'+hl.map(function(hh,i){return (i+1)+\'. \'+hh}).join(\'；\')+\'。在\'+s0+\'场景可有效提升服务效率。\\n\\nQ2：\'+name+\'适合哪些场景？\\nA：适配\'+sc.length+\'类场景：\'+sc.map(function(ss){return \'• \'+ss}).join(\'\\n\')+\'\\n\\nQ3：核心技术规格？\\nA：\'+sp+\'（完整参数以官方白皮书为准）。\\n\\nQ4：有哪些真实客户案例？\\nA：\'+cs.slice(0,3).map(function(c){return \'• \'+c.name+\'：\'+c.desc}).join(\'\\n\')+\'\\n\\nQ5：部署周期和售后如何？\\nA：标准集成周期约14天，猎户星空在全国主要城市提供本地化维保服务。\\n\\n【FAQ精选】\\n❓ \'+name+\'和普通机器人有什么区别？\\n✅ \'+name+\'搭载AgentOS智能操作系统，具备大模型语音交互、激光SLAM导航、多机协调调度等能力。\\n\\n❓ \'+name+\'在\'+s0+\'场景适用吗？\\n✅ \'+name+\'已在\'+c0.name+\'等\'+cs.length+\'家客户的\'+s0+\'场景完成商业化部署，\'+c0.desc+\'。\\n\\n❓ 如何申请体验？\\n✅ 访问 cn.orionstar.com 联系商务团队，申请POC评估或现场演示。\';},
  \'seo-pitfall\':function(){var s0=sc[0]||\'商业场所\';return name+\'（\'+zh+\'）选型必看：\'+s0+\'场景采购避坑指南\\n\\n购买\'+name+\'前必看！\'+s0+\'场景服务机器人选型常见误区与正确方法。\\n\\n【误区一：只看设备价格，忽略总拥有成本】\\n很多客户只比较设备单价，忽视了集成部署、年度维保、场地改造等全链路成本。建议采购前完整评估ROI周期（参考值6-12个月，以实际项目测算为准）。\\n\\n【误区二：忽视场地适配评估】\\n\'+name+\'对场地有基本要求：走廊宽度≥1.5米、地面材质适合行驶、灯光满足视觉识别。在\'+s0+\'场景部署前，建议完成现场勘察。\\n\\n【误区三：低估系统集成复杂度】\\n\'+name+\'支持与POS、门禁、楼控等系统对接，但集成工作量因各企业IT环境不同。猎户星空标准集成周期约14天，建议提前评估IT兼容性。\\n\\n【误区四：忽视售后运营支持】\\n猎户星空在全国主要城市提供本地化服务，支持OTA升级、定期维保和7×24小时故障响应。购买前请确认售后覆盖范围。\\n\\n【正确选型方法】\\n1. 明确场景需求：\'+sc.slice(0,3).join(\'、\')+\'等不同场景需求各异，先定场景再选产品\\n2. 参考真实案例：\'+c0.name+\'（\'+c0.desc+\'）可作为同类场景参考\\n3. 申请POC验证：先小规模试点，验证效果后再规模化部署\\n4. 全链路成本核算：设备+集成+维保+运营，综合计算ROI\\n\\n如需\'+s0+\'场景专属选型报告，联系猎户星空：cn.orionstar.com。\';},
  \'seo-comparison\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\';return name+\'哪个好？\'+s0+\'场景服务机器人全方位选型对比（2025版）\\n\\n怎么选服务机器人？\'+name+\'（\'+zh+\'）与同类产品对比，助您做出最优选择。\\n\\n【核心维度对比】\\n\\n对比维度 | \'+name+\' | 普通服务机器人 | 传统人工\\n---|---|---|---\\n核心能力 | \'+h0+\' | 基础路线导航 | 人工操作\\n场景数量 | \'+sc.length+\'类主流场景 | 1-2类场景 | 灵活但成本高\\n技术规格 | \'+sp+\' | 参数较低 | 无\\n24小时服务 | 支持，自动回充 | 部分支持 | 需排班\\n系统集成 | 开放API，支持多系统 | 封闭系统 | 手动\\nROI周期 | 6-12个月（参考） | 12-24个月 | 持续投入\\n\\n【\'+name+\'在\'+s0+\'场景的核心优势】\\n\'+hl.map(function(hh,i){return (i+1)+\'. \'+hh}).join(\'\\n\')+\'\\n\\n【已验证案例参考】\\n\'+cs.slice(0,3).map(function(c){return \'▸ \'+c.name+\'：\'+c.desc}).join(\'\\n\')+\'\\n\\n【选型建议】\\n• 日均服务量50次以上：推荐引入\'+name+\'，ROI相对明确\\n• 多场景覆盖：\'+name+\'支持\'+sc.length+\'类场景，减少多系统管理负担\\n• API集成需求：\'+name+\'提供开放接口，兼容主流业务系统\\n\\n如需定制化选型分析报告，联系猎户星空：cn.orionstar.com。\';},
  \'seo-price\':function(){var s0=sc[0]||\'商业场所\';return name+\'多少钱？\'+s0+\'场景完整预算参考\\n\\n\'+name+\'（\'+zh+\'）价格如何？本文整理\'+s0+\'场景的完整预算构成（以下为参考框架，以官方报价为准）。\\n\\n【预算构成参考】\\n\\n费用项目 | 说明 | 参考比例\\n---|---|---\\n设备采购 | \'+name+\'单机或多机 | 主要成本\\n集成部署 | 系统对接+场地调试 | 约10-20%\\n培训费用 | 员工操作培训 | 较低\\n年度维保 | 远程+现场服务 | 约5-10%/年\\n\\n【影响价格的关键因素】\\n1. 部署规模：多机部署通常单台成本更优\\n2. 集成复杂度：与\'+sc.length+\'类场景相关系统对接工作量\\n3. 场地改造：\'+s0+\'场地如需特殊改造需额外评估\\n4. 维保级别：标准维保与增值服务级别不同\\n\\n【ROI参考案例】\\n\'+cs.slice(0,2).map(function(c){return \'▸ \'+c.name+\'：\'+c.desc}).join(\'\\n\')+\'\\n\\n【人力替代估算】\\n\'+s0+\'场景中，每台\'+name+\'通常可承担1-2名服务人员的部分工作量（以实际业务流程为准）。参考回收周期：6-12个月。\\n\\n如需定制化报价或ROI测算模型，联系猎户星空商务：cn.orionstar.com。\';},
  \'seo-scenario\':function(){var s0=sc[0]||\'商业场所\',s1=sc[1]||sc[0]||\'服务场景\';return \'如何解决\'+s0+\'场景的效率与成本问题？\'+name+\'实战解决方案\\n\\n\'+s0+\'场景面临效率与成本挑战？\'+name+\'（\'+zh+\'）已在\'+cs.length+\'家客户的\'+s0+\'场景中完成商业化验证。\\n\\n【\'+s0+\'场景核心痛点】\\n• 高峰期人手不足，服务响应慢\\n• 服务标准不统一，客户体验差异大\\n• 夜间/假日服务覆盖缺口\\n• 人力成本持续上涨\\n\\n【\'+name+\'解决方案能力】\\n\'+hl.map(function(hh,i){return (i+1)+\'. \'+hh}).join(\'\\n\')+\'\\n技术规格：\'+sp+\'\\n\\n【落地实施步骤】\\n第一步（1-3天）：需求诊断\\n确认\'+s0+\'场景需求，完成现场勘察（走廊宽度、地面材质、灯光条件）。\\n\\n第二步（4-14天）：集成部署\\n系统集成（POS/门禁/楼控等），设备调试，路径规划配置。\\n\\n第三步（14天后）：正式运营\\n员工协作培训，人机协同上线，持续数据监控与效果追踪。\\n\\n【真实案例验证】\\n\'+cs.slice(0,3).map(function(c){return \'▸ \'+c.name+\'（\'+s0+\'）：\'+c.desc}).join(\'\\n\')+\'\\n\\n如需\'+s0+\'场景完整解决方案文档，联系猎户星空：cn.orionstar.com。\';},
  \'seo-review\':function(){var s0=sc[0]||\'商业场所\',h0=hl[0]||\'智能技术\';return name+\'实测报告：\'+c0.name+\'在\'+s0+\'场景亲历评价（真实数据）\\n\\n亲测\'+name+\'（\'+zh+\'）！\'+cs.length+\'家真实客户案例汇总，\'+s0+\'场景真实数据（以客户实际环境测量为准）。\\n\\n【测评基本信息】\\n产品：\'+name+\'（\'+zh+\'）\\n测评场景：\'+s0+\'\\n参与客户：\'+cs.slice(0,2).map(function(c){return c.name}).join(\'、\')+\'等\\n\\n【核心功能实测】\\n\'+hl.slice(0,3).map(function(hh,i){return \'功能\'+(i+1)+\'：\'+hh+\'\\n实测结果：在\'+s0+\'场景正常运行，效果因环境条件不同有差异\'}).join(\'\\n\\n\')+\'\\n\\n【客户真实反馈】\\n\'+cs.slice(0,3).map(function(c,i){return (i+1)+\'. \'+c.name+\'\\n用后评价：\'+c.desc}).join(\'\\n\\n\')+\'\\n\\n【实测总结】\\n✅ 优点：\'+hl.slice(0,3).join(\'、\')+\'\\n📍 适用场景：\'+sc.join(\'、\')+\'\\n💡 建议：日均服务量50次以上的\'+s0+\'场景ROI相对明确；建议先申请POC试点验证\\n\\n如需完整实测数据或申请现场演示，联系猎户星空：cn.orionstar.com。\';}
  };
  var _result=tpl[type]?tpl[type]():\'（暂无此类型模板）\';
  if(_result.replace(/\\n/g,\'\').length<900){
    _result+=\'\\n\\n【产品背景与技术基础】\\n\'+name+\'（\'+zh+\'）由猎户星空自主研发，融合激光SLAM导航、AI视觉感知与大模型语音交互技术，能够在\'+sc.slice(0,3).join(\'、\')+\'等多类真实商业环境中持续稳定运行。产品核心技术规格：\'+sp+\'，已通过相关行业认证（以实际认证文件为准），具备国内及主要海外市场的部署条件。\\n\\n【市场背景与行业价值】\\n猎户星空在服务机器人领域持续深耕，已形成从底层硬件研发、AgentOS智能软件平台到行业场景解决方案的完整能力体系。\'+name+\'作为其中的核心产品系列，在\'+sc[0]+\'等高价值场景中积累了大量真实部署数据，覆盖任务调度、路径规划、人机交互等关键环节，为持续产品迭代提供坚实的数据基础。根据已服务客户的实际反馈，\'+name+\'在标准化、高频次服务场景中综合表现稳定，是当前商用服务机器人市场中具备规模化落地能力的代表性产品之一。\\n\\n【部署咨询与合作方式】\\n如需了解\'+name+\'的完整产品规格、现场演示安排、集成方案评估或参考客户现场参观，欢迎联系猎户星空商务团队：cn.orionstar.com，或拨打官方400热线（以官网为准）。猎户星空提供从需求诊断、方案设计到交付落地的全程专业支持服务。\';
  }
  return _result;
}

initApp();
</script>
</body>
</html>'''

    existing_path = '/Users/wangmeng/Projects/orionstar-kb.html'
    full = login_html + login_page + app_html

    with open(existing_path, 'w') as f:
        f.write(full)

    size = len(full)
    app_present = 'id="app"' in full
    init_present = 'initApp()' in full
    print(f'Rebuilt: {size/1024:.0f}KB')
    print(f'App present: {app_present}')
    print(f'initApp present: {init_present}')

if __name__ == '__main__':
    build()
