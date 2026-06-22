#!/usr/bin/env node

import { Buffer } from 'buffer';

const colors = {
  reset: '\x1b[0m',
  bold: '\x1b[1m',
  cyan: '\x1b[36m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  red: '\x1b[31m',
  gray: '\x1b[90m',
  underlined: '\x1b[4m'
};

const printHelp = () => {
  console.log(`
${colors.bold}${colors.cyan}Google News CLI Tool${colors.reset}
Usage:
  node index.js [options]

Options:
  -h, --help       Show this help message
  -s, --search     Search query to find stories on specific topics
  -l, --limit      Number of headlines to return (default: 10)
  --lang           Language code (e.g., en, es, default: en)
  --country        Country/region code (e.g., US, GB, default: US)

Examples:
  node index.js
  node index.js --limit 5
  node index.js --search "technology"
  node index.js --search "space" --limit 3
  node index.js --lang es-419 --country AR
`);
};

function decodeEntities(str) {
  if (!str) return '';
  return str
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&apos;/g, "'")
    .replace(/&#39;/g, "'")
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/<!\[CDATA\[([\s\S]*?)\]\]>/g, '$1')
    .trim();
}

function getRelativeTime(pubDateStr) {
  try {
    const pubDate = new Date(pubDateStr);
    const now = new Date();
    const diffMs = now - pubDate;
    if (isNaN(diffMs)) return pubDateStr;
    
    const diffMins = Math.floor(diffMs / 60000);
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return pubDate.toLocaleDateString();
  } catch (e) {
    return pubDateStr;
  }
}

async function main() {
  const args = process.argv.slice(2);
  let search = '';
  let limit = 10;
  let lang = 'en';
  let country = 'US';
  let showHelp = false;

  for (let i = 0; i < args.length; i++) {
    const arg = args[i];
    if (arg === '--help' || arg === '-h') {
      showHelp = true;
    } else if (arg === '--search' || arg === '-s') {
      search = args[++i];
    } else if (arg === '--limit' || arg === '-l') {
      const val = parseInt(args[++i], 10);
      if (!isNaN(val)) limit = val;
    } else if (arg === '--lang') {
      lang = args[++i] || 'en';
    } else if (arg === '--country') {
      country = args[++i] || 'US';
    }
  }

  if (showHelp) {
    printHelp();
    process.exit(0);
  }

  // Construct Google News RSS url
  // Example ceid value: US:en, AR:es-419
  const ceid = `${country}:${lang}`;
  let url = '';
  let headerText = '';

  if (search) {
    url = `https://news.google.com/rss/search?q=${encodeURIComponent(search)}&hl=${lang}&gl=${country}&ceid=${ceid}`;
    headerText = `Search Results for "${search}"`;
  } else {
    url = `https://news.google.com/rss?hl=${lang}&gl=${country}&ceid=${ceid}`;
    headerText = `Top Stories`;
  }

  console.log(`${colors.gray}Fetching news from Google...${colors.reset}\n`);

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const xml = await response.text();

    const itemRegex = /<item>([\s\S]*?)<\/item>/g;
    let match;
    const items = [];

    while ((match = itemRegex.exec(xml)) !== null) {
      const itemXml = match[1];
      const titleRaw = (itemXml.match(/<title>([\s\S]*?)<\/title>/) || [])[1] || '';
      const link = (itemXml.match(/<link>([\s\S]*?)<\/link>/) || [])[1] || '';
      const pubDate = (itemXml.match(/<pubDate>([\s\S]*?)<\/pubDate>/) || [])[1] || '';
      const sourceRaw = (itemXml.match(/<source[^>]*>([\s\S]*?)<\/source>/) || [])[1] || '';
      
      const title = decodeEntities(titleRaw);
      const source = decodeEntities(sourceRaw);
      
      // Clean source name suffix from title if present
      let cleanTitle = title;
      if (source && title.endsWith(` - ${source}`)) {
        cleanTitle = title.substring(0, title.length - (source.length + 3));
      }

      items.push({
        title: cleanTitle,
        link: decodeEntities(link),
        pubDate: decodeEntities(pubDate),
        source: source
      });
    }

    if (items.length === 0) {
      console.log(`${colors.yellow}No news articles found.${colors.reset}`);
      return;
    }

    const displayCount = Math.min(items.length, limit);
    console.log(`${colors.bold}${colors.cyan}=== ${headerText} (Showing ${displayCount} of ${items.length}) ===${colors.reset}\n`);

    for (let i = 0; i < displayCount; i++) {
      const item = items[i];
      const indexStr = `${i + 1}.`.padEnd(4);
      const relativeTime = getRelativeTime(item.pubDate);
      const sourceStr = item.source ? `[${item.source}]` : '';

      console.log(`${colors.bold}${colors.green}${indexStr}${item.title}${colors.reset}`);
      if (sourceStr || relativeTime) {
        console.log(`    ${colors.gray}${sourceStr} • ${relativeTime}${colors.reset}`);
      }
      console.log(`    ${colors.underlined}${colors.cyan}${item.link}${colors.reset}\n`);
    }

  } catch (error) {
    console.error(`${colors.red}Error fetching or parsing news:${colors.reset}`, error.message);
    process.exit(1);
  }
}

main();
