// ============================================================
// Ad Trend Briefing - Google Apps Script (v6 - Research Enhanced)
// ============================================================
// 매주 자동으로 광고/미디어 업계 트렌드를 수집, 분석하고
// 한국어 보고서를 이메일로 발송합니다.
//
// 핵심: 논문(연구 결과) 비중 확대 및 별도 섹션 구성
//
// 설정:
// 1. https://script.google.com 접속
// 2. 새 프로젝트 생성 후 이 코드 붙여넣기
// 3. sendWeeklyReport() 수동 실행하여 권한 승인
// 4. setupWeeklyTrigger() 실행하여 주간 자동 실행 등록
// ============================================================

var CONFIG = {
  recipientEmail: "hyungu@innocean.com",
  emailSubjectPrefix: "[광고/미디어 심층 리포트]",

  rssFeeds: {
    "AdAge": "https://adage.com/arc/outboundfeeds/rss/",
    "Adweek": "https://www.adweek.com/feed/",
    "The Drum": "https://www.thedrum.com/feeds/all.xml",
    "Marketing Dive": "https://www.marketingdive.com/feeds/news/",
    "Digiday": "https://digiday.com/feed/",
    "MediaPost": "https://www.mediapost.com/rss/publications/"
  },

  searchKeywords: [
    "advertising media effectiveness",
    "digital advertising technology",
    "programmatic advertising",
    "social media advertising",
    "video advertising measurement",
    "consumer behavior social media",
    "AI in marketing research",
    "brand equity advertising"
  ],

  categories: {
    "AI_auto": { name: "AI/\uc790\ub3d9\ud654", keywords: ["ai", "artificial intelligence", "machine learning", "automation", "generative", "chatgpt", "llm", "openai"] },
    "programmatic": { name: "\ud504\ub85c\uadf8\ub798\ub9e4\ud2f1/\uc560\ub4dc\ud14c\ud06c", keywords: ["programmatic", "ad tech", "adtech", "rtb", "real-time bidding", "dsp", "ssp"] },
    "social": { name: "\uc18c\uc15c\ubbf8\ub514\uc5b4", keywords: ["social media", "instagram", "tiktok", "facebook", "meta", "youtube", "influencer", "creator"] },
    "video": { name: "\ub3d9\uc601\uc0c1/CTV", keywords: ["video", "ctv", "connected tv", "streaming", "ott"] },
    "data": { name: "\ub370\uc774\ud130/\ud504\ub77c\uc774\ubc84\uc2dc", keywords: ["data", "privacy", "cookie", "cookieless", "first-party", "gdpr", "consent"] },
    "brand": { name: "\ube0c\ub79c\ub4dc/\ud06c\ub9ac\uc5d0\uc774\ud2f0\ube0c", keywords: ["brand", "creative", "campaign", "storytelling", "content marketing"] },
    "measurement": { name: "\uce21\uc815/\ud6a8\uacfc", keywords: ["measurement", "roi", "attribution", "effectiveness", "kpi", "analytics"] },
    "retail": { name: "\ub9ac\ud14c\uc77c\ubbf8\ub514\uc5b4", keywords: ["retail media", "commerce media", "amazon ads", "walmart"] }
  },

  coreKeywords: [
    "advertis", "ad campaign", "media buy", "programmatic", "brand market",
    "digital market", "social media market", "ctv", "connected tv",
    "ad tech", "adtech", "retail media", "video ad", "influencer market",
    "creator econom", "ad spend", "ad revenue", "audience target",
    "click-through", "ctr", "openai ad", "chatgpt ad", "research", "study"
  ],

  maxArticlesPerSource: 4,
  maxTotalArticles: 15,
  maxPapers: 10 // 논문 수 확대
};

var TOPIC_DESCRIPTIONS = {
  "AI_auto": "AI \ubc0f \uc790\ub3d9\ud654 \uae30\uc220\uc774 \uad11\uace0\uc5c5\uacc4\uc5d0 \ubbf8\uce58\ub294 \ubcc0\ud654",
  "programmatic": "\ud504\ub85c\uadf8\ub798\ub9e4\ud2f1 \uad11\uace0\uc640 \uc560\ub4dc\ud14c\ud06c \uae30\uc220 \ub3d9\ud5a5",
  "social": "\uc18c\uc15c\ubbf8\ub514\uc5b4 \ud50c\ub7ab\ud3fc \uad11\uace0 \uc804\ub7b5 \ubcc0\ud654",
  "video": "\ub3d9\uc601\uc0c1 \ubc0f CTV \uad11\uace0 \ud2b8\ub80c\ub4dc",
  "data": "\ub370\uc774\ud130 \ud65c\uc6a9\uacfc \ud504\ub77c\uc774\ubc84\uc2dc \uaddc\uc81c \ub300\uc751",
  "brand": "\ube0c\ub79c\ub4dc \uc804\ub7b5 \ubc0f \ud06c\ub9ac\uc5d0\uc774\ud2f0\ube0c \uce94\ud398\uc778",
  "measurement": "\uad11\uace0 \ud6a8\uacfc \uce21\uc815 \ubc0f ROI \ubd84\uc11d",
  "retail": "\ub9ac\ud14c\uc77c\ubbf8\ub514\uc5b4 \ub124\ud2b8\uc6cc\ud06c \ud655\uc7a5"
};


// ============================================================
// Main: Send Weekly Report
// ============================================================
function sendWeeklyReport() {
  Logger.log("Ad Trend Analysis starting...");

  var articles = collectRssFeeds();
  Logger.log("Articles collected: " + articles.length);

  var papers = searchSemanticScholar();
  Logger.log("Papers collected: " + papers.length);

  var topArticles = selectTopArticles(articles);
  var topPapers = selectTopPapers(papers);
  Logger.log("Selected: " + topArticles.length + " articles, " + topPapers.length + " papers");

  var report = generateReport(topArticles, topPapers, articles.length, papers.length);
  sendEmail(report);

  Logger.log("Weekly report sent successfully!");
}


// ============================================================
// Korean Translation (built-in LanguageApp)
// ============================================================
function translateToKorean(text) {
  if (!text || text.trim().length === 0) return text;
  
  // 잡음 제거 (영어 상태)
  text = text.replace(/subscribe/gi, "").replace(/newsletter/gi, "");
  text = text.replace(/Digiday Media Buying Summit/gi, "");
  text = text.replace(/secure your spot/gi, "");
  
  try {
    if (text.length > 4500) text = text.substring(0, 4500);
    var result = LanguageApp.translate(text, "en", "ko");
    Utilities.sleep(300);
    
    // 한국어 잡음 제거
    if (result) {
      result = result.replace(/\uac31\uc2e0\ud558\uc138\uc694/g, "") // 갱신하세요
                     .replace(/\uad6c\ub3c5/g, "") // 구독
                     .replace(/\ub274\uc2a4\ub808\ud130/g, "") // 뉴스레터
                     .replace(/Ad Age \ud06c\ub85c\uc2a4\uc6cc\ub4dc/g, "") // Ad Age 크로스워드
                     .replace(/\uc790\ub9ac\ub97c \ud655\ubcf4\ud558\uc138\uc694/g, ""); // 자리를 확보하세요
    }
    
    return result || text;
  } catch (e) {
    Logger.log("Translation error: " + e.message);
    return text;
  }
}


// ============================================================
// RSS Feed Collection
// ============================================================
function collectRssFeeds() {
  var articles = [];
  var cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - 7);

  var feeds = CONFIG.rssFeeds;
  var sourceNames = Object.keys(feeds);

  for (var s = 0; s < sourceNames.length; s++) {
    var sourceName = sourceNames[s];
    var feedUrl = feeds[sourceName];
    try {
      var response = UrlFetchApp.fetch(feedUrl, { muteHttpExceptions: true });
      if (response.getResponseCode() !== 200) {
        Logger.log("[RSS] " + sourceName + " failed: HTTP " + response.getResponseCode());
        continue;
      }

      var xml = response.getContentText();
      var doc = XmlService.parse(xml);
      var root = doc.getRootElement();
      var items = parseRssItems(root, sourceName);

      var count = 0;
      for (var i = 0; i < items.length; i++) {
        var item = items[i];
        if (item.date && item.date < cutoff) continue;
        if (!item.title || item.title.trim().length < 10) continue;

        articles.push({
          source: sourceName,
          type: "industry",
          title: item.title.trim(),
          url: item.url || "",
          summary: cleanHtml(item.summary || "").substring(0, 800), // 더 길게 가져옴
          date: item.date,
          author: item.author || ""
        });
        count++;
      }
      Logger.log("[RSS] " + sourceName + ": " + count);

    } catch (e) {
      Logger.log("[RSS] " + sourceName + " error: " + e.message);
    }

    Utilities.sleep(500);
  }

  return articles;
}


function parseRssItems(root, sourceName) {
  var items = [];
  try {
    var channel = root.getChild("channel");
    if (channel) {
      var rssItems = channel.getChildren("item");
      for (var i = 0; i < rssItems.length; i++) {
        var item = rssItems[i];
        items.push({
          title: getChildText(item, "title"),
          url: getChildText(item, "link"),
          summary: getChildText(item, "description"),
          date: parseDate(getChildText(item, "pubDate")),
          author: getChildText(item, "author")
        });
      }
      return items;
    }

    var atomNs = XmlService.getNamespace("http://www.w3.org/2005/Atom");
    var entries = root.getChildren("entry", atomNs);
    if (!entries || entries.length === 0) entries = root.getChildren("entry");
    for (var j = 0; j < entries.length; j++) {
      var entry = entries[j];
      var linkEl = entry.getChild("link", atomNs) || entry.getChild("link");
      items.push({
        title: getChildText(entry, "title"),
        url: linkEl ? linkEl.getAttribute("href").getValue() : "",
        summary: getChildText(entry, "summary") || getChildText(entry, "content"),
        date: parseDate(getChildText(entry, "updated") || getChildText(entry, "published")),
        author: ""
      });
    }
  } catch (e) {
    Logger.log("XML parse error (" + sourceName + "): " + e.message);
  }

  return items;
}


function getChildText(element, childName) {
  try {
    var child = element.getChild(childName);
    if (child) return child.getText();
    if (childName.indexOf(":") > -1) {
      var parts = childName.split(":");
      var dcNs = XmlService.getNamespace("dc", "http://purl.org/dc/elements/1.1/");
      var dcChild = element.getChild(parts[1], dcNs);
      if (dcChild) return dcChild.getText();
    }
  } catch (e) {}
  return "";
}


function parseDate(dateStr) {
  if (!dateStr) return null;
  try {
    return new Date(dateStr);
  } catch (e) {
    return null;
  }
}


function cleanHtml(html) {
  if (!html) return "";
  return html.replace(/<[^>]+>/g, "").replace(/&[^;]+;/g, " ").trim();
}


// ============================================================
// Semantic Scholar Search
// ============================================================
function searchSemanticScholar() {
  var papers = [];
  var seenTitles = {};
  var cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - 45); // 기간 조금 더 늘림
  var cutoffStr = Utilities.formatDate(cutoffDate, "GMT", "yyyy-MM-dd");

  for (var k = 0; k < CONFIG.searchKeywords.length; k++) {
    var keyword = CONFIG.searchKeywords[k];
    try {
      var url = "https://api.semanticscholar.org/graph/v1/paper/search?query=" + encodeURIComponent(keyword) + "&fields=title,authors,abstract,url,year,citationCount,publicationDate&limit=8&publicationDateOrYear=" + cutoffStr + ":";

      var response = UrlFetchApp.fetch(url, { muteHttpExceptions: true });

      if (response.getResponseCode() === 429) {
        Utilities.sleep(5000);
        continue;
      }
      if (response.getResponseCode() !== 200) continue;

      var data = JSON.parse(response.getContentText());
      var results = data.data || [];

      for (var p = 0; p < results.length; p++) {
        var paper = results[p];
        var title = (paper.title || "").trim();
        if (!title || seenTitles[title.toLowerCase()]) continue;
        seenTitles[title.toLowerCase()] = true;

        var authorNames = [];
        var authors = paper.authors || [];
        for (var a = 0; a < Math.min(authors.length, 3); a++) {
          authorNames.push(authors[a].name);
        }

        papers.push({
          source: "Semantic Scholar",
          type: "academic",
          title: title,
          url: paper.url || "",
          summary: (paper.abstract || "").substring(0, 800), // 초록 충분히 가져옴
          date: paper.publicationDate ? new Date(paper.publicationDate) : null,
          author: authorNames.join(", "),
          citations: paper.citationCount || 0
        });
      }

      Utilities.sleep(1500);

    } catch (e) {
      Logger.log("[Semantic Scholar] error (" + keyword + "): " + e.message);
    }
  }

  return papers;
}


// ============================================================
// Selection and Categorization
// ============================================================
function relevanceScore(item) {
  var text = (item.title + " " + item.summary).toLowerCase();
  var score = 0;
  for (var i = 0; i < CONFIG.coreKeywords.length; i++) {
    if (text.indexOf(CONFIG.coreKeywords[i]) > -1) score += 2;
  }
  // AI 가중치
  if (text.indexOf("ai") > -1 || text.indexOf("chatgpt") > -1) score += 2;
  return score;
}


function selectTopArticles(articles) {
  articles.sort(function(a, b) { return relevanceScore(b) - relevanceScore(a); });

  var selected = [];
  var sourceCount = {};

  for (var i = 0; i < articles.length; i++) {
    var article = articles[i];
    var s = article.source;
    if ((sourceCount[s] || 0) >= CONFIG.maxArticlesPerSource) continue;
    selected.push(article);
    sourceCount[s] = (sourceCount[s] || 0) + 1;
    if (selected.length >= CONFIG.maxTotalArticles) break;
  }

  return selected;
}


function selectTopPapers(papers) {
  // 논문은 인용수 + 관련성 고려하여 상위 N개
  papers.sort(function(a, b) { 
    return (b.citations || 0) + relevanceScore(b) - ((a.citations || 0) + relevanceScore(a)); 
  });
  return papers.slice(0, CONFIG.maxPapers);
}


function categorizeItem(item) {
  var text = (item.title + " " + item.summary).toLowerCase();
  var bestKey = "etc";
  var bestScore = 0;

  var catKeys = Object.keys(CONFIG.categories);
  for (var c = 0; c < catKeys.length; c++) {
    var key = catKeys[c];
    var keywords = CONFIG.categories[key].keywords;
    var score = 0;
    for (var k = 0; k < keywords.length; k++) {
      if (text.indexOf(keywords[k]) > -1) score++;
    }
    // AI 카테고리 우대
    if (key === "AI_auto" && score > 0) score += 2;
    
    if (score > bestScore) {
      bestScore = score;
      bestKey = key;
    }
  }

  return bestKey;
}


// ============================================================
// Report Generation (Updated for Research Section)
// ============================================================
function generateReport(topArticles, topPapers, totalArticles, totalPapers) {
  var today = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy-MM-dd HH:mm");
  var totalSelected = topArticles.length + topPapers.length;

  var html = '<div style="font-family:Apple SD Gothic Neo,Segoe UI,sans-serif; max-width:800px; margin:0 auto; background:#fff; padding:30px; border-radius:12px;">';

  html += '<h1 style="color:#1a73e8; border-bottom:3px solid #1a73e8; padding-bottom:12px;">\uc8fc\uac04 \uad11\uace0/\ubbf8\ub514\uc5b4 \uc2ec\uce35 \ub9ac\ud3ec\ud2b8</h1>';

  html += '<table style="width:100%; border-collapse:collapse; margin:15px 0; font-size:14px;">';
  html += '<tr style="background:#f2f6fc;"><td style="padding:8px 12px; border:1px solid #ddd;"><b>\ubc1c\ud589\uc77c</b></td><td style="padding:8px 12px; border:1px solid #ddd;">' + today + '</td></tr>';
  html += '<tr><td style="padding:8px 12px; border:1px solid #ddd;"><b>\ubd84\uc11d \uaddc\ubaa8</b></td><td style="padding:8px 12px; border:1px solid #ddd;">\uc5c5\uacc4 \ub274\uc2a4 ' + totalArticles + '\uac74 + \ud559\uc220 \uc5f0\uad6c ' + totalPapers + '\uac74 \uc911 <b>\ud575\uc2ec ' + totalSelected + '\uac74</b> \uc120\ubcc4</td></tr>';
  html += '</table>';

  // 1. Executive Summary - AI & Research Highlight
  html += '<h2 style="color:#333; margin-top:30px; border-bottom:1px solid #e0e0e0; padding-bottom:8px;">\ud575\uc2ec \uc694\uc57d (Executive Summary)</h2>';
  
  // AI Highlight
  var aiItems = topArticles.filter(function(i) { return categorizeItem(i) === "AI_auto"; });
  if (aiItems.length > 0) {
    var topAi = aiItems[0];
    html += '<p><b>\ud83e\udd16 AI \ud2b8\ub80c\ub4dc: ' + translateToKorean(topAi.title) + '</b><br>';
    html += '<span style="font-size:13px; color:#555;">' + translateToKorean(topAi.summary).substring(0, 300) + '...</span></p>';
  }
  
  // Research Highlight
  if (topPapers.length > 0) {
    var topPaper = topPapers[0];
    html += '<p><b>\ud83d\udcda \uc8fc\ubaa9\ud560 \uc5f0\uad6c: ' + translateToKorean(topPaper.title) + '</b><br>';
    html += '<span style="font-size:13px; color:#555;">' + translateToKorean(topPaper.summary).substring(0, 300) + '...</span></p>';
  }





  // 3. Industry News Section
  html += '<h2 style="color:#1a73e8; margin-top:40px; border-bottom:1px solid #ddd; padding-bottom:8px;">\uc5c5\uacc4 \uc8fc\uc694 \ub274\uc2a4 (Industry News)</h2>';

  // Categorize
  var categorized = {};
  var usedTitles = {};
  for (var i = 0; i < topArticles.length; i++) {
    var item = topArticles[i];
    var tKey = item.title.toLowerCase();
    if (usedTitles[tKey]) continue;
    usedTitles[tKey] = true;
    var c = categorizeItem(item);
    if (!categorized[c]) categorized[c] = [];
    categorized[c].push(item);
  }

  var catKeys = Object.keys(categorized).filter(function(k) { return k !== "etc"; });
  // AI first
  catKeys.sort(function(a, b) { 
    if (a === "AI_auto") return -1;
    if (b === "AI_auto") return 1;
    return categorized[b].length - categorized[a].length; 
  });

  for (var c = 0; c < catKeys.length; c++) {
    var catKey = catKeys[c];
    var catItems = categorized[catKey];
    var catConfig = CONFIG.categories[catKey];
    var catName = catConfig ? catConfig.name : catKey;

    html += '<h3 style="color:#1a73e8; margin-top:25px;">' + catName + '</h3>';

    for (var j = 0; j < catItems.length; j++) {
      var cItem = catItems[j];
      var titleKr = translateToKorean(cItem.title);
      var summaryKr = translateToKorean(cItem.summary);

      html += '<div style="margin:12px 0; padding:12px 16px; background:#f8f9fa; border-radius:8px; border-left:4px solid #1a73e8;">';
      html += '<b>\ud83d\udcf0 ' + titleKr + '</b><br>';
      html += '<span style="font-size:12px; color:#888;">' + cItem.source + '</span>';
      html += '<p style="color:#555; font-size:13px; margin:8px 0 4px 0; line-height:1.5;">' + summaryKr + '</p>';
      if (cItem.url) {
        html += '<a href="' + cItem.url + '" style="color:#1a73e8; font-size:12px;">\uc6d0\ubb38 \ubcf4\uae30</a>';
      }
      html += '</div>';
    }
  }

  // Footer
  html += '<div style="margin-top: 50px;"></div>';

  // 4. Research Section (Academic) - Moved to End
  html += '<h2 style="color:#d93025; margin-top:40px; border-bottom:1px solid #ddd; padding-bottom:8px;">\ud559\uc220 \uc5f0\uad6c \ubc0f \uc774\ub860 (Research & Theory)</h2>';
  
  if (topPapers.length === 0) {
    html += '<p style="color:#888;">\uc774\ubc88 \uc8fc \uc218\uc9d1\ub41c \uc8fc\uc694 \ub17c\ubb38\uc774 \uc5c6\uc2b5\ub2c8\ub2e4.</p>';
  } else {
    for (var i = 0; i < topPapers.length; i++) {
      var p = topPapers[i];
      var titleKr = translateToKorean(p.title);
      var summaryKr = translateToKorean(p.summary);
      
      html += '<div style="margin:15px 0; padding:15px; background:#fff8f8; border-radius:8px; border-left:4px solid #d93025;">';
      html += '<b style="font-size:15px;">\ud83d\udcda ' + titleKr + '</b><br>';
      html += '<span style="font-size:12px; color:#666;">' + p.source + ' | \uc778\uc6a9: ' + p.citations + '</span>';
      html += '<p style="font-size:13px; color:#333; line-height:1.6; margin:8px 0;">' + summaryKr + '</p>';
      if (p.url) {
        html += '<a href="' + p.url + '" style="color:#d93025; font-size:12px; text-decoration:none;">\u2192 \ub17c\ubb38 \ubcf4\uae30</a>';
      }
      html += '</div>';
    }
  }

  // Footer
  html += '<p style="color:#888; font-size:11px; margin-top:20px; border-top:1px solid #e0e0e0; padding-top:10px;">';
  html += '\uc774 \ubcf4\uace0\uc11c\ub294 Google Apps Script\uc5d0\uc11c \uc790\ub3d9\uc73c\ub85c \uc218\uc9d1\u00b7\ubc88\uc5ed\u00b7\ubd84\uc11d\ub418\uc5b4 \uc0dd\uc131\ub418\uc5c8\uc2b5\ub2c8\ub2e4.<br>';
  html += '\uc18c\uc2a4: Semantic Scholar (Academic), AdAge, Adweek, Digiday, etc.<br>';
  html += '\uc0dd\uc131 \uc2dc\uac04: ' + today;
  html += '</p></div>';

  return html;
}


// ============================================================
// Send Email
// ============================================================
function sendEmail(htmlBody) {
  var today = Utilities.formatDate(new Date(), "Asia/Seoul", "yyyy-MM-dd");
  var subject = CONFIG.emailSubjectPrefix + " " + today;

  GmailApp.sendEmail(
    CONFIG.recipientEmail,
    subject,
    "HTML email viewer required.",
    {
      htmlBody: htmlBody,
      name: "\uad11\uace0 \ud2b8\ub80c\ub4dc \ube0c\ub9ac\ud551 \ubd07"
    }
  );

  Logger.log("Email sent: " + subject + " -> " + CONFIG.recipientEmail);
}


// ============================================================
// Weekly Trigger Setup (Monday 9 AM KST)
// ============================================================
function setupWeeklyTrigger() {
  var triggers = ScriptApp.getProjectTriggers();
  for (var i = 0; i < triggers.length; i++) {
    if (triggers[i].getHandlerFunction() === "sendWeeklyReport") {
      ScriptApp.deleteTrigger(triggers[i]);
    }
  }

  ScriptApp.newTrigger("sendWeeklyReport")
    .timeBased()
    .onWeekDay(ScriptApp.WeekDay.MONDAY)
    .atHour(9)
    .create();

  Logger.log("Weekly trigger set: Monday 9 AM");
}
