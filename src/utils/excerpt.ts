export function generateExcerpt(content: string, maxChars = 200) {
  if (!content) return '';
  // Remove HTML tags
  let text = content.replace(/<[^>]*>/g, ' ');
  // Remove Markdown image/link syntax and code fences
  text = text.replace(/!\[[^\]]*\]\([^\)]+\)/g, ' ');
  text = text.replace(/\[[^\]]*\]\([^\)]+\)/g, ' ');
  text = text.replace(/```[\s\S]*?```/g, ' ');
  // Remove remaining markdown chars
  text = text.replace(/[#_*`>~\-]{1,3}/g, ' ');
  // Collapse whitespace
  text = text.replace(/\s+/g, ' ').trim();
  if (text.length <= maxChars) return text;
  const truncated = text.slice(0, maxChars);
  const lastSpace = truncated.lastIndexOf(' ');
  return (lastSpace > 0 ? truncated.slice(0, lastSpace) : truncated) + '…';
}
